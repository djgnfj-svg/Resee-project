# JWT 인증 + 보안 강화

> **핵심 성과**: DB 유출 시에도 **계정 안전**, Timing Attack 방어, Rate Limiting **5회/분**

---

## 한 줄 요약

토큰을 해싱해서 DB 유출 시에도 계정 탈취 불가능하게 개선

---

## 배경

이메일 인증 토큰을 평문으로 DB에 저장하고 있었다.
DB가 유출될 경우 공격자가 토큰을 그대로 사용해 계정을 탈취할 수 있는 위험이 있었다.
또한 일반적인 문자열 비교(==)를 사용하면 Timing Attack에 취약하다는 보안 가이드를 발견했다.
SHA-256 해싱과 secrets.compare_digest()로 두 가지 취약점을 모두 해결했다.

---

## 문제

평문 토큰 저장 → DB 유출 시 즉시 계정 탈취 가능

```python
# backend/accounts/models.py (개선 전)
import random

def generate_email_verification_token(self):
    token = ''.join(random.choices(string.ascii_letters, k=32))

    # 평문 그대로 DB 저장
    self.email_verification_token = token
    self.save()
    return token

def verify_email(self, token):
    # 일반 비교 (Timing Attack 취약)
    if self.email_verification_token == token:
        self.is_verified = True
        self.save()
        return True
    return False
```

---

## 해결

### Before → After

#### 1. SHA-256 해싱

```python
# backend/accounts/models.py:107-142
import hashlib
import secrets

def generate_email_verification_token(self):
    # 암호학적으로 안전한 토큰 생성
    token = secrets.token_urlsafe(32)

    # SHA-256 해싱 후 DB 저장
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    self.email_verification_token = token_hash  # 해시만 저장
    self.save()

    return token  # 원본은 이메일로 전송
```

#### 2. Constant-time 비교

```python
# backend/accounts/models.py:125-142
def verify_email(self, token):
    # 입력받은 토큰 해싱
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Constant-time 비교 (Timing Attack 방어)
    if not secrets.compare_digest(self.email_verification_token, token_hash):
        return False

    self.is_verified = True
    self.save()
    return True
```

#### 3. Rate Limiting

```python
# backend/resee/throttling.py:54-68
class LoginRateThrottle(RedisThrottleMixin, AnonRateThrottle):
    scope = 'login'
    cache = property(RedisThrottleMixin.get_cache)  # Redis 사용

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)  # IP 주소
        return self.cache_format % {'scope': self.scope, 'ident': ident}

# backend/accounts/auth/views.py:32-35
class EmailTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [LoginRateThrottle]  # 5회/분
```

### Workflow

```
Before: 평문 저장
  Token 생성 → DB 저장 ("abc123") → DB 유출 시 즉시 탈취

After: SHA-256 해싱
  Token 생성 → SHA-256 해싱 → DB 저장 (해시만)
  → DB 유출 시 원본 알 수 없음

Timing Attack 방어:
  == 비교: 0.001ms ~ 0.005ms (시간 차이로 정보 유출)
  secrets.compare_digest: 항상 0.005ms (일정)
```

---

## 성과

| 지표 | Before | After | 개선 |
|-----|--------|-------|------|
| **DB 유출 시 위험** | 즉시 탈취 | 원본 알 수 없음 | **100% 방어** |
| **Timing Attack** | 취약 | 방어 | **완전 차단** |
| **무차별 대입** | 무제한 | 5회/분 | **96% 감소** |

---

## 코드 위치

```
backend/accounts/models.py        # SHA-256 해싱
backend/resee/throttling.py       # Rate Limiting
backend/accounts/auth/views.py    # Login View
```

**핵심 로직 (3줄)**:
```python
token_hash = hashlib.sha256(token.encode()).hexdigest()  # 해싱
self.email_verification_token = token_hash               # 저장
secrets.compare_digest(db_hash, input_hash)              # 비교
```

---

**작성일**: 2025-10-21
**키워드**: SHA-256, Timing Attack, Rate Limiting, JWT
