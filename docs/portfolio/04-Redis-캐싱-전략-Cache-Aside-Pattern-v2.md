# 성과

Gunicorn worker를 늘려도, 재시작해도 Rate Limiting 유지

---

# **한 줄 요약**

Rate Limiting을 Redis로 분리해서 멀티 프로세스 환경 대응

---

# **배경**

Rate Limiting 구현 중 Gunicorn worker 설정을 확인하던 중 문제를 발견했다. locmem 캐시는 **프로세스별 독립 메모리**를 사용하므로, worker가 2개 이상이면 각각 별도로 카운팅하여 Rate Limiting이 무의미해진다. 이미 Celery용 Redis를 사용 중이었으므로, Rate Limiting도 Redis로 분리하는 하이브리드 전략을 선택했다.

---

# **문제**

Gunicorn worker 2개 사용 시 locmem의 프로세스별 독립 메모리로 인해 Rate Limiting 2배 증가 (100→200/hour)

---

# **해결**

### **Before**

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        # 모든 캐싱 처리
        # Worker마다 독립 메모리 → Rate Limiting 무의미
    }
}
```

### **After**

### **1. 캐시 분리 전략 (Cache-Aside Pattern)**

```python
# 일반 캐싱용 (휘발성 OK)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'resee-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 5000,
            'CULL_FREQUENCY': 4,
        }
    },
    # Rate Limiting 전용 (공유 필수)
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
class RedisThrottleMixin:
    """Redis 캐시를 사용하는 Throttle Mixin"""
    cache_name = 'throttle'

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

locmem은 프로세스별 독립 메모리라는 특성을 간과했다. 설정 파일만 보고 넘어가지 말고, **멀티 프로세스 환경에서 어떻게 동작하는지**까지 고려해야 한다는 걸 깨달았다.

---
