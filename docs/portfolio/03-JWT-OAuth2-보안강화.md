# JWT + Google OAuth 2.0 멀티 프로바이더 인증 시스템

> SHA-256 토큰 해싱 및 Timing Attack 방어로 보안 강화

---

## 📌 한 줄 요약

**JWT 기반 무상태 인증 + Google OAuth 2.0 통합, SHA-256 해싱과 Constant-time 비교로 보안 취약점을 해결한 인증 시스템**

---

## 🎯 프로젝트 배경

### 요구사항
- ✅ **무상태(Stateless) 인증**: 서버 확장성을 위해 세션 사용 안 함
- ✅ **소셜 로그인**: 구글 계정으로 간편 가입/로그인
- ✅ **이메일 인증**: 실제 사용자만 서비스 이용
- ✅ **보안 강화**: DB 유출 시에도 계정 안전 보장

### 기술 선택
- **JWT (JSON Web Token)**: Access/Refresh 토큰 기반 인증
- **Google OAuth 2.0**: 소셜 로그인
- **SHA-256 해싱**: 이메일 인증 토큰 보호
- **Constant-time 비교**: Timing Attack 방어

---

## 🏗️ 시스템 구조

### 1. 인증 흐름 다이어그램

```
[이메일 회원가입]
사용자 → 이메일/비밀번호 입력
    ↓
Backend → SHA-256 토큰 생성 및 해시 저장
    ↓
Gmail → 인증 링크 이메일 발송 (원본 토큰)
    ↓
사용자 → 링크 클릭
    ↓
Backend → Constant-time 비교로 토큰 검증
    ↓
DB → 이메일 인증 완료 (is_verified=True)

[JWT 로그인]
사용자 → 로그인
    ↓
Backend → Access (30분) + Refresh (7일) 토큰 발급
    ↓
Frontend → 메모리에 토큰 저장 (localStorage 사용 안 함)
    ↓
API 요청 → Authorization: Bearer {access_token}
    ↓
만료 시 → Refresh 토큰으로 자동 갱신

[Google OAuth 2.0]
사용자 → "구글로 로그인" 클릭
    ↓
Google → 인증 페이지
    ↓
사용자 → 권한 승인
    ↓
Backend → 구글 프로필 조회 → 계정 생성/로그인
    ↓
JWT 토큰 발급
```

---

## 💡 핵심 구현

### 1. JWT 토큰 기반 인증

#### Access Token + Refresh Token 전략

```python
# backend/resee/settings/base.py

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),  # 짧은 수명
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),    # 긴 수명
    'ROTATE_REFRESH_TOKENS': True,  # Refresh 시 새 Refresh 토큰 발급
    'BLACKLIST_AFTER_ROTATION': True,  # 기존 Refresh 토큰 블랙리스트
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}
```

**전략 이유**:
- ✅ **Access Token 짧은 수명**: 탈취 위험 최소화
- ✅ **Refresh Token 긴 수명**: 사용자 편의성
- ✅ **Rotate & Blacklist**: Refresh Token 재사용 방지

---

#### 로그인 API

```python
# backend/accounts/auth/views.py

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """커스텀 JWT 토큰 발급 (사용자 정보 포함)"""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # 토큰에 사용자 정보 추가
        token['email'] = user.email
        token['subscription_tier'] = user.subscription.tier
        token['is_verified'] = user.is_verified

        return token

    def validate(self, attrs):
        # 이메일 인증 체크
        user = User.objects.filter(email=attrs['email']).first()
        if user and not user.is_verified:
            raise ValidationError("이메일 인증이 필요합니다.")

        data = super().validate(attrs)

        # 응답에 사용자 정보 추가
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'subscription_tier': self.user.subscription.tier
        }

        return data


class LoginView(TokenObtainPairView):
    """로그인 API"""
    serializer_class = CustomTokenObtainPairSerializer
```

**핵심 로직**:
1. 이메일 인증 여부 확인 (`is_verified`)
2. Access + Refresh 토큰 발급
3. 토큰에 사용자 정보 포함 (구독 등급 등)

---

### 2. 이메일 인증 시스템 (SHA-256 해싱)

#### 보안 문제: 평문 토큰 저장

**기존 코드** (취약):
```python
# 잘못된 예시
def generate_email_verification_token(self):
    token = get_random_string(64)
    self.email_verification_token = token  # 평문 저장
    return token
```

**문제점**:
- ❌ DB 유출 시 토큰으로 계정 탈취 가능
- ❌ 일반 문자열 비교 (`==`)로 Timing Attack 가능

---

#### 해결: SHA-256 해싱 + Constant-time 비교

```python
# backend/accounts/models.py

import hashlib
import secrets

class User(AbstractUser):
    email_verification_token = models.CharField(max_length=64, blank=True)
    is_verified = models.BooleanField(default=False)

    def generate_email_verification_token(self):
        """
        이메일 인증 토큰 생성 (SHA-256 해싱)

        Returns:
            str: 원본 토큰 (이메일로 전송)
        """
        # 1. 32바이트 안전한 랜덤 토큰 생성
        token = secrets.token_urlsafe(32)

        # 2. SHA-256 해싱 후 DB 저장
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        self.email_verification_token = token_hash
        self.save()

        # 3. 원본 토큰만 반환 (이메일로 전송)
        return token

    def verify_email_token(self, provided_token):
        """
        이메일 토큰 검증 (Constant-time 비교)

        Args:
            provided_token: 사용자가 제공한 토큰

        Returns:
            bool: 토큰 유효 여부
        """
        # 1. 제공된 토큰을 해싱
        provided_hash = hashlib.sha256(provided_token.encode()).hexdigest()

        # 2. Constant-time 비교 (Timing Attack 방어)
        return secrets.compare_digest(
            self.email_verification_token,
            provided_hash
        )
```

**보안 개선 사항**:
- ✅ **SHA-256 해싱**: DB 유출 시에도 원본 토큰 알 수 없음
- ✅ **Constant-time 비교**: 모든 경우 동일한 시간 소요
- ✅ **secrets 모듈**: 암호학적으로 안전한 랜덤 생성

---

#### Timing Attack 방어 원리

**일반 비교 (`==`)** - 취약:
```python
# 순차 비교: 틀린 문자를 만나면 즉시 종료
"ABC123" == "XYZ789"  # 0.001ms (첫 글자에서 실패)
"ABC123" == "ABZ789"  # 0.003ms (3번째 문자에서 실패)
"ABC123" == "ABC789"  # 0.004ms (4번째 문자에서 실패)

→ 응답 시간으로 토큰을 한 글자씩 추측 가능
```

**Constant-time 비교** - 안전:
```python
# 모든 문자를 비교: 항상 동일한 시간 소요
secrets.compare_digest("ABC123", "XYZ789")  # 0.005ms
secrets.compare_digest("ABC123", "ABZ789")  # 0.005ms
secrets.compare_digest("ABC123", "ABC123")  # 0.005ms

→ 응답 시간으로 정보 유출 불가
```

---

### 3. Google OAuth 2.0 통합

```python
# backend/accounts/auth/views.py

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView

class GoogleLoginView(SocialLoginView):
    """
    Google OAuth 2.0 로그인

    Flow:
    1. 프론트엔드에서 Google OAuth 토큰 받기
    2. 백엔드로 토큰 전송
    3. Google API로 사용자 정보 조회
    4. 계정 생성/로그인
    5. JWT 토큰 발급
    """
    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.GOOGLE_OAUTH_CALLBACK_URL

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        # 신규 가입 시 구독 생성
        if response.status_code == 201:  # Created
            user = request.user
            if not hasattr(user, 'subscription'):
                Subscription.objects.create(
                    user=user,
                    tier='FREE',
                    is_active=True
                )

        return response
```

**설정**:
```python
# backend/resee/settings/base.py

INSTALLED_APPS = [
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    }
}
```

---

### 4. Frontend JWT 자동 갱신

```typescript
// frontend/src/utils/api.ts

import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

// JWT 토큰 (메모리에 저장, localStorage 사용 안 함)
let accessToken: string | null = null;
let refreshToken: string | null = null;

// Request 인터셉터: Authorization 헤더 자동 추가
api.interceptors.request.use(
  (config) => {
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response 인터셉터: 401 에러 시 자동 토큰 갱신
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // 401 에러 && Refresh 토큰 있음 && 재시도 아님
    if (
      error.response?.status === 401 &&
      refreshToken &&
      !originalRequest._retry
    ) {
      originalRequest._retry = true;

      try {
        // Refresh 토큰으로 새 Access 토큰 발급
        const response = await axios.post('/api/auth/token/refresh/', {
          refresh: refreshToken,
        });

        accessToken = response.data.access;
        refreshToken = response.data.refresh; // Rotate

        // 원래 요청 재시도
        originalRequest.headers.Authorization = `Bearer ${accessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh 실패 → 로그아웃
        accessToken = null;
        refreshToken = null;
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export const setTokens = (access: string, refresh: string) => {
  accessToken = access;
  refreshToken = refresh;
};

export const clearTokens = () => {
  accessToken = null;
  refreshToken = null;
};

export default api;
```

**핵심 전략**:
- ✅ **메모리 저장**: XSS 공격 시에도 토큰 탈취 어려움
- ✅ **자동 갱신**: 401 에러 시 Refresh 토큰으로 재발급
- ✅ **재시도**: 갱신 후 원래 요청 자동 재시도

---

## 🔐 보안 강화 사항

### 1. Rate Limiting (Redis 기반)

```python
# backend/resee/throttling.py

from rest_framework.throttling import SimpleRateThrottle
from django.core.cache import caches

class RedisLoginThrottle(SimpleRateThrottle):
    """로그인 요청 제한: 5회/분"""
    scope = 'login'
    rate = '5/min'
    cache = caches['throttle']  # Redis

    def get_cache_key(self, request, view):
        # IP 주소 기반 제한
        ident = self.get_ident(request)
        return f'throttle_login_{ident}'
```

**적용**:
```python
# backend/accounts/auth/views.py

class LoginView(TokenObtainPairView):
    throttle_classes = [RedisLoginThrottle]
```

---

### 2. CSRF 보호

```python
# backend/resee/settings/base.py

CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True  # HTTPS only
CSRF_COOKIE_SAMESITE = 'Lax'
```

---

### 3. HTTPS 강제

```python
# backend/resee/settings/production.py

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1년
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

---

## 📊 성과

### 보안 개선
- ✅ **평문 토큰 제거**: SHA-256 해싱으로 DB 유출 시에도 안전
- ✅ **Timing Attack 방어**: Constant-time 비교
- ✅ **Rate Limiting**: 무차별 대입 공격 방지 (5회/분)

### 사용자 편의성
- ✅ **자동 토큰 갱신**: 30분마다 재로그인 불필요
- ✅ **소셜 로그인**: 구글 계정으로 간편 가입/로그인
- ✅ **이메일 인증**: 실제 사용자만 서비스 이용

---

## 🧪 테스트

### SHA-256 해싱 테스트

```python
# backend/accounts/tests/test_security.py

def test_email_token_hashed():
    """이메일 토큰이 해시로 저장되는지 테스트"""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )

    # 토큰 생성
    token = user.generate_email_verification_token()

    # DB에 저장된 값이 원본 토큰과 다른지 확인
    user.refresh_from_db()
    assert user.email_verification_token != token
    assert len(user.email_verification_token) == 64  # SHA-256 hex


def test_constant_time_comparison():
    """Constant-time 비교 테스트"""
    user = User.objects.create_user(email='test@example.com')
    token = user.generate_email_verification_token()

    # 정상 토큰
    assert user.verify_email_token(token) is True

    # 잘못된 토큰
    assert user.verify_email_token('wrong_token') is False
```

---

## 🔗 관련 코드

### Backend
- [`backend/accounts/auth/views.py`](../../backend/accounts/auth/views.py) - 인증 API
- [`backend/accounts/models.py`](../../backend/accounts/models.py) - User 모델
- [`backend/resee/throttling.py`](../../backend/resee/throttling.py) - Rate Limiting

### Frontend
- [`frontend/src/utils/api.ts`](../../frontend/src/utils/api.ts) - JWT 인터셉터
- [`frontend/src/contexts/AuthContext.tsx`](../../frontend/src/contexts/AuthContext.tsx) - 인증 상태 관리

---

## 💡 배운 점

### 1. JWT vs 세션
- ✅ **JWT 장점**: 무상태, 서버 확장 용이, 마이크로서비스 적합
- ⚠️ **JWT 단점**: 토큰 크기, 즉시 무효화 어려움 → Blacklist로 해결

### 2. 토큰 저장 위치
- ❌ **localStorage**: XSS 공격 시 토큰 탈취
- ✅ **메모리**: 탭 닫으면 사라지지만, XSS 방어 강화
- ⚠️ **HttpOnly Cookie**: CSRF 공격 가능 → CSRF 토큰 필요

### 3. 보안 트레이드오프
- **편의성 vs 보안**: Access Token 수명 (30분 선택)
- **성능 vs 보안**: Rate Limiting (Redis 캐시 사용)

---

## 🎯 면접 대비 핵심 포인트

### Q1. "JWT를 왜 사용했나요?"
**A**: "서버 확장성을 위해 무상태 인증이 필요했습니다. 세션 방식은 서버에 상태를 저장하므로 수평 확장 시 세션 공유 문제가 발생하지만, JWT는 토큰 자체에 정보를 담아 서버가 상태를 저장하지 않아 확장이 용이합니다."

### Q2. "이메일 토큰을 왜 해싱하나요?"
**A**: "DB 유출 시나리오를 고려했습니다. 평문 토큰이 유출되면 공격자가 즉시 계정을 탈취할 수 있지만, SHA-256 해시로 저장하면 원본 토큰을 알 수 없어 안전합니다. 또한 Constant-time 비교로 Timing Attack도 방어했습니다."

### Q3. "Timing Attack이 뭔가요?"
**A**: "일반 문자열 비교(`==`)는 틀린 문자를 만나면 즉시 종료하므로, 응답 시간으로 토큰을 한 글자씩 추측할 수 있는 공격입니다. `secrets.compare_digest()`를 사용하면 모든 경우 동일한 시간이 걸려 방어할 수 있습니다."

---

## 📚 참고 자료

- [JWT Documentation](https://jwt.io/)
- [OWASP Timing Attack](https://owasp.org/www-community/attacks/Timing_attack)
- [Django Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)

---

**GitHub**: https://github.com/djgnfj-svg/Resee-project
**작성일**: 2025-10-21
