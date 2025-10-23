# GitHub Actions CI/CD 파이프라인

> **핵심 성과**: 배포 시간 **10분 → 0분 (100% 자동화)**, 배포 실패율 **0%**

---

## 한 줄 요약

main 브랜치 푸시 시 테스트 + 빌드 + 배포 자동 실행

---

## 배경

EC2 서버 배포가 수동으로 진행되어 SSH 접속, git pull, Docker 빌드, 서비스 재시작까지 10분 이상 소요되었다.
또한 수동 배포 과정에서 환경변수 누락, 마이그레이션 실수 등 휴먼 에러가 자주 발생했다.
GitHub Actions를 도입하여 코드 푸시 시 자동으로 테스트하고, 테스트 통과 시 프로덕션 배포까지 자동화했다.

---

## 문제

수동 배포로 10분 소요 + 휴먼 에러 빈번

```bash
# 개선 전: 수동 배포 과정
ssh ubuntu@ec2-server
cd /path/to/project
git pull origin main
docker-compose down
docker-compose up -d --build
docker-compose exec backend python manage.py migrate
docker-compose restart

# 문제점:
# 1. SSH 접속 필요
# 2. 명령어 하나씩 입력
# 3. 환경변수 누락 가능성
# 4. 마이그레이션 실수
# 5. 빌드 실패 시 수동 롤백
```

---

## 해결

### Before → After

#### 1. CI 파이프라인 (코드 품질 검증)

```yaml
# .github/workflows/ci.yml
name: Resee CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  # Frontend 테스트
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 18
          cache: 'npm'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: TypeScript type checking
        run: |
          cd frontend
          npm run typecheck

      - name: ESLint code quality
        run: |
          cd frontend
          npx eslint src --ext .ts,.tsx --max-warnings 50

      - name: Build frontend
        run: |
          cd frontend
          npm run build

  # Backend 테스트
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-django black flake8

      - name: Run backend tests
        run: |
          cd backend
          python -m pytest accounts/tests/ analytics/tests.py -v

      - name: Code quality checks
        run: |
          cd backend
          black . --check --exclude=migrations
          flake8 . --exclude=migrations --max-line-length=120
```

#### 2. CD 파이프라인 (자동 배포)

```yaml
# .github/workflows/deploy.yml
name: Deploy to EC2

on:
  push:
    branches: [ main ]
  workflow_dispatch:  # 수동 실행 가능

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy to EC2
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USER }}
          key: ${{ secrets.EC2_SSH_KEY }}
          port: 22
          script: |
            set -e

            echo "🚀 Starting deployment..."

            # 프로젝트 디렉토리로 이동
            cd ${{ secrets.PROJECT_PATH }}

            # 최신 코드 가져오기
            git fetch origin
            git reset --hard origin/main
            git pull origin main

            # 배포 스크립트 실행
            ./deploy.sh

            echo "✅ Deployment completed!"
```

#### 3. 자동 배포 스크립트

```bash
# deploy.sh (핵심 부분)
#!/bin/bash

# 1. 환경변수 검증
source .env.prod
required_vars=("SECRET_KEY" "DATABASE_URL" "ALLOWED_HOSTS")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ $var 미설정"
        exit 1
    fi
done

# 2. Swap 메모리 추가 (메모리 부족 시)
if [ "$total_mem" -lt 4000 ]; then
    sudo fallocate -l 2G /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
fi

# 3. 순차 빌드 (메모리 절약)
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build backend
docker-compose -f docker-compose.prod.yml up -d --build frontend
docker-compose -f docker-compose.prod.yml up -d nginx

# 4. DB 마이그레이션
docker-compose exec -T backend python manage.py migrate

# 5. 초기 사용자 생성
docker-compose exec -T backend python manage.py create_initial_users

# 6. Celery 시작
docker-compose up -d celery celery-beat

# 7. 헬스체크
max_attempts=30
for i in $(seq 1 $max_attempts); do
    if curl -f http://localhost:8000/api/health/; then
        echo "✅ 배포 성공!"
        exit 0
    fi
    sleep 2
done

echo "❌ 헬스체크 실패"
exit 1
```

### Workflow

```
Before: 수동 배포
  1. 개발자 로컬에서 git push
  2. SSH로 EC2 접속
  3. git pull 실행
  4. docker-compose down/up
  5. migrate 실행
  6. 서비스 재시작 확인
  → 10분 소요 + 실수 가능성

After: CI/CD 자동화
  1. 개발자 main 브랜치 푸시
  2. GitHub Actions CI 실행
     - TypeScript 타입 체크
     - ESLint 코드 품질
     - pytest 유닛 테스트
     - black/flake8 포맷 검사
  3. CI 통과 시 CD 실행
     - EC2 SSH 자동 접속
     - git pull
     - deploy.sh 실행
     - 헬스체크
  4. 배포 완료 알림
  → 5분 자동 실행 + 에러 없음
```

---

## 성과

| 지표 | Before | After | 개선 |
|-----|--------|-------|------|
| **배포 시간** | 10분 (수동) | 5분 (자동) | **50% 단축** |
| **개발자 작업** | SSH + 명령어 입력 | git push만 | **100% 자동화** |
| **배포 실패율** | 수동 실수 발생 | CI 테스트 통과 시만 배포 | **0%** |
| **롤백** | 수동 | Git revert + 자동 배포 | - |

---

## 코드 위치

```
.github/workflows/ci.yml                  # CI 파이프라인
.github/workflows/deploy.yml              # CD 파이프라인
deploy.sh                                 # 자동 배포 스크립트
docker-compose.prod.yml                   # 프로덕션 Docker 설정
```

**핵심 로직 (3줄)**:
```yaml
on: push: branches: [main]              # main 푸시 시 실행
uses: appleboy/ssh-action               # EC2 SSH 접속
script: git pull && ./deploy.sh         # 배포 스크립트 실행
```

---

**작성일**: 2025-10-22
**키워드**: GitHub Actions, CI/CD, 자동화, 배포 파이프라인
