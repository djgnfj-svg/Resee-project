# CI/CD 파이프라인 가이드

Resee 프로젝트의 자동화된 CI/CD 파이프라인 설정 및 사용 가이드입니다.

## 📋 개요

### 구성된 워크플로우
1. **CI Pipeline** (`.github/workflows/ci.yml`)
   - 자동 테스트 실행
   - 코드 품질 검사
   - 보안 스캔
   - Docker 이미지 빌드 및 푸시

2. **배포 파이프라인** (`.github/workflows/deploy.yml`)
   - Staging 자동 배포
   - Production 수동 승인 배포
   - 롤백 기능

3. **E2E 테스트** (`.github/workflows/e2e-tests.yml`)
   - End-to-End 테스트
   - 접근성 테스트
   - 성능 테스트

## 🔧 초기 설정

### 1. GitHub Secrets 설정

GitHub 리포지토리의 Settings > Secrets and variables > Actions에서 다음 secrets를 설정하세요:

#### Staging 환경
```
STAGING_HOST=your-staging-server-ip
STAGING_USER=ubuntu
STAGING_SSH_KEY=your-private-ssh-key
STAGING_PORT=22
STAGING_DATABASE_URL=postgresql://user:pass@host:5432/db
STAGING_SECRET_KEY=your-staging-secret-key
STAGING_ALLOWED_HOSTS=staging.yourdomain.com
```

#### Production 환경
```
PRODUCTION_HOST=your-production-server-ip
PRODUCTION_USER=ubuntu
PRODUCTION_SSH_KEY=your-private-ssh-key
PRODUCTION_PORT=22
PRODUCTION_DATABASE_URL=postgresql://user:pass@host:5432/db
PRODUCTION_SECRET_KEY=your-production-secret-key
PRODUCTION_ALLOWED_HOSTS=yourdomain.com
PRODUCTION_DOMAIN=yourdomain.com
```

#### 선택적 설정
```
SLACK_WEBHOOK_URL=your-slack-webhook-for-notifications
CODECOV_TOKEN=your-codecov-token
```

### 2. 서버 SSH 키 설정

배포 대상 서버에서 SSH 키를 설정하세요:

```bash
# 로컬에서 SSH 키 생성
ssh-keygen -t ed25519 -C "github-actions@resee.com"

# 공개 키를 서버에 복사
ssh-copy-id ubuntu@your-server-ip

# 개인 키를 GitHub Secrets에 추가 (STAGING_SSH_KEY, PRODUCTION_SSH_KEY)
cat ~/.ssh/id_ed25519
```

### 3. 서버 환경 준비

배포 대상 서버에서 필요한 소프트웨어를 설치하세요:

```bash
# Docker 및 Docker Compose 설치
sudo apt update
sudo apt install docker.io docker-compose git -y
sudo usermod -aG docker ubuntu

# 프로젝트 디렉토리 준비
sudo mkdir -p /home/ubuntu/resee
sudo chown ubuntu:ubuntu /home/ubuntu/resee

# 프로젝트 클론
git clone https://github.com/yourusername/resee.git /home/ubuntu/resee
```

## 🚀 CI/CD 파이프라인 사용법

### 자동 트리거

#### CI 파이프라인
- `main`, `develop` 브랜치로 푸시할 때
- `main` 브랜치로 PR 생성할 때

#### Staging 배포
- `main` 브랜치로 푸시할 때 자동 배포

#### Production 배포
- `v*` 태그 푸시할 때 (예: `v1.0.0`)
- 수동 트리거 (workflow_dispatch)

### 수동 배포

GitHub 웹 인터페이스에서 수동으로 배포를 트리거할 수 있습니다:

1. GitHub 리포지토리 → Actions 탭
2. "Deploy to Production" 워크플로우 선택
3. "Run workflow" 클릭
4. 환경 선택 (staging/production)

### 태그를 통한 Production 배포

```bash
# 새 버전 태그 생성 및 푸시
git tag v1.0.0
git push origin v1.0.0
```

## 📊 모니터링 및 로그

### 배포 상태 확인

```bash
# 서버에서 서비스 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend

# Health check
curl http://your-server/api/health/
```

### GitHub Actions 로그
- GitHub Actions 탭에서 워크플로우 실행 결과 확인
- 실패한 단계의 상세 로그 확인 가능

## 🔄 배포 전략

### Staging 환경
- `main` 브랜치의 모든 변경사항이 자동으로 배포
- 테스트 데이터 자동 생성
- 개발자 및 QA 테스트용

### Production 환경
- 태그 기반 또는 수동 배포만
- 배포 전 자동 백업
- 실패 시 자동 롤백

## 🛠️ 로컬 배포 스크립트

서버에서 직접 배포할 때 사용할 수 있는 스크립트:

```bash
# 권한 부여 (최초 1회)
chmod +x scripts/deploy.sh

# Staging 배포
./scripts/deploy.sh staging

# Production 배포
./scripts/deploy.sh production
```

## 📝 환경 설정 파일

### `.env.staging`
- Staging 환경용 설정
- 테스트 계정 자동 생성
- 상대적으로 관대한 보안 설정

### `.env.prod`
- Production 환경용 설정
- 엄격한 보안 설정
- 모니터링 및 백업 설정

## 🔐 보안 고려사항

### Secrets 관리
- 모든 중요한 정보는 GitHub Secrets에 저장
- 환경 파일은 리포지토리에 커밋하지 않음
- 정기적인 비밀번호 및 키 교체

### 서버 보안
- SSH 키 기반 인증만 허용
- 방화벽 설정으로 필요한 포트만 개방
- 정기적인 보안 업데이트

## 📈 테스트 커버리지

### 백엔드
- 단위 테스트: pytest
- 통합 테스트: Django TestCase
- 목표 커버리지: 80% 이상

### 프론트엔드
- 단위 테스트: Jest + React Testing Library
- E2E 테스트: Playwright
- 목표 커버리지: 70% 이상

### 접근성 및 성능
- axe-core를 통한 접근성 테스트
- Lighthouse를 통한 성능 측정

## 🚨 문제 해결

### 일반적인 문제

#### 배포 실패
1. GitHub Secrets 확인
2. 서버 SSH 연결 확인
3. 디스크 공간 확인
4. 로그 파일 검토

#### 테스트 실패
1. 의존성 버전 충돌 확인
2. 환경 변수 설정 확인
3. 데이터베이스 마이그레이션 상태 확인

#### Docker 이미지 빌드 실패
1. Dockerfile 문법 확인
2. 기본 이미지 버전 확인
3. 빌드 컨텍스트 크기 확인

### 긴급 롤백

Production에서 문제가 발생한 경우:

```bash
# 서버에서 직접 롤백
cd /home/ubuntu/resee
git reset --hard HEAD~1
docker-compose -f docker-compose.prod.yml restart
```

## 📞 지원

문제가 해결되지 않는 경우:
1. GitHub Issues에 문제 보고
2. 팀 Slack 채널에 문의
3. 로그 파일과 함께 상세한 문제 설명 제공

---

**주의**: Production 배포는 항상 신중하게 진행하고, 배포 전 Staging 환경에서 충분한 테스트를 완료하세요.