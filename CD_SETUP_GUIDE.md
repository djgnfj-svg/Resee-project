# GitHub Actions CD 설정 가이드

**목표**: `main` 브랜치에 푸시하면 자동으로 EC2 서버에 배포

---

## 📋 사전 준비

- ✅ EC2 인스턴스 실행 중
- ✅ GitHub 저장소 생성
- ✅ 로컬에서 코드 커밋 가능

---

## 🔐 Step 1: EC2 SSH 키페어 생성

### 1-1. EC2에 접속

```bash
ssh -i your-existing-key.pem ubuntu@your-ec2-ip
```

### 1-2. GitHub Actions용 SSH 키 생성

```bash
# ED25519 키 생성 (권장)
ssh-keygen -t ed25519 -C "github-actions-cd" -f ~/.ssh/github_cd_ed25519

# 프롬프트가 나오면 Enter 3번 (비밀번호 없음)
```

**출력 예시**:
```
Generating public/private ed25519 key pair.
Enter passphrase (empty for no passphrase): [Enter]
Enter same passphrase again: [Enter]
Your identification has been saved in /home/ubuntu/.ssh/github_cd_ed25519
Your public key has been saved in /home/ubuntu/.ssh/github_cd_ed25519.pub
```

### 1-3. 공개키를 authorized_keys에 추가

```bash
# 공개키를 authorized_keys에 추가
cat ~/.ssh/github_cd_ed25519.pub >> ~/.ssh/authorized_keys

# 권한 설정 (중요!)
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/github_cd_ed25519
chmod 644 ~/.ssh/github_cd_ed25519.pub
```

### 1-4. 개인키 복사 (GitHub Secret에 사용)

```bash
# 개인키 내용 출력 (복사해두기)
cat ~/.ssh/github_cd_ed25519
```

**출력 예시** (전체 복사):
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
...
(여러 줄)
...
-----END OPENSSH PRIVATE KEY-----
```

⚠️ **주의**: 이 키는 절대 GitHub 코드에 커밋하면 안 됩니다!

### 1-5. SSH 연결 테스트 (로컬에서)

```bash
# 로컬 머신에서 테스트
ssh -i ~/.ssh/github_cd_ed25519 ubuntu@your-ec2-ip

# 성공하면 접속됨
```

---

## 🔑 Step 2: GitHub Secrets 설정

### 2-1. GitHub 저장소로 이동

```
https://github.com/your-username/Resee-project
```

### 2-2. Settings → Secrets and variables → Actions

```
Repository Settings
  → Secrets and variables
    → Actions
      → New repository secret
```

### 2-3. 4개의 Secret 추가

#### Secret 1: `EC2_HOST`
```
Name: EC2_HOST
Value: 13.209.123.45  (예시 - 실제 EC2 IP 주소)
```

#### Secret 2: `EC2_USER`
```
Name: EC2_USER
Value: ubuntu
```

#### Secret 3: `EC2_SSH_KEY`
```
Name: EC2_SSH_KEY
Value: (Step 1-4에서 복사한 개인키 전체 내용)
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
...
-----END OPENSSH PRIVATE KEY-----
```

⚠️ **중요**:
- `-----BEGIN` 부터 `-----END`까지 **전체** 복사
- 앞뒤 공백 없이 정확히 복사

#### Secret 4: `PROJECT_PATH`
```
Name: PROJECT_PATH
Value: /home/ubuntu/Resee-project  (또는 실제 프로젝트 경로)
```

### 2-4. Secrets 확인

설정 완료 후 4개가 보여야 합니다:
```
✅ EC2_HOST
✅ EC2_USER
✅ EC2_SSH_KEY
✅ PROJECT_PATH
```

---

## 🖥️ Step 3: EC2 서버 설정

### 3-1. 프로젝트 클론 (처음인 경우)

```bash
# EC2에 접속
ssh ubuntu@your-ec2-ip

# 프로젝트 디렉토리 생성 및 클론
cd ~
git clone https://github.com/your-username/Resee-project.git

# 프로젝트 디렉토리로 이동
cd Resee-project
```

### 3-2. 환경변수 파일 설정

```bash
# .env.prod 파일 생성 (이미 있으면 스킵)
vi .env.prod
```

**필수 환경변수** (`.env.prod`):
```bash
# Django Core
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=reseeall.com,www.reseeall.com,your-ec2-ip
CSRF_TRUSTED_ORIGINS=https://reseeall.com,https://www.reseeall.com

# Database
POSTGRES_PASSWORD=postgres123
DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/resee_prod

# Frontend
FRONTEND_URL=https://reseeall.com
REACT_APP_API_URL=https://reseeall.com/api

# Email (Gmail SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
ENFORCE_EMAIL_VERIFICATION=True

# Admin Account (자동 생성)
ADMIN_EMAIL=djgnfj8923@naver.com
ADMIN_PASSWORD=your-secure-password

# Settings Module
DJANGO_SETTINGS_MODULE=resee.settings.production

# AI Services
ANTHROPIC_API_KEY=your-api-key
```

### 3-3. deploy.sh 실행 권한 추가

```bash
chmod +x deploy.sh
```

### 3-4. Docker 및 Docker Compose 설치 확인

```bash
# Docker 버전 확인
docker --version
docker-compose --version

# 설치 안 되어 있으면 deploy.sh가 자동 설치함
```

### 3-5. 첫 배포 (수동)

```bash
# 처음 한 번은 수동으로 배포
./deploy.sh
```

**예상 소요 시간**: 5-10분

---

## 🚀 Step 4: CD 워크플로우 테스트

### 4-1. 간단한 변경사항 커밋

```bash
# 로컬에서
cd /home/djgnf/projects/Resee-project

# 테스트용 변경
echo "# CD Test" >> CD_TEST.md

# 커밋 및 푸시
git add CD_TEST.md
git commit -m "test: CD workflow test"
git push origin main
```

### 4-2. GitHub Actions 확인

```
GitHub 저장소 → Actions 탭
```

**확인 사항**:
1. "Deploy to EC2" 워크플로우 실행 중
2. 로그에서 진행 상황 확인
   ```
   🚀 Starting deployment...
   📥 Pulling latest code...
   🔧 Running deployment script...
   ✅ Deployment completed successfully!
   ```

### 4-3. 배포 성공 확인

```bash
# EC2에서 확인
cd /home/ubuntu/Resee-project
git log -1  # 최신 커밋 확인

# 서비스 상태 확인
docker-compose -f docker-compose.prod.yml ps
```

### 4-4. 웹사이트 접속 테스트

```
https://reseeall.com
https://reseeall.com/api/health/
```

---

## 🐛 문제 해결 (Troubleshooting)

### 문제 1: SSH 연결 실패

**증상**:
```
Error: ssh: connect to host x.x.x.x port 22: Connection refused
```

**해결**:
```bash
# EC2 보안 그룹에서 22번 포트 열기
AWS Console → EC2 → Security Groups
  → Inbound rules → Edit
    → Add rule: SSH (22), Source: GitHub Actions IP 범위
```

**또는 모든 IP 허용** (비권장):
```
SSH | TCP | 22 | 0.0.0.0/0
```

### 문제 2: Permission denied (publickey)

**증상**:
```
Error: ubuntu@x.x.x.x: Permission denied (publickey)
```

**해결**:
```bash
# EC2에서 authorized_keys 재확인
cat ~/.ssh/authorized_keys  # 공개키가 있는지 확인

# 권한 재설정
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

### 문제 3: Git pull 실패

**증상**:
```
error: Your local changes to the following files would be overwritten by merge
```

**해결**:
```bash
# EC2에서
cd /home/ubuntu/Resee-project

# 로컬 변경사항 백업 후 초기화
git stash
git pull origin main

# 또는 강제 pull
git fetch origin
git reset --hard origin/main
```

### 문제 4: deploy.sh 실행 권한 오류

**증상**:
```
./deploy.sh: Permission denied
```

**해결**:
```bash
chmod +x deploy.sh
```

### 문제 5: Docker 빌드 메모리 부족

**증상**:
```
Error: OOMKilled (Out of Memory)
```

**해결**:
```bash
# Swap 메모리 확인 (deploy.sh가 자동 추가하지만 확인)
free -h

# 수동 추가 (필요시)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 문제 6: .env.prod 파일 없음

**증상**:
```
Error: .env.prod file not found
```

**해결**:
```bash
# EC2에서 .env.prod 생성
cd /home/ubuntu/Resee-project
cp .env.example .env.prod
vi .env.prod  # 실제 값 입력
```

---

## 📊 배포 플로우

```
┌─────────────────────────────────────────────────────┐
│ 1. 개발자가 main 브랜치에 푸시                        │
│    git push origin main                             │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 2. GitHub Actions 워크플로우 자동 실행               │
│    - Checkout code                                  │
│    - SSH to EC2                                     │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 3. EC2 서버에서 자동 실행                            │
│    - git pull origin main                           │
│    - ./deploy.sh                                    │
│      ├─ Docker 빌드                                 │
│      ├─ 컨테이너 재시작                             │
│      ├─ 마이그레이션                                │
│      ├─ 정적 파일 수집                              │
│      └─ 서비스 헬스체크                             │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 4. 배포 완료                                         │
│    https://reseeall.com 업데이트됨                   │
└─────────────────────────────────────────────────────┘
```

---

## 🔒 보안 체크리스트

배포 전 확인:

- [ ] EC2 SSH 키를 GitHub Secrets에만 저장
- [ ] `.env.prod` 파일을 `.gitignore`에 추가
- [ ] SSH 22번 포트를 필요한 IP만 허용 (옵션)
- [ ] EC2 보안 그룹에서 80, 443 포트만 공개
- [ ] `ADMIN_PASSWORD`가 강력한 비밀번호로 설정됨
- [ ] `SECRET_KEY`가 프로덕션 전용으로 생성됨
- [ ] `DEBUG=False` 설정됨

---

## 🎯 배포 후 확인사항

```bash
# 1. 서비스 실행 확인
docker-compose -f docker-compose.prod.yml ps

# 2. 로그 확인
docker-compose -f docker-compose.prod.yml logs --tail=50

# 3. 헬스체크
curl https://reseeall.com/api/health/

# 4. 관리자 로그인 테스트
# https://reseeall.com/admin/
# Email: djgnfj8923@naver.com
# Password: (ADMIN_PASSWORD)
```

---

## 📈 CI/CD 개선 방향

### 현재 (Basic CD)
```
Push → Deploy → Done
```

### 향후 개선 (Full CI/CD)
```
Push → Test → Build → Deploy → Healthcheck → Rollback (if fail)
```

**추가 가능한 기능**:
1. **자동 테스트**: pytest, npm test
2. **린팅**: black, eslint
3. **타입 체크**: mypy, TypeScript
4. **보안 스캔**: Snyk, Trivy
5. **롤백**: 이전 버전으로 자동 복구
6. **알림**: Slack, Discord 배포 알림

---

## 📚 관련 파일

- `.github/workflows/deploy.yml` - CD 워크플로우
- `deploy.sh` - 배포 스크립트
- `.env.prod` - 프로덕션 환경변수 (서버에만 존재)
- `docker-compose.prod.yml` - 프로덕션 Docker 설정

---

**최종 확인**: 이제 `main` 브랜치에 푸시할 때마다 자동으로 프로덕션 배포됩니다! 🚀
