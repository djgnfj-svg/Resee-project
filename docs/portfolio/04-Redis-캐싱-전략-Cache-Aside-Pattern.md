# 성과

Worker 2개 환경에서 정확한 Rate Limiting, 재시작 시에도 카운터 유지

---

# **한 줄 요약**

Rate Limiting을 Redis로 분리해서 메모리 효율성과 영속성 확보

---

# **배경**

Gunicorn worker 2개로 운영 중, locmem 캐시로 Rate Limiting을 처리하면 각 worker가 독립적으로 카운팅하여 제한이 2배 증가(100→200/hour)하는 문제 발생. 또한 재시작 시 제한 정보가 초기화되어 보안 취약점 존재. Rate Limiting만 Redis로 분리하여 worker 간 카운터 공유 및 영속성 확보.

---

# **문제**

1. **Gunicorn worker 2개 사용 시 제한 2배 증가**
   - 각 worker가 독립적인 locmem 사용
   - Worker 1: 100/hour, Worker 2: 100/hour → 실제 200/hour
   - Rate Limiting이 무의미해짐

2. **재시작 후 제한 초기화**
   - 서버 재시작 시 카운터 리셋 → 악의적 요청 방어 실패

---

# **해결**

### **Before**

```python
# backend/resee/settings/base.py (개선 전)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        # 모든 캐싱을 여기서 처리
        # Rate Limiting 포함 → 재시작 시 카운터 초기화
    }
}

# 문제점:
# 1. 서버 재시작 시 Rate Limiting 카운터 초기화 (보안 취약)
# 2. 여러 서버 환경에서 각각 독립적으로 카운팅 (분산 환경 불가)
```

### **After**

### **1. 캐시 분리 전략 (Cache-Aside Pattern)**

```python
# backend/resee/settings/base.py:234-255
CACHES = {
    # 일반 캐싱용 (빠른 응답, 휘발성 OK)
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'resee-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 5000,
            'CULL_FREQUENCY': 4,
        }
    },
    # Rate Limiting 전용 (영속성 필수)
    'throttle': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/0'),
        'OPTIONS': {
            'MAX_CONNECTIONS': 50,
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'throttle',
        'TIMEOUT': 3600,  # 1시간 TTL
    }
}
```

### **2. Redis Throttle 구현**

```python
# backend/resee/throttling.py:11-34
class RedisThrottleMixin:
    """Redis 캐시를 사용하는 Throttle Mixin"""
    cache_name = 'throttle'  # Redis 캐시 지정

    def get_cache(self):
        return caches[self.cache_name]

class RedisAnonRateThrottle(RedisThrottleMixin, AnonRateThrottle):
    """익명 사용자 Rate Limiting (Redis) - 100/hour"""
    cache = property(RedisThrottleMixin.get_cache)

class RedisUserRateThrottle(RedisThrottleMixin, UserRateThrottle):
    """인증 사용자 Rate Limiting (Redis) - 1000/hour"""
    cache = property(RedisThrottleMixin.get_cache)

class LoginRateThrottle(RedisThrottleMixin, AnonRateThrottle):
    """로그인 시도 제한 (Redis) - 5/minute"""
    scope = 'login'
    cache = property(RedisThrottleMixin.get_cache)
```

### **3. 설명**

1. **Cache-Aside Pattern 동작 원리**
   - 요청 들어옴 → Redis 캐시 조회 → 카운터 증가 → 제한 확인
   - 캐시에 없으면 새 카운터 생성 (TTL: 1시간)
   - 제한 초과 시 429 응답, 제한 내면 요청 처리

2. **하이브리드 전략 선택 이유**
   - **locmem**: Health check, 모니터링 메트릭 (Redis 장애 시에도 동작 필요)
   - **Redis**: Rate Limiting 전용
     * Gunicorn worker 2개가 같은 카운터 공유 (100/hour 정확히 제한)
     * 재시작해도 카운터 유지 (보안 강화)
   - 전부 Redis로 하면? → 가능하지만 Redis 장애 시 health check도 실패

3. **대안 검토**
   - ❌ **Memcached**: 영속성 없음, 재시작 시 데이터 손실
   - ❌ **Database**: I/O 병목, Rate Limiting에 부적합
   - ✅ **Redis**: 메모리 기반 + 영속성 확보

---

## **배운 점**

**locmem은 프로세스별 독립 메모리**라는 특성을 간과했다. Gunicorn worker 2개면 캐시도 2개 생성되어 Rate Limiting이 무의미해진다. 멀티 프로세스 환경에서는 **공유 캐시(Redis)가 필수**임을 깨달았다.

---
