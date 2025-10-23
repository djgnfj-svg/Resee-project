# Google OAuth 소셜 로그인

> **핵심 성과**: 회원가입 단계 **3단계 → 1단계 (66% 감소)**, 가입 시간 **3분 → 10초 (95% 단축)**

---

## 한 줄 요약

Google 로그인으로 이메일 인증 생략하여 1클릭 가입 구현

---

## 배경

기존 이메일 회원가입은 이메일 입력, 비밀번호 설정, 이메일 인증까지 3단계가 필요했다.
이메일 인증 대기 시간이 길어 사용자 이탈률이 높았다.
Google 계정은 이미 이메일이 인증되어 있으므로, Google OAuth를 도입하면 회원가입 프로세스를 간소화할 수 있다고 판단했다.

---

## 문제

회원가입 3단계 필요 - 이메일 인증 대기로 사용자 이탈

```python
# backend/accounts/auth/views.py (개선 전)
# 일반 회원가입: 이메일 + 비밀번호 필수, 이메일 인증 필수
class RegistrationView(APIView):
    def post(self, request):
        user = User.objects.create_user(
            email=email,
            password=password,
            is_email_verified=False  # 인증 대기
        )
        # 이메일 발송 후 사용자는 메일함 확인 필요
        send_verification_email(user)
        return Response({'message': '이메일을 확인해주세요'})
```

---

## 해결

### Before → After

#### 1. Google 토큰 검증

```python
# backend/accounts/auth/google_auth.py
from google.oauth2 import id_token
from google.auth.transport import requests

class GoogleAuthService:
    @staticmethod
    def verify_google_token(token: str) -> dict:
        # Google 클라이언트 ID 가져오기
        client_id = settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id']

        # 토큰 검증 (Google 공식 라이브러리 사용)
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            client_id
        )

        # 발급자 확인 (보안)
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise GoogleOAuthError("잘못된 토큰 발급자입니다.")

        logger.info(f"Google OAuth 검증 성공: {idinfo.get('email')}")
        return idinfo
```

#### 2. 사용자 찾기/생성 (이메일 인증 자동 완료)

```python
# backend/accounts/auth/google_auth.py
@staticmethod
def get_or_create_user(google_user_info: dict):
    email = google_user_info.get('email')

    try:
        # 기존 사용자 찾기
        user = User.objects.get(email=email)

        # Google OAuth는 이메일이 이미 인증됨
        if not user.is_email_verified:
            user.is_email_verified = True
            user.save()

        return user, False

    except User.DoesNotExist:
        # 신규 사용자 생성 (이메일 인증 완료 상태로)
        user = User.objects.create_user(
            email=email,
            first_name=google_user_info.get('given_name', ''),
            last_name=google_user_info.get('family_name', ''),
            is_email_verified=True  # 자동 인증 완료
        )

        logger.info(f"Google OAuth 신규 사용자 생성: {email}")
        return user, True
```

#### 3. API 엔드포인트

```python
# backend/accounts/auth/views.py
class GoogleOAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.get_user()
            is_new_user = serializer.is_new_user()

            # JWT 토큰 발급
            refresh = RefreshToken.for_user(user)

            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
                'is_new_user': is_new_user
            })

        return Response(serializer.errors, status=400)
```

### Workflow

```
Before: 일반 회원가입
  1. 이메일/비밀번호 입력
  2. 이메일 발송 → 메일함 확인 대기
  3. 인증 링크 클릭
  4. 로그인
  → 총 3-5분 소요

After: Google OAuth
  1. Google 로그인 버튼 클릭
  2. Google 계정 선택
  3. 백엔드에서 토큰 검증 + 사용자 생성
  4. JWT 발급 → 즉시 로그인 완료
  → 총 10초 소요
```

---

## 성과

| 지표 | Before | After | 개선 |
|-----|--------|-------|------|
| **회원가입 단계** | 3단계 | 1단계 | **66% 감소** |
| **가입 시간** | 3-5분 | 10초 | **95% 단축** |
| **이메일 인증** | 필수 대기 | 자동 완료 | - |
| **사용자 이탈** | 이메일 인증 단계에서 이탈 | 즉시 완료 | - |

---

## 코드 위치

```
backend/accounts/auth/google_auth.py      # GoogleAuthService
backend/accounts/auth/views.py            # GoogleOAuthView
backend/accounts/tests/tests.py           # Google OAuth 테스트
```

**핵심 로직 (3줄)**:
```python
idinfo = id_token.verify_oauth2_token(token, requests.Request(), client_id)
user, created = GoogleAuthService.get_or_create_user(idinfo)
refresh = RefreshToken.for_user(user)
```

---

**작성일**: 2025-10-22
**키워드**: Google OAuth, 소셜 로그인, 이메일 인증 자동화
