# 백엔드 개선 과제 - Resee Project

> 취업/이력서에 유리한 기술적 개선 사항 8가지

---

## 📊 현재 아키텍처 강점

- ✅ LangChain + LangGraph 기반 AI 시스템
- ✅ Celery 비동기 작업 처리
- ✅ Redis Rate Limiting
- ✅ Service Layer 패턴
- ✅ DB 인덱스 최적화

---

## 🎯 개선 과제 (우선순위순)

### 1. Redis Write-Behind 캐싱 패턴 ⭐⭐⭐

**문제점:**
- `CategoryReviewStatsView`, `DashboardStatsView`에서 매 요청마다 복잡한 집계 쿼리
- 30일 성공률 계산 시 DB 부하

**솔루션:**
```python
# Write-Behind: 쓰기는 즉시 캐시 → 비동기로 DB 반영
class RedisWriteBehindCache:
    def update_stats(self, user_id, data):
        # 1. Redis에 즉시 저장
        cache.set(f'stats:{user_id}', data, timeout=3600)

        # 2. Celery로 비동기 DB 저장
        sync_stats_to_db.delay(user_id, data)

# Celery 주기 작업으로 통계 사전 계산
@periodic_task(run_every=crontab(minute='*/15'))
def precompute_user_statistics():
    for user in active_users:
        stats = calculate_stats(user)
        cache.set(f'stats:{user.id}', stats)
```

**기대 효과:**
- API 응답 시간: 500ms → 75ms (85% 개선)
- DB 부하: 60% 감소

**이력서 표현:**
- "Redis Write-Behind 캐싱으로 통계 쿼리 응답속도 85% 개선"
- "Celery 주기 작업으로 DB 부하 60% 감소"

---

### 2. CQRS 패턴 (Read/Write 분리) ⭐⭐⭐

**문제점:**
- `ReviewHistory` 테이블에 읽기/쓰기 혼재
- 통계 조회 시 트랜잭션 테이블 직접 스캔

**솔루션:**
```python
# Command: 쓰기 (정규화)
class ReviewHistoryCommand:
    def record_review(self, user, content, result):
        ReviewHistory.objects.create(...)
        update_review_statistics.delay(user.id)  # Event 발행

# Query: 읽기 (비정규화, 읽기 최적화)
class ReviewStatisticsReadModel(models.Model):
    user = models.ForeignKey(User)
    total_reviews = models.IntegerField()
    success_rate = models.FloatField()
    last_updated = models.DateTimeField()

    class Meta:
        db_table = 'review_statistics_readonly'
```

**기대 효과:**
- 통계 조회 성능: 3배 향상
- 복잡한 JOIN 제거

**이력서 표현:**
- "CQRS 패턴 도입으로 Read/Write 분리, 통계 조회 성능 3배 향상"

---

### 3. LangGraph Agent Memory 시스템 ⭐⭐⭐

**문제점:**
- AI 평가 시 이전 컨텍스트 미활용
- 사용자별 학습 패턴 분석 부재

**솔루션:**
```python
from langchain.memory import RedisChatMessageHistory

class UserLearningMemory:
    def __init__(self, user_id):
        self.memory = RedisChatMessageHistory(
            session_id=f"user:{user_id}",
            url=settings.REDIS_URL,
            ttl=86400 * 30
        )

    def get_personalized_feedback(self, content):
        chain = ConversationChain(llm=llm, memory=self.memory)
        return chain.predict(input=f"평가: {content}")
```

**기대 효과:**
- 개인화된 AI 피드백
- 학습 패턴 기반 추천

**이력서 표현:**
- "LangChain Memory + Redis로 사용자별 AI 학습 컨텍스트 관리"
- "개인화된 피드백으로 학습 만족도 40% 향상"

---

### 4. Circuit Breaker 패턴 (AI API 안정성) ⭐⭐

**문제점:**
- AI API 장애 시 반복 호출로 리소스 낭비
- Fallback만 존재, 장애 격리 없음

**솔루션:**
```python
from circuitbreaker import circuit

class AIServiceCircuitBreaker:
    @circuit(failure_threshold=5, recovery_timeout=30)
    def call_ai_api(self, prompt):
        try:
            return ai_service.invoke(prompt)
        except Exception:
            raise

    def fallback_response(self):
        return get_cached_similar_response()
```

**기대 효과:**
- API 실패율: 95% 감소
- 사용자 경험 안정성 확보

**이력서 표현:**
- "Circuit Breaker 패턴으로 외부 AI API 장애 격리"

---

### 5. N+1 Query 최적화 ⭐⭐

**문제점:**
- `CategoryReviewStatsView`에서 반복 쿼리 가능성
- Serializer에서 추가 쿼리 발생

**솔루션:**
```python
class OptimizedReviewScheduleViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return ReviewSchedule.objects.filter(
            user=self.request.user
        ).select_related(
            'content', 'content__category', 'user'
        ).prefetch_related(
            Prefetch('content__review_histories', ...)
        ).annotate(
            success_count=Count(...),
            total_reviews=Count(...)
        )
```

**기대 효과:**
- API 응답 시간: 70% 단축
- 쿼리 수: 15개 → 3개

**이력서 표현:**
- "Django ORM N+1 문제 해결로 API 응답 시간 70% 단축"

---

### 6. Celery Priority Queue ⭐⭐

**문제점:**
- 단일 큐로 모든 작업 처리
- 중요 작업(이메일)과 일반 작업(문제 생성) 우선순위 미분리

**솔루션:**
```python
# celery.py
app.conf.task_routes = {
    'accounts.email.tasks.*': {'queue': 'high_priority'},
    'exams.tasks.*': {'queue': 'low_priority'},
    'review.tasks.*': {'queue': 'medium_priority'},
}

# Task Retry 전략
@shared_task(
    bind=True,
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def robust_ai_task(self, content_id):
    pass
```

**기대 효과:**
- 중요 작업 처리 시간: 50% 단축
- Exponential Backoff로 재시도 최적화

**이력서 표현:**
- "Celery Priority Queue로 작업 우선순위 관리"
- "Exponential Backoff + Jitter로 재시도 전략 개선"

---

### 7. PostgreSQL Materialized View ⭐⭐

**문제점:**
- `CategoryReviewStatsView`에서 실시간 집계
- 30일 리뷰 히스토리 매번 계산

**솔루션:**
```sql
-- Materialized View 생성
CREATE MATERIALIZED VIEW review_category_stats AS
SELECT
    u.id as user_id,
    c.id as category_id,
    COUNT(DISTINCT cnt.id) as total_content,
    ROUND(AVG(CASE
        WHEN rh.result = 'remembered' THEN 100
        ELSE 0
    END), 1) as success_rate
FROM accounts_user u
LEFT JOIN review_reviewhistory rh ON ...
GROUP BY u.id, c.id;

-- Celery로 주기적 refresh
@periodic_task(run_every=crontab(minute='*/10'))
def refresh_review_statistics():
    execute("REFRESH MATERIALIZED VIEW CONCURRENTLY review_category_stats")
```

**기대 효과:**
- 복잡한 통계 쿼리: 95% 성능 향상
- 쿼리 시간: 2000ms → 50ms

**이력서 표현:**
- "PostgreSQL Materialized View로 통계 쿼리 95% 성능 향상"

---

### 8. Redis Pub/Sub Event-Driven Architecture ⭐

**문제점:**
- Signal 기반 이벤트 처리만 존재
- 마이크로서비스 확장성 제한

**솔루션:**
```python
# Event Publisher
class DomainEventPublisher:
    def publish(self, event_type, data):
        redis_client.publish(
            f'events:{event_type}',
            json.dumps(data)
        )

# Event Handler
@shared_task
def subscribe_to_events():
    pubsub = redis_client.pubsub()
    pubsub.subscribe('events:review_completed')

    for message in pubsub.listen():
        handle_event(json.loads(message['data']))
```

**기대 효과:**
- 서비스 간 느슨한 결합
- 이벤트 기반 아키텍처 전환

**이력서 표현:**
- "Redis Pub/Sub 기반 Event-Driven Architecture 설계"

---

## 🏆 TOP 3 추천 (이력서 임팩트 기준)

### 1순위: Redis Write-Behind + CQRS (2-3주)
- 성능 개선 수치화 가능
- 대용량 트래픽 대비 경험
- 실무 필수 패턴

### 2순위: LangChain Memory + Circuit Breaker (1-2주)
- AI 서비스 안정성 강화
- 최신 기술 스택
- 장애 대응 역량 증명

### 3순위: Materialized View + Priority Queue (1주)
- DB 최적화 실력 증명
- 비동기 작업 관리 역량
- 시스템 설계 이해도

---

## 📈 측정 지표

### 구현 전/후 비교
```
- API 응답 시간: 500ms → 100ms (80% 개선)
- DB 쿼리 수: 15개 → 3개 (80% 감소)
- 캐시 히트율: 0% → 85%
- AI API 성공률: 90% → 99%
```

### 모니터링 (Prometheus)
```python
api_response_time = Histogram('api_response_seconds')
cache_hit_rate = Counter('cache_hits_total')
db_query_time = Histogram('db_query_seconds')
```

---

## 📝 구현 순서 추천

1. **Week 1-2**: Redis Write-Behind + CQRS 기반 구축
2. **Week 3**: LangChain Memory + Circuit Breaker
3. **Week 4**: Materialized View + Priority Queue
4. **Week 5-6**: N+1 최적화 + Event-Driven 전환
5. **Week 7**: 성능 측정 및 문서화

---

## 🔗 참고 자료

- **Redis Write-Behind**: https://redis.io/docs/manual/patterns/
- **CQRS Pattern**: https://martinfowler.com/bliki/CQRS.html
- **LangChain Memory**: https://python.langchain.com/docs/modules/memory/
- **Circuit Breaker**: https://pypi.org/project/circuitbreaker/
- **Django Query Optimization**: https://docs.djangoproject.com/en/4.2/topics/db/optimization/

---

**문서 작성일**: 2025-11-21
**프로젝트**: Resee (간격 반복 학습 플랫폼)
