# GitHub Actions CD 설정 가이드

이 문서는 GitHub Actions를 사용하여 EC2로 자동 배포를 설정하는 방법을 안내합니다.

---

## 🎯 배포 흐름

```
git push origin main
    ↓
GitHub Actions 트리거
    ↓
EC2에 SSH 접속
    ↓
git pull origin main
    ↓
./deploy.sh 실행
    ↓
✅ 배포 완료!
```

---

## 📋 사전 준비

### 1. EC2 SSH 키 확인

EC2 인스턴스에 접속할 때 사용하는 `.pem` 파일이 필요합니다.

**파일 위치 예시:**
```bash
# 로컬 컴퓨터에서
ls ~/.ssh/your-ec2-key.pem

# 또는
ls ~/Downloads/your-ec2-key.pem
```

**키 파일이 없는 경우:**
1. AWS Console → EC2 → Key Pairs
2. 새 키 페어 생성
3. `.pem` 파일 다운로드

### 2. EC2 정보 확인

다음 정보를 확인하세요:

```bash
# SSH 접속 테스트
ssh -i ~/.ssh/your-key.pem ubuntu@reseeall.com

# 프로젝트 경로 확인
pwd  # 예: /home/ubuntu/Resee-project
```

필요한 정보:
- **EC2_HOST**: `reseeall.com` (또는 IP 주소)
- **EC2_USER**: `ubuntu` (기본값)
- **EC2_SSH_KEY**: `.pem` 파일 내용 전체
- **PROJECT_PATH**: `/home/ubuntu/Resee-project` (프로젝트 경로)

---

## ⚙️ GitHub Secrets 설정

### 1. GitHub 저장소로 이동

```
https://github.com/your-username/Resee-project
```

### 2. Settings → Secrets and variables → Actions

```
Settings (상단 탭)
  → Secrets and variables (왼쪽 메뉴)
    → Actions
      → New repository secret (녹색 버튼)
```

### 3. 다음 4개의 Secrets 생성

#### Secret 1: EC2_HOST

```
Name: EC2_HOST
Value: reseeall.com
```

#### Secret 2: EC2_USER

```
Name: EC2_USER
Value: ubuntu
```

#### Secret 3: EC2_SSH_KEY

```
Name: EC2_SSH_KEY
Value: [.pem 파일 전체 내용]
```

**.pem 파일 내용 복사 방법:**

**Mac/Linux:**
```bash
cat ~/.ssh/your-ec2-key.pem | pbcopy  # Mac (클립보드 복사)
cat ~/.ssh/your-ec2-key.pem           # Linux (출력 후 복사)
```

**Windows (PowerShell):**
```powershell
Get-Content ~\.ssh\your-ec2-key.pem | Set-Clipboard
```

**중요:** 다음 형식을 포함하여 전체 내용을 복사하세요:
```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
(여러 줄)
...
-----END RSA PRIVATE KEY-----
```

#### Secret 4: PROJECT_PATH

```
Name: PROJECT_PATH
Value: /home/ubuntu/Resee-project
```

**프로젝트 경로 확인:**
```bash
# EC2에 SSH 접속 후
cd Resee-project
pwd  # 출력된 경로 사용
```

---

## ✅ 설정 완료 확인

### 1. Secrets 확인

GitHub → Settings → Secrets and variables → Actions에서 다음 4개가 있는지 확인:

- ✅ `EC2_HOST`
- ✅ `EC2_USER`
- ✅ `EC2_SSH_KEY`
- ✅ `PROJECT_PATH`

### 2. 워크플로우 파일 확인

```bash
ls .github/workflows/deploy.yml
```

---

## 🚀 첫 자동 배포 테스트

### 1. 테스트 커밋 푸시

```bash
# 간단한 변경사항 만들기
echo "# Auto-deploy test" >> README.md

git add README.md
git commit -m "test: Verify GitHub Actions CD setup"
git push origin main
```

### 2. GitHub Actions 모니터링

```
GitHub 저장소 → Actions 탭 → "Deploy to EC2" 워크플로우 클릭
```

**확인 사항:**
- ✅ 워크플로우가 자동으로 시작됨
- ✅ "Deploy to EC2" 단계 진행
- ✅ 녹색 체크마크 (성공)

### 3. 배포 로그 확인

Actions 탭에서 워크플로우를 클릭하면 다음과 같은 로그가 보입니다:

```
🚀 Starting deployment...
📥 Pulling latest code...
🔧 Running deployment script...
✅ Deployment completed successfully!
```

### 4. 서비스 확인

```bash
# 웹사이트 접속
https://reseeall.com

# API 헬스체크
https://reseeall.com/api/health/
```

---

## 🔧 일상적인 사용

### 배포 방법

이제 코드 변경 후 다음만 하면 됩니다:

```bash
git add .
git commit -m "feat: Add new feature"
git push origin main  # 자동 배포 시작!
```

### 수동 배포 (필요 시)

GitHub Actions를 통한 수동 실행:

```
GitHub → Actions → Deploy to EC2 → Run workflow (오른쪽 버튼)
```

### 배포 상태 확인

```
GitHub → Actions 탭
```

- 🟢 녹색: 배포 성공
- 🔴 빨간색: 배포 실패
- 🟡 노란색: 배포 진행 중

---

## 🐛 트러블슈팅

### 문제 1: "Host key verification failed"

**원인**: EC2 호스트 키가 GitHub Actions 러너에 없음

**해결**: `.github/workflows/deploy.yml`에 다음 옵션이 있는지 확인:
```yaml
with:
  host: ${{ secrets.EC2_HOST }}
  username: ${{ secrets.EC2_USER }}
  key: ${{ secrets.EC2_SSH_KEY }}
```

### 문제 2: "Permission denied (publickey)"

**원인**: SSH 키가 올바르지 않음

**해결**:
1. `.pem` 파일 전체 내용 복사 확인
2. `-----BEGIN`과 `-----END` 포함 확인
3. GitHub Secrets에서 `EC2_SSH_KEY` 재설정

### 문제 3: "No such file or directory"

**원인**: 프로젝트 경로가 잘못됨

**해결**:
```bash
# EC2에 SSH 접속
ssh -i ~/.ssh/your-key.pem ubuntu@reseeall.com

# 프로젝트 경로 확인
cd Resee-project
pwd  # 출력된 경로를 PROJECT_PATH에 설정
```

### 문제 4: "./deploy.sh: Permission denied"

**원인**: deploy.sh 실행 권한 없음

**해결**:
```bash
# EC2에서
cd /home/ubuntu/Resee-project
chmod +x deploy.sh
git add deploy.sh
git commit -m "fix: Add execute permission to deploy.sh"
git push origin main
```

### 문제 5: "git pull" 실패

**원인**: EC2에서 git 인증 실패

**해결**:
```bash
# EC2에서 GitHub 인증 설정
git config --global credential.helper store

# 또는 SSH 키 사용
git remote set-url origin git@github.com:your-username/Resee-project.git
```

### 문제 6: 배포 타임아웃

**원인**: 배포가 30분 이상 소요

**해결**: `.github/workflows/deploy.yml`에서 타임아웃 증가:
```yaml
command_timeout: 60m  # 60분으로 증가
```

---

## 📊 배포 로그 확인

### GitHub Actions 로그

```
GitHub → Actions → 워크플로우 클릭 → Deploy to EC2 단계
```

### EC2 실시간 로그

```bash
# EC2에 SSH 접속
ssh -i ~/.ssh/your-key.pem ubuntu@reseeall.com

# Docker 로그 확인
cd /home/ubuntu/Resee-project
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 🔒 보안 권장사항

### 1. SSH 키 보안

- ✅ `.pem` 파일을 GitHub에 커밋하지 마세요
- ✅ `.pem` 파일 권한: `chmod 400 your-key.pem`
- ✅ GitHub Secrets만 사용
- ✅ 정기적으로 SSH 키 로테이션

### 2. 배포 권한

```bash
# EC2에서 최소 권한 원칙
# ubuntu 사용자만 프로젝트 디렉토리 접근 가능
chown -R ubuntu:ubuntu /home/ubuntu/Resee-project
chmod 755 /home/ubuntu/Resee-project
```

### 3. 브랜치 보호

GitHub → Settings → Branches → Add rule:
- Branch name pattern: `main`
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass before merging

---

## 📈 고급 설정 (선택사항)

### 1. Slack 알림 추가

`.github/workflows/deploy.yml`에 추가:

```yaml
- name: Notify Slack on Success
  if: success()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
    payload: |
      {
        "text": "✅ Deployment to production succeeded!"
      }
```

### 2. 배포 전 테스트 실행

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          docker-compose exec backend python -m pytest
          docker-compose exec frontend npm test

  deploy:
    needs: test  # 테스트 통과 후에만 배포
    runs-on: ubuntu-latest
    # ... 기존 배포 단계
```

### 3. 롤백 기능

```yaml
- name: Create backup before deployment
  run: |
    BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
    docker-compose -f docker-compose.prod.yml exec backend \
      pg_dump -U postgres resee_prod > backup_${BACKUP_DATE}.sql
```

---

## 🎓 학습 자료

- [GitHub Actions 공식 문서](https://docs.github.com/en/actions)
- [appleboy/ssh-action](https://github.com/appleboy/ssh-action)
- [GitHub Secrets 사용법](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

---

## ✅ 체크리스트

배포 자동화 설정 완료 확인:

- [ ] GitHub Secrets 4개 설정 완료
- [ ] `.github/workflows/deploy.yml` 파일 존재
- [ ] 테스트 커밋 푸시 성공
- [ ] GitHub Actions에서 녹색 체크마크 확인
- [ ] https://reseeall.com 정상 접속
- [ ] API 헬스체크 정상 응답

모두 체크했다면 설정 완료입니다! 🎉

---

## 📞 문제 발생 시

1. GitHub Actions 로그 확인
2. EC2 Docker 로그 확인
3. 이 문서의 트러블슈팅 섹션 참고
4. TROUBLESHOOTING.md 문서 참고
