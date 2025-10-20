# Redis 쓰로틀링

## 핵심 개념

**Redis 기반 Rate Limiting**으로 API 남용을 방지합니다.
8개의 쓰로틀 클래스로 엔드포인트별, 사용자 등급별로 세밀한 요청 제한을 적용합니다.

## 주요 기능

- **8개 쓰로틀 클래스**:
  - RedisAnonRateThrottle: 익명 사용자 (IP 기반)
  - RedisUserRateThrottle: 인증 사용자 (User ID 기반)
  - EmailRateThrottle: 이메일 관련 작업
  - LoginRateThrottle: 로그인 시도
  - RegistrationRateThrottle: 회원가입
  - SubscriptionBasedThrottle: 구독 등급별 제한
  - APIRateThrottle: API 요청 (등급별)
  - AIEndpointThrottle: AI 엔드포인트 (등급별)
- **Redis 캐시 사용**:
  - 빠른 조회 속도
  - 분산 환경 지원
  - 자동 만료
- **구독 등급별 차등 제한**:
  - FREE: 엄격한 제한
  - BASIC: 중간 제한
  - PRO: 관대한 제한

## 동작 흐름

```
[익명 사용자 요청]
1. API 요청 수신
   ↓
2. RedisAnonRateThrottle 적용
   ↓
3. IP 주소 추출
   ↓
4. Redis에서 `throttle_anon:{IP}` 조회
   ↓
5. 제한 초과 확인
   - 초과: 429 Too Many Requests 반환
   - 미초과: 카운터 증가 후 요청 허용

[인증 사용자 요청]
1. API 요청 수신
   ↓
2. RedisUserRateThrottle 적용
   ↓
3. User ID 추출
   ↓
4. Redis에서 `throttle_user:{user_id}` 조회
   ↓
5. 제한 확인 및 처리

[구독 등급별 제한]
1. API 요청 (인증 사용자)
   ↓
2. SubscriptionBasedThrottle 적용
   ↓
3. 사용자 구독 등급 조회
   ↓
4. 등급별 scope 설정 (api_free, api_basic, api_pro)
   ↓
5. Redis에서 해당 scope 카운터 조회
   ↓
6. 제한 확인
```

## Rate Limit 설정

```python
# backend/resee/settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'resee.throttling.RedisAnonRateThrottle',
        'resee.throttling.RedisUserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',          # 익명: 시간당 100회
        'user': '1000/hour',          # 인증: 시간당 1000회
        'login': '5/minute',          # 로그인: 분당 5회
        'registration': '3/minute',   # 회원가입: 분당 3회
        'email': '10/hour',           # 이메일: 시간당 10회

        # 구독 등급별 (API)
        'api_free': '100/hour',
        'api_basic': '500/hour',
        'api_pro': '2000/hour',

        # 구독 등급별 (AI)
        'ai_free': '10/hour',
        'ai_basic': '50/hour',
        'ai_pro': '200/hour',
    }
}
```

## Redis 캐시 설정

```python
# backend/resee/settings/base.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'default-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 5000,
            'CULL_FREQUENCY': 4,
        }
    },
    'throttle': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/0'),
        'OPTIONS': {
            'MAX_CONNECTIONS': 50,
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        }
    },
}
```

## 엔드포인트별 적용

```python
from rest_framework.views import APIView
from resee.throttling import LoginRateThrottle, AIEndpointThrottle

# 로그인 엔드포인트
class LoginView(APIView):
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        # 로그인 로직 (분당 5회 제한)
        pass

# AI 문제 생성 엔드포인트
class QuestionGenerationView(APIView):
    throttle_classes = [AIEndpointThrottle]

    def post(self, request):
        # 구독 등급별 제한 적용
        # FREE: 시간당 10회
        # BASIC: 시간당 50회
        # PRO: 시간당 200회
        pass
```

## 관련 파일

- `backend/resee/throttling.py` - 8개 쓰로틀 클래스
- `backend/resee/settings/base.py` - 쓰로틀 설정

## 429 응답 예시

```json
{
  "detail": "Request was throttled. Expected available in 3600 seconds."
}
```

## 쓰로틀 클래스 상세

### 1. RedisAnonRateThrottle
- 익명 사용자 (IP 기반)
- 시간당 100회

### 2. RedisUserRateThrottle
- 인증 사용자 (User ID 기반)
- 시간당 1000회

### 3. EmailRateThrottle
- 이메일 발송/검증
- 시간당 10회
- IP 또는 User ID 기반

### 4. LoginRateThrottle
- 로그인 시도
- 분당 5회
- 브루트포스 공격 방지

### 5. RegistrationRateThrottle
- 회원가입
- 분당 3회
- 스팸 계정 생성 방지

### 6. SubscriptionBasedThrottle (Base)
- 구독 등급 확인
- 등급별 scope 동적 설정
- 상속용 베이스 클래스

### 7. APIRateThrottle
- 일반 API 요청
- FREE: 100/시간, BASIC: 500/시간, PRO: 2000/시간

### 8. AIEndpointThrottle
- AI 서비스 (비용 제어)
- FREE: 10/시간, BASIC: 50/시간, PRO: 200/시간

## 테스트 명령어

```bash
# Rate limit 상태 확인
docker-compose exec backend python manage.py rate_limit_status

# Redis 캐시 확인
docker-compose exec redis redis-cli
> KEYS throttle*
> TTL throttle_anon:127.0.0.1
```

## 확장 가능성

추가 가능한 쓰로틀:
- 결제 API 쓰로틀 (분당 1회)
- 파일 업로드 쓰로틀 (MB 기반)
- Webhook 쓰로틀
- IP 기반 블랙리스트 쓰로틀
