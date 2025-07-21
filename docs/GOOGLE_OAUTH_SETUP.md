# Google OAuth 2.0 설정 가이드

Google OAuth 2.0을 통한 소셜 로그인을 설정하려면 다음 단계를 따르세요.

## 1. Google APIs Console 설정

### 1.1 Google Cloud Console 접속
1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. Google 계정으로 로그인

### 1.2 프로젝트 생성 또는 선택
1. 상단의 프로젝트 선택 드롭다운 클릭
2. 새 프로젝트 생성하거나 기존 프로젝트 선택
3. 프로젝트 이름: `Resee` (또는 원하는 이름)

### 1.3 Google+ API 활성화
1. 왼쪽 사이드바에서 "APIs & Services" > "Library" 선택
2. "Google+ API" 검색 후 클릭
3. "Enable" 버튼 클릭하여 API 활성화

### 1.4 OAuth 2.0 클라이언트 ID 생성
1. 왼쪽 사이드바에서 "APIs & Services" > "Credentials" 선택
2. 상단의 "+ CREATE CREDENTIALS" 클릭
3. "OAuth client ID" 선택

### 1.5 OAuth 동의 화면 설정 (필요시)
처음 OAuth 클라이언트를 생성하는 경우:
1. "CONFIGURE CONSENT SCREEN" 클릭
2. "External" 선택 후 "CREATE"
3. 필수 정보 입력:
   - App name: `Resee`
   - User support email: 본인 이메일
   - Developer contact information: 본인 이메일
4. "SAVE AND CONTINUE" 클릭
5. Scopes 화면에서 "SAVE AND CONTINUE"
6. Test users 화면에서 "SAVE AND CONTINUE"

### 1.6 웹 애플리케이션 클라이언트 생성
1. Application type: "Web application" 선택
2. Name: "Resee Frontend" (또는 원하는 이름)
3. Authorized JavaScript origins 추가:
   - 개발환경: `http://localhost:3000`
   - 프로덕션환경: `https://yourdomain.com`
4. Authorized redirect URIs는 비워둠 (Google Identity Services 사용시 불필요)
5. "CREATE" 클릭

### 1.7 클라이언트 ID 복사
1. 생성된 클라이언트의 "Client ID" 복사
2. "Client secret"도 함께 복사해둠

## 2. 백엔드 환경 변수 설정

### 2.1 Docker 환경 변수 설정
`docker-compose.yml` 파일의 backend 서비스에 환경 변수 추가:

```yaml
backend:
  environment:
    - GOOGLE_OAUTH2_CLIENT_ID=your_client_id_here
    - GOOGLE_OAUTH2_CLIENT_SECRET=your_client_secret_here
```

### 2.2 .env 파일 설정 (선택사항)
백엔드 루트에 `.env` 파일 생성:

```env
GOOGLE_OAUTH2_CLIENT_ID=your_client_id_here
GOOGLE_OAUTH2_CLIENT_SECRET=your_client_secret_here
```

## 3. 프론트엔드 환경 변수 설정

### 3.1 .env 파일 설정
`frontend/.env` 파일에 Client ID 추가:

```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_GOOGLE_CLIENT_ID=your_client_id_here
```

⚠️ **중요**: 프론트엔드에는 Client ID만 필요하고, Client Secret은 절대 프론트엔드에 포함하지 마세요!

## 4. 개발 환경 테스트

### 4.1 서비스 재시작
```bash
docker-compose down
docker-compose up -d
```

### 4.2 Google 로그인 테스트
1. `http://localhost:3000/login` 접속
2. "Google로 로그인" 버튼 클릭
3. Google 계정으로 로그인
4. 자동으로 대시보드로 리다이렉트 확인

## 5. 프로덕션 배포시 주의사항

### 5.1 도메인 업데이트
Google APIs Console에서 Authorized JavaScript origins에 프로덕션 도메인 추가:
- `https://yourdomain.com`
- `https://www.yourdomain.com` (필요시)

### 5.2 환경 변수 설정
프로덕션 환경의 환경 변수 파일에 실제 값 설정

### 5.3 HTTPS 필수
프로덕션에서는 반드시 HTTPS를 사용해야 합니다.

## 6. 트러블슈팅

### 6.1 일반적인 오류

**"Error: Invalid request (Invalid app ID)"**
- `REACT_APP_GOOGLE_CLIENT_ID`가 올바르게 설정되었는지 확인
- 브라우저 캐시 및 로컬 스토리지 클리어

**"Error: Origin mismatch"**
- Google APIs Console에서 Authorized JavaScript origins 확인
- 정확한 도메인과 포트가 등록되었는지 확인

**백엔드 토큰 검증 실패**
- `GOOGLE_OAUTH2_CLIENT_ID`가 백엔드에 올바르게 설정되었는지 확인
- 백엔드와 프론트엔드에서 동일한 Client ID 사용하는지 확인

### 6.2 디버깅 팁
- 브라우저 개발자 도구의 Console에서 오류 메시지 확인
- Network 탭에서 API 호출 상태 확인
- 백엔드 로그에서 토큰 검증 과정 확인

## 7. 보안 고려사항

- Client Secret은 절대 프론트엔드나 공개 저장소에 노출하지 말 것
- 환경 변수 파일 (`.env`)은 `.gitignore`에 추가
- 프로덕션에서는 적절한 도메인 제한 설정
- 정기적으로 OAuth 클라이언트 자격 증명 갱신 고려

---

이 가이드를 따라 설정하면 Google OAuth 2.0을 통한 소셜 로그인이 정상적으로 작동합니다.