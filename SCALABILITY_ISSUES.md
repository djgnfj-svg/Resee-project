# 확장성 문제 분석 (Scalability Issues)

사용자가 많아질 때 발생할 수 있는 병목 지점과 해결 방안을 분석합니다.

---

## 🚨 핵심 문제 요약

| 카테고리 | 현재 상태 | 임계점 | 위험도 |
|---------|----------|-------|--------|
| **동시 접속** | Gunicorn 2 workers × 2 threads = **4개 요청** | 100명 동시 접속 | 🔴 매우 높음 |
| **AI API 비용** | 무제한 호출 (검증+평가+생성) | 월 1000명 활성 사용자 | 🔴 매우 높음 |
| **DB 연결** | PostgreSQL pooler (6543 transaction mode) | 동시 500 쿼리 | 🟡 중간 |
| **Rate Limiting** | 1000 req/hour | 시간당 평균 17 req/user | 🟢 낮음 |
| **캐싱** | locmem (단일 프로세스) | 멀티 인스턴스 배포 시 | 🟠 높음 |
| **Celery Worker** | 단일 worker (추정) | 시간당 100개 비동기 작업 | 🟠 높음 |

---

## 1. 🔴 동시 접속 처리 한계 (Critical)

### 문제 상황

**Gunicorn 설정**:
```dockerfile
# Dockerfile:44
CMD ["gunicorn", "resee.wsgi:application",
     "--bind", "0.0.0.0:8080",
     "--workers", "2",        # ⚠️ 2개 프로세스
     "--threads", "2",        # ⚠️ 각 2개 스레드
     "--timeout", "120"]
```

**처리 능력**:
- **최대 동시 요청: 4개** (2 workers × 2 threads)
- 각 요청 평균 응답 시간 100ms 가정 시:
  - **초당 처리량: 40 req/s**
  - **동시 접속 가능 사용자: ~100명**

### 증상
- 사용자 100명 이상 동시 접속 시 요청 대기 발생
- 502/504 Gateway Timeout 에러 증가
- 평균 응답 시간 급격히 증가 (100ms → 5초+)
- AI 기능 사용 시 timeout (120초 제한)

### 임계점
- **평일 점심시간 (12-1pm)**: 동시 접속 50-100명 예상
- **시험 기간**: 동시 접속 200-500명 예상
- **서비스 다운 위험**: 100명 초과 시

### 해결 방안

#### 즉시 조치 (1-2일)
1. **Worker 수 증가**
```bash
# Railway 환경 변수 추가
GUNICORN_WORKERS=4  # CPU 코어 수 × 2
GUNICORN_THREADS=4   # I/O 대기 많은 경우 증가

# Dockerfile 수정
CMD ["gunicorn", "resee.wsgi:application",
     "--workers", "4",
     "--threads", "4",  # 최대 16 동시 요청
     "--timeout", "120"]
```

**예상 효과**: 4 → 16 동시 요청 (400% 향상)

2. **Railway 인스턴스 Scale-out**
```bash
# Railway Dashboard에서 설정
Instances: 1 → 2-3개 (Horizontal Scaling)
Load Balancer: Railway 자동 제공
```

**예상 효과**: 16 → 48 동시 요청 (1200% 향상)

#### 중기 대책 (1주)
3. **비동기 처리 전환**
```python
# ASGI (Uvicorn) 도입 검토
# 동일 리소스로 10배 이상 처리량 향상 가능

# Dockerfile
CMD ["uvicorn", "resee.asgi:application",
     "--host", "0.0.0.0",
     "--port", "8080",
     "--workers", "4"]
```

4. **정적 콘텐츠 CDN 분리**
- 현재: Whitenoise로 Django에서 직접 서빙
- 개선: S3 + CloudFront로 분리
- **효과**: Django 부하 30% 감소

#### 장기 대책 (1개월)
5. **로드 밸런서 + 멀티 리전**
- Railway 멀티 리전 배포 (US West + Asia)
- 지역별 트래픽 분산
- **효과**: 지연시간 50% 감소, 가용성 99.9%

---

## 2. 🔴 AI API 비용 폭증 (Critical)

### 문제 상황

**AI 사용 현황**:
```python
# backend/ai_services/ 구조
ai_services/
├── validators/content_validator.py  # claude-3-7-sonnet (고가)
├── evaluators/answer_evaluator.py   # claude-3-haiku
├── evaluators/title_evaluator.py    # claude-3-haiku
├── generators/mc_generator.py       # LangGraph (복잡)
└── generators/question_generator.py # LangGraph
```

**비용 추정** (Anthropic 가격 기준):
- **claude-3.7-sonnet**: $3.00/MTok input, $15.00/MTok output
- **claude-3-haiku**: $0.25/MTok input, $1.25/MTok output

**사용 시나리오**:
1. 콘텐츠 검증 (평균 1K tokens): $0.015/회
2. 답변 평가 (평균 500 tokens): $0.001/회
3. 객관식 생성 (평균 2K tokens): $0.003/회
4. 시험 문제 생성 (평균 3K tokens): $0.005/회

**비용 계산**:
- 활성 사용자 1,000명/월
- 각자 평균 20개 콘텐츠 생성 + 50회 복습
- **월 예상 비용**: $600-1,500

### 증상
- 사용자 1,000명 도달 시 월 AI 비용 $1,500+
- PRO 구독료($9.99/월)로 커버 불가
- Rate limit 초과로 서비스 중단 위험

### 임계점
- **손익분기점**: 월 활성 사용자 300명 (PRO 가입률 30% 가정)
- **위험 구간**: 월 활성 사용자 1,000명+

### 해결 방안

#### 즉시 조치 (1-2일)
1. **AI 기능 Rate Limiting 강화**
```python
# backend/resee/settings/production.py (현재 설정)
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'user': '1000/hour',  # ⚠️ 너무 관대함
}

# 개선안
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    # 구독 티어별 AI 사용 제한
    'ai_free': '10/day',      # 무료: 하루 10회
    'ai_basic': '50/day',     # BASIC: 하루 50회
    'ai_pro': '200/day',      # PRO: 하루 200회
}
```

```python
# backend/ai_services/base.py에 추가
from django_ratelimit.decorators import ratelimit

class BaseAIService:
    @ratelimit(key='user', rate='10/d', method='POST')
    def call_anthropic(self, prompt: str):
        # AI 호출 전 rate limit 체크
        pass
```

2. **응답 캐싱 (Redis)**
```python
# 동일 콘텐츠 검증 결과 캐싱
from django.core.cache import caches

def validate_content(content_id, text):
    cache_key = f'ai_validation:{content_id}:{hash(text)}'
    cached = caches['api'].get(cache_key)

    if cached:
        return cached  # 캐시 히트 (비용 $0)

    result = ai_service.validate(text)  # AI 호출 (비용 발생)
    caches['api'].set(cache_key, result, timeout=86400)  # 24시간
    return result
```

**예상 효과**:
- 캐시 히트율 30-50% 가정
- 월 비용 $1,500 → $750-1,050 (30-50% 절감)

#### 중기 대책 (1주)
3. **Prompt 최적화**
```python
# ❌ 비효율적 (1,500 tokens)
prompt = f"""
다음 학습 콘텐츠를 검증하세요.
제목: {title}
내용: {content}
카테고리: {category}
작성자: {author}
생성일: {created_at}
[길고 상세한 지시사항...]
"""

# ✅ 최적화 (800 tokens)
prompt = f"""
검증 대상:
제목: {title}
내용: {content}

기준: 명확성, 정확성
형식: {{"score": 0-100, "issues": []}}
"""
```

**예상 효과**: Token 사용량 40-50% 감소

4. **AI 모델 다운그레이드**
```python
# 간단한 작업은 Haiku 사용
validators/content_validator.py: claude-3-7-sonnet → claude-3-haiku
# 비용: $0.015/회 → $0.001/회 (93% 절감)
```

#### 장기 대책 (1개월)
5. **오픈소스 LLM 도입 (Self-hosting)**
- 간단한 평가: Llama 3.1 8B (AWS EC2 g4dn.xlarge)
- 복잡한 생성: Claude Haiku (API)
- **월 비용**: $150 (EC2) + $300 (Claude) = $450
- **절감액**: $1,050 (70% 절감)

6. **사용자 크레딧 시스템**
```python
# 구독 티어별 월 AI 크레딧
FREE: 100 크레딧 (콘텐츠 검증 10회)
BASIC: 500 크레딧 (50회)
PRO: 2,000 크레딧 (200회)

# 초과 시 추가 구매 유도
```

---

## 3. 🟠 데이터베이스 연결 부족

### 문제 상황

**PostgreSQL 연결 설정**:
```python
# backend/resee/settings/production.py:320
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=300,  # 연결 재사용 5분
        conn_health_checks=True,
    )
}
```

**Supabase 제약**:
- Transaction Mode Pooler: **동시 연결 제한**
- Free tier: 최대 60 연결
- Pro tier: 최대 200 연결 (추정)

**문제 계산**:
- Gunicorn 2 workers × 2 threads = 4 연결
- Celery 1 worker = 1-4 연결
- **총 8개 연결** (현재)
- **100명 동시 접속 시**: 100개 연결 필요

### 증상
- `OperationalError: FATAL: remaining connection slots reserved`
- 502 Bad Gateway (DB 연결 실패)
- 쿼리 대기 시간 증가

### 임계점
- Free tier: 60 연결 (동시 접속 60명)
- Pro tier: 200 연결 (동시 접속 200명)

### 해결 방안

#### 즉시 조치
1. **Connection Pooling 최적화**
```python
# settings/production.py
DATABASES['default']['OPTIONS'] = {
    'connect_timeout': 10,
    'options': '-c statement_timeout=30000',  # 30초
}

# PgBouncer 활용 (Supabase 내장)
DATABASE_URL = 'postgresql://...pooler.supabase.com:6543/...'  # Transaction mode
# Session mode로 전환 검토 (포트 5432)
```

2. **연결 수 모니터링**
```python
# backend/resee/views.py (health check에 추가)
from django.db import connection

def check_db_connections():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT count(*)
            FROM pg_stat_activity
            WHERE datname = current_database()
        """)
        active_connections = cursor.fetchone()[0]
    return active_connections
```

#### 중기 대책
3. **Read Replica 활용**
```python
# 읽기 전용 쿼리는 Replica로 분산
DATABASES = {
    'default': {...},
    'replica': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'read-replica.supabase.com',
    }
}

# Automatic routing
DATABASE_ROUTERS = ['resee.db_router.ReplicaRouter']
```

---

## 4. 🟠 캐싱 전략 부족

### 문제 상황

**현재 캐싱**:
```python
# backend/resee/settings/production.py:134
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',  # ⚠️
        'OPTIONS': {
            'MAX_ENTRIES': 5000,
        },
    },
    'throttle': {
        'BACKEND': 'django_redis.cache.RedisCache',  # ✅
    }
}
```

**문제점**:
- **locmem**: 프로세스별 독립 캐시 (멀티 인스턴스 시 무용지물)
- **공유 불가**: Worker 1이 캐싱한 데이터를 Worker 2가 재사용 불가
- **캐시 히트율 저하**: 실제 효과 25% 미만

### 증상
- 동일 API 요청이 매번 DB 쿼리 실행
- 멀티 인스턴스 배포 시 캐시 효과 사라짐
- Redis는 있지만 throttling만 사용

### 해결 방안

#### 즉시 조치
1. **Default Cache를 Redis로 전환**
```python
# settings/production.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',  # ✅ 변경
        'LOCATION': os.environ.get('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
            },
        },
        'TIMEOUT': 300,  # 5분
    }
}
```

2. **API 응답 캐싱**
```python
# backend/content/views.py
from django.views.decorators.cache import cache_page
from rest_framework.decorators import action

class ContentViewSet(viewsets.ModelViewSet):
    @cache_page(300)  # 5분 캐싱
    def list(self, request):
        # 콘텐츠 목록 조회
        pass

    @action(detail=True)
    @cache_page(60)  # 1분 캐싱
    def retrieve(self, request, pk=None):
        # 콘텐츠 상세 조회
        pass
```

**예상 효과**:
- DB 쿼리 50-70% 감소
- 응답 시간 40-60% 단축
- 캐시 히트율 60-80%

#### 중기 대책
3. **QuerySet 캐싱**
```python
from django.core.cache import cache

def get_user_contents(user_id):
    cache_key = f'user_contents:{user_id}'
    cached = cache.get(cache_key)

    if cached:
        return cached

    contents = Content.objects.filter(author_id=user_id)\
        .select_related('category')\
        .prefetch_related('review_schedules')

    cache.set(cache_key, list(contents), timeout=300)
    return contents
```

---

## 5. 🟡 Session 저장소 비효율

### 문제 상황

```python
# backend/resee/settings/production.py:182
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # ⚠️ DB 저장
SESSION_COOKIE_AGE = 86400  # 1일
```

**문제점**:
- 모든 요청마다 DB에서 세션 조회
- 사용자 1,000명 × 평균 20 req/session = **20,000 쿼리/일**
- PostgreSQL 연결 및 부하 증가

### 해결 방안

```python
# Redis 세션으로 전환
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'  # Redis cache
```

**예상 효과**:
- DB 쿼리 20,000/일 감소
- 세션 조회 속도 10배 향상 (PostgreSQL 50ms → Redis 5ms)

---

## 6. 🟢 현재 양호한 부분

### ✅ N+1 쿼리 최적화 완료
- select_related, prefetch_related 적용
- 쿼리 수 95% 감소 (41 → 2)

### ✅ Rate Limiting 구현
- Redis 기반 throttling
- 익명/인증 사용자 구분

### ✅ Celery 비동기 처리
- 이메일, AI 작업 비동기 처리
- 사용자 응답 속도 유지

---

## 📊 우선순위별 액션 플랜

### 🚨 P0 - 즉시 (1-2일)
1. ✅ Gunicorn workers 증가 (2→4)
2. ✅ AI Rate Limiting 강화 (구독 티어별)
3. ✅ Default Cache Redis 전환
4. ✅ Session Redis 전환

**예상 효과**: 동시 접속 100 → 400명, AI 비용 30% 절감

### 🔴 P1 - 긴급 (1주)
5. ✅ Railway 멀티 인스턴스 (2-3개)
6. ✅ AI 응답 캐싱
7. ✅ API 응답 캐싱
8. ✅ DB 연결 모니터링

**예상 효과**: 동시 접속 1,200명, AI 비용 50% 절감

### 🟠 P2 - 중요 (1개월)
9. ⏳ ASGI (Uvicorn) 전환
10. ⏳ CDN 도입 (S3 + CloudFront)
11. ⏳ Read Replica 활용
12. ⏳ 오픈소스 LLM 도입

**예상 효과**: 동시 접속 5,000명+, AI 비용 70% 절감

---

## 💰 비용 분석

### 현재 인프라 비용 (월)
- Railway: $10
- Supabase PostgreSQL: $0 (Free tier)
- Upstash Redis: $0 (Free tier)
- Vercel: $0 (Hobby)
- Anthropic API: ~$0 (사용자 적음)
- **총합**: ~$10/월

### 사용자 증가 시 예상 비용 (월)

| 월 활성 사용자 | Railway | Supabase | Redis | Anthropic | 총합 |
|---------------|---------|----------|-------|-----------|------|
| **100명** | $20 | $0 (Free) | $0 (Free) | $150 | **$170** |
| **500명** | $50 | $25 (Pro) | $10 | $750 | **$835** |
| **1,000명** | $100 | $25 | $20 | $1,500 | **$1,645** |
| **최적화 후 1,000명** | $100 | $25 | $20 | $450 | **$595** |

### 수익 분석 (PRO 가입률 30% 가정)

| 월 활성 사용자 | PRO 구독자 | 월 수익 | 월 비용 | 순익 |
|---------------|------------|---------|---------|------|
| **100명** | 30명 | $300 | $170 | **+$130** ✅ |
| **500명** | 150명 | $1,500 | $835 | **+$665** ✅ |
| **1,000명 (최적화 전)** | 300명 | $3,000 | $1,645 | **+$1,355** ✅ |
| **1,000명 (최적화 후)** | 300명 | $3,000 | $595 | **+$2,405** 🚀 |

**결론**:
- 최적화 없이도 손익분기점 통과
- 최적화 시 순익 80% 증가 ($1,355 → $2,405)

---

## 🎯 결론

### 가장 심각한 문제 Top 3
1. **동시 접속 처리 한계** (Gunicorn 2 workers)
2. **AI API 비용 폭증** (무제한 호출)
3. **캐싱 전략 부족** (locmem → Redis 필요)

### 빠른 해결 가능 (1-2일)
- Workers 증가: 4 → 16 동시 요청
- Rate limiting: AI 호출 제한
- Cache 전환: Redis 공유 캐시

### 투자 대비 효과 최고
- **총 작업 시간**: 1-2일
- **비용 절감**: 월 $1,050 (AI)
- **성능 향상**: 400% (동시 접속)
- **ROI**: 무한대 🚀

---

*이 분석은 2025년 11월 기준 Resee 프로젝트 실제 코드 및 인프라를 바탕으로 작성되었습니다.*
