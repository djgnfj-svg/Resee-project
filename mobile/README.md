# Resee Mobile App

React Native 모바일 앱 - 스마트 복습 플랫폼

## 📱 프로젝트 구조

```
mobile/
├── src/
│   ├── api/              # API 클라이언트 (auth, content, review)
│   ├── components/       # 재사용 가능한 컴포넌트
│   ├── screens/          # 화면 컴포넌트
│   │   ├── Auth/         # 로그인, 회원가입
│   │   ├── Home/         # 홈 대시보드
│   │   ├── Content/      # 콘텐츠 관리
│   │   ├── Review/       # 복습 기능
│   │   ├── Stats/        # 통계
│   │   └── Profile/      # 프로필
│   ├── navigation/       # React Navigation 설정
│   ├── contexts/         # Context API (AuthContext)
│   ├── utils/            # 유틸리티 (API client, storage, config)
│   └── types/            # TypeScript 타입 정의
├── android/              # Android 네이티브 코드
├── ios/                  # iOS 네이티브 코드
└── App.tsx               # 앱 엔트리포인트
```

## 🚀 시작하기

### 1. 환경 설정

**필수 요구사항:**
- Node.js 18+
- React Native CLI
- Android Studio (Android) 또는 Xcode (iOS)

**macOS (iOS 개발):**
```bash
# Homebrew 설치 (없는 경우)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Node.js 설치
brew install node

# Watchman 설치
brew install watchman

# CocoaPods 설치
sudo gem install cocoapods
```

**Windows/Linux (Android 개발):**
- Android Studio 설치
- Android SDK 및 emulator 설정

### 2. 의존성 설치

```bash
cd mobile
npm install

# iOS의 경우 (macOS만)
cd ios && pod install && cd ..
```

### 3. 환경 변수 설정

`src/utils/config.ts` 파일에서 API URL을 확인하세요:

```typescript
// iOS Simulator
DEV_BASE_URL: 'http://localhost:8000'

// Android Emulator
DEV_BASE_URL: 'http://10.0.2.2:8000'

// 실제 기기 (같은 네트워크)
DEV_BASE_URL: 'http://<your-computer-ip>:8000'
```

### 4. 앱 실행

**iOS:**
```bash
npm run ios

# 또는 특정 시뮬레이터
npm run ios -- --simulator="iPhone 15 Pro"
```

**Android:**
```bash
# 에뮬레이터를 먼저 실행한 후
npm run android
```

**Metro Bundler 수동 시작:**
```bash
npm start
```

## 🔧 개발 명령어

```bash
# TypeScript 타입 체크
npm run type-check

# ESLint 검사
npm run lint

# 테스트
npm test
```

## 📦 주요 패키지

- **React Navigation** - 화면 네비게이션
- **React Query** - 서버 상태 관리
- **React Native Paper** - Material Design UI 컴포넌트
- **Axios** - HTTP 클라이언트
- **React Native Encrypted Storage** - 보안 저장소 (토큰 관리)
- **React Native Vector Icons** - 아이콘

## 🎨 화면 구성

### 인증 (Auth)
- ✅ **로그인** - 이메일/비밀번호 로그인
- ✅ **회원가입** - 신규 사용자 등록
- ⏳ **비밀번호 찾기** - 비밀번호 재설정 (준비 중)

### 메인 (Main)
- ✅ **홈** - 대시보드, 오늘의 복습 요약
- ✅ **콘텐츠** - 학습 콘텐츠 목록 및 관리
- ✅ **복습** - 복습 스케줄 및 진행
- ⏳ **통계** - 학습 통계 및 분석 (준비 중)
- ✅ **프로필** - 사용자 설정 및 로그아웃

## ⚠️ 백엔드 수정 필요사항

현재 백엔드는 웹 전용으로 설정되어 있어 모바일 지원을 위해 다음 수정이 필요합니다:

### 1. Refresh Token 응답 포함 (필수)

**현재 문제:**
- 백엔드가 refresh token을 HttpOnly Cookie로만 반환
- React Native는 브라우저가 아니므로 HttpOnly Cookie 사용 불가

**해결 방법:**
`backend/accounts/auth/views.py`의 `EmailTokenObtainPairView` 수정:

```python
def post(self, request, *args, **kwargs):
    response = super().post(request, *args, **kwargs)

    # 모바일 클라이언트 체크
    is_mobile = request.headers.get('X-Client-Type') == 'mobile'

    if response.status_code == 200 and 'refresh' in response.data:
        refresh_token = response.data.pop('refresh')

        if is_mobile:
            # 모바일: refresh token을 응답에 포함
            response.data['refresh'] = str(refresh_token)
        else:
            # 웹: HttpOnly Cookie 사용 (기존 방식)
            set_refresh_token_cookie(response, refresh_token)

    return response
```

동일하게 `CookieTokenRefreshView`도 수정 필요.

### 2. CORS 설정 (개발 환경)

개발 시 localhost에서 테스트하려면 CORS 허용:

```python
# settings/development.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React 웹
    "http://localhost:8081",  # React Native Metro
]
```

## 🐛 트러블슈팅

### 빌드 에러

**iOS pod install 실패:**
```bash
cd ios
pod deintegrate
pod install
```

**Android 빌드 에러:**
```bash
cd android
./gradlew clean
cd ..
npm run android
```

### 네트워크 연결 에러

**iOS Simulator:**
- `http://localhost:8000` 사용
- 백엔드가 실행 중인지 확인

**Android Emulator:**
- `http://10.0.2.2:8000` 사용 (10.0.2.2 = 호스트 컴퓨터)

**실제 기기:**
- 같은 WiFi 네트워크 사용
- 컴퓨터 IP 주소 확인 후 사용
- 방화벽 설정 확인

### Metro Bundler 문제

```bash
# 캐시 삭제
npm start -- --reset-cache
```

## 📝 다음 단계

### 우선순위 HIGH
- [ ] 백엔드 모바일 인증 지원 추가
- [ ] 콘텐츠 작성/수정 화면 구현
- [ ] 복습 진행 화면 구현

### 우선순위 MEDIUM
- [ ] 마크다운 에디터/뷰어 통합
- [ ] 통계 차트 구현
- [ ] 푸시 알림 설정

### 우선순위 LOW
- [ ] 다크 모드 지원
- [ ] 오프라인 지원
- [ ] 성능 최적화

## 📄 라이선스

MIT License

## 🤝 기여

버그 제보 및 기능 제안은 GitHub Issues를 이용해주세요.
