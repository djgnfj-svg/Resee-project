# Resee Mobile App

React Native (Expo) 기반 모바일 애플리케이션

## 기술 스택

- **React Native**: Expo SDK
- **TypeScript**: 타입 안정성
- **Navigation**: React Navigation (Stack + Bottom Tabs)
- **State Management**:
  - React Query (서버 상태)
  - Context API (인증, 테마)
- **API Client**: Axios
- **Secure Storage**: expo-secure-store

## 프로젝트 구조

```
mobile/
├── src/
│   ├── api/              # API 클라이언트 (auth, content, review, exams, subscription)
│   ├── contexts/         # React Context (AuthContext)
│   ├── navigation/       # 네비게이션 구조
│   │   ├── types.ts     # 네비게이션 타입 정의
│   │   ├── AuthNavigator.tsx
│   │   ├── MainNavigator.tsx
│   │   ├── ContentNavigator.tsx
│   │   ├── ExamsNavigator.tsx
│   │   └── RootNavigator.tsx
│   ├── screens/         # 화면 컴포넌트
│   │   ├── auth/       # 로그인, 회원가입, 이메일 인증
│   │   ├── main/       # 대시보드, 복습, 프로필
│   │   ├── content/    # 콘텐츠 목록, 상세, 생성, 수정
│   │   └── exams/      # 시험 목록, 상세, 생성, 결과
│   ├── components/      # 재사용 가능한 컴포넌트
│   ├── types/          # TypeScript 타입 정의
│   ├── constants/      # 상수 (config, colors, etc.)
│   └── utils/          # 유틸리티 함수
├── App.tsx             # 앱 진입점
└── package.json
```

## 주요 기능

### 1. 인증 시스템
- 로그인/회원가입
- 이메일 인증
- JWT 토큰 관리 (Secure Store)
- 자동 토큰 갱신

### 2. 대시보드
- 오늘의 복습 개수
- 대기 중인 복습
- 전체 콘텐츠 수
- 성공률 통계

### 3. 학습 콘텐츠 관리
- 콘텐츠 목록 조회
- 콘텐츠 생성/수정/삭제
- 카테고리별 분류
- AI 콘텐츠 검증

### 4. 복습 시스템
- 에빙하우스 망각곡선 기반
- 4가지 복습 모드
  - objective: 객관식
  - descriptive: 서술형
  - multiple_choice: 다지선다
  - subjective: 주관식
- AI 답변 평가

### 5. AI 주간 시험
- 시험 생성
- 시험 풀이
- 결과 확인

### 6. 프로필 & 구독
- 프로필 관리
- 구독 티어 관리 (FREE/BASIC/PRO)

## 개발 환경 설정

### 1. 의존성 설치

```bash
npm install
```

### 2. 백엔드 연결 설정

개발 환경에서는 로컬 Docker 백엔드를 사용합니다:

```bash
# 프로젝트 루트에서 백엔드 실행
cd ..
docker-compose up -d
```

모바일 앱은 자동으로 `http://localhost:8000/api`에 연결됩니다.

### 3. 앱 실행

```bash
# Android
npm run android

# iOS (macOS만 가능)
npm run ios

# Web
npm run web

# Expo Go 앱으로 실행
npm start
```

## API 설정

API 엔드포인트는 `src/constants/config.ts`에서 설정됩니다:

```typescript
export const API_CONFIG = {
  BASE_URL: __DEV__
    ? 'http://localhost:8000/api'  // 개발 환경
    : 'https://resee-project-production.up.railway.app/api',  // 프로덕션
};
```

## 네비게이션 구조

```
RootNavigator
├── Auth (미인증 시)
│   ├── Login
│   ├── Register
│   ├── EmailVerification
│   └── VerificationPending
│
└── Main (인증 후)
    ├── DashboardTab
    ├── ContentTab (Stack)
    │   ├── ContentList
    │   ├── ContentDetail
    │   ├── ContentCreate
    │   └── ContentEdit
    ├── ReviewTab
    ├── ExamsTab (Stack)
    │   ├── ExamList
    │   ├── ExamDetail
    │   ├── ExamCreate
    │   └── ExamResult
    └── ProfileTab
```

## 상태 관리

### 서버 상태 (React Query)
- API 데이터 캐싱
- 자동 리페치
- 낙관적 업데이트

### 로컬 상태 (Context API)
- **AuthContext**: 사용자 인증 상태
  - `user`: 현재 로그인한 사용자
  - `login()`: 로그인
  - `register()`: 회원가입
  - `logout()`: 로그아웃
  - `isAuthenticated`: 인증 여부

## API 클라이언트

모든 API 요청은 `src/api/` 디렉토리에서 관리됩니다:

```typescript
// 사용 예시
import { authAPI, contentAPI, reviewAPI } from '../api';

// 로그인
await authAPI.login({ email, password });

// 콘텐츠 조회
const contents = await contentAPI.getContents();

// 복습 완료
await reviewAPI.completeReview(scheduleId, { result: 'remembered' });
```

## 보안

### 토큰 저장
- Access Token: Expo SecureStore에 암호화 저장
- 메모리에 캐싱하여 빠른 접근

### API 인터셉터
- 자동 Authorization 헤더 추가
- 401 에러 시 자동 로그아웃
- 사용자 친화적인 에러 메시지

## 테스트 계정

```
interview@resee.com / interview2025!   # PRO 티어
admin@resee.com / admin123!            # BASIC 티어, 관리자
```

## 다음 단계

### 우선순위 높음
1. Content 화면 구현 (목록, 생성, 수정)
2. Review 화면 구현 (오늘의 복습)
3. Exams 화면 구현 (시험 생성, 풀이)

### 우선순위 중간
1. 프로필 편집 기능
2. 비밀번호 변경
3. 알림 설정
4. 구독 관리

### 우선순위 낮음
1. 다크 모드
2. 오프라인 모드
3. 푸시 알림
4. 앱 내 결제

## 개발 팁

### Android 개발 시 localhost 연결

Android 에뮬레이터에서 localhost 연결이 안 될 경우:

```typescript
// src/constants/config.ts
export const API_CONFIG = {
  BASE_URL: __DEV__
    ? 'http://10.0.2.2:8000/api'  // Android 에뮬레이터
    // ? 'http://localhost:8000/api'  // iOS 시뮬레이터
    : 'https://resee-project-production.up.railway.app/api',
};
```

### 디버깅

```bash
# React Native 디버거
npm start -- --dev-client

# Expo 로그 확인
npx expo start --clear
```

## 참고 자료

- [React Navigation](https://reactnavigation.org/)
- [React Query](https://tanstack.com/query/latest)
- [Expo Documentation](https://docs.expo.dev/)
- [TypeScript](https://www.typescriptlang.org/)

## 라이선스

MIT
