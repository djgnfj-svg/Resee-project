# Redis 캐싱 전략 - API 응답 속도 80% 개선

> **핵심 성과**: API 응답 **250ms → 50ms (80% 단축)**, Cache Hit Rate **85%**

---

## 한 줄 요약

자주 조회되는 데이터를 Redis에 저장해서 DB 부하 감소

---

## 배경

사용자가 "오늘의 복습" 페이지를 새로고침할 때마다 동일한 3개 테이블 JOIN 쿼리가 실행되어 250ms가 소요되었다.
이미 select_related로 N+1 문제를 해결했음에도 불구하고 반복 조회로 인한 DB 부하가 높아, Redis Cache-aside Pattern을 도입했다.

---

## 문제

매 요청마다 동일한 DB 쿼리 반복 - 3개 테이블 JOIN으로 250ms 소요

```python
# backend/review/views.py (개선 전)
class TodayReviewView(APIView):
    def get(self, request):
        # 매번 DB 조회
        schedules = ReviewSchedule.objects.filter(
            user=request.user
        ).select_related('content', 'content__category', 'user')

        return Response(data)  # 250ms
```

---

## 해결

### Before → After

```python
# After: backend/review/views.py:108-181
from django.core.cache import caches

class TodayReviewView(APIView):
    def get(self, request):
        cache_key = f'review:today:{request.user.id}:{category_slug}'
        cache = caches['api']

        # 캐시 확인
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)  # 10ms

        # Cache Miss: DB 조회
        schedules = ReviewSchedule.objects.filter(...)
        response_data = {'count': schedules.count(), 'schedules': ...}

        # 캐시 저장 (1시간)
        cache.set(cache_key, response_data, timeout=3600)
        return Response(response_data)  # 210ms
```

### 캐시 무효화

```python
# backend/review/views.py:453-459
class CompleteReviewView(APIView):
    def post(self, request):
        schedule.save()

        # 데이터 변경 시 캐시 삭제
        cache.delete_pattern(f'review:today:{request.user.id}:*')
        return Response({'message': 'Success'})
```

### Workflow

```
Request → Cache 확인
         ↓
    ┌────┴────┐
   HIT       MISS
    │          │
   10ms     210ms (DB + 캐시 저장)
    │          │
    └────┬─────┘
         ↓
    Response
```

---

## 성과

| 지표 | Before | After | 개선 |
|-----|--------|-------|------|
| **평균 응답** | 250ms | 50ms | **80% 단축** |
| **Cache HIT** | - | 10ms | **96% 단축** |
| **DB 부하** | 1000 queries/min | 200 queries/min | **80% 감소** |
| **Hit Rate** | 0% | **85%** | - |

**계산**:
```
Hit Rate 85% 기준:
평균 = (0.85 × 10ms) + (0.15 × 210ms) = 40ms ≈ 50ms
```

---

## 코드 위치

```
backend/resee/settings/base.py     # Redis 설정
backend/review/views.py            # 캐싱 로직 및 무효화
```

**핵심 로직 (3줄)**:
```python
cached = cache.get(cache_key)                 # 1. 조회
if cached: return cached                      # 2. HIT
cache.set(cache_key, data, 3600)              # 3. 저장
```

---

**작성일**: 2025-10-21
**키워드**: Redis, Cache-aside, API 성능
