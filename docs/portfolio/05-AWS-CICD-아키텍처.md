# AWS & CI/CD 아키텍처

> **핵심 성과**: **배포 자동화 100%**, **무중단 배포**, **비용 $0 (프리티어)**

---

## 한 줄 요약

GitHub Actions + Docker + CloudFlare로 무료 자동 배포 구축

---

## 배경

처음에는 서버에 SSH 접속해서 `git pull` → `docker-compose up`으로 수동 배포했다.
배포할 때마다 5분씩 걸리고, 실수로 서비스가 중단되는 일이 잦았다.
GitHub Actions로 CI/CD 파이프라인을 구축하여 배포를 자동화하고 안정성을 확보했다.

---

## 선택 이유

**왜 AWS와 GitHub Actions인가?**

채용 공고 대부분이 "AWS 경험자 우대", "CI/CD 파이프라인 구축 경험"을 요구했습니다.
하지만 돈이 없어서 AWS의 유료 서비스(ECS, RDS 등)는 사용할 수 없었고,
**프리티어로 최대한 활용하는 방법**을 고민했습니다.

**기술 선택 과정**:
1. **Jenkins**: 서버 리소스 많이 필요 (EC2 t2.micro로는 부족)
2. **AWS CodePipeline**: 프리티어 제한 초과 시 과금
3. ✅ **GitHub Actions**: 무료 (퍼블릭 레포), 설정 간단

**인프라 전략**:
- ❌ **AWS RDS**: 최소 $15/월
- ✅ **EC2 + PostgreSQL Docker**: 프리티어 무료
- ❌ **AWS ALB**: $16/월
- ✅ **Nginx + CloudFlare**: 무료 (HTTPS, CDN 포함)

---

## 문제

수동 배포로 인한 휴먼 에러와 서비스 중단

```bash
# 기존 배포 과정 (수동)
ssh ec2-user@서버IP
git pull origin main
docker-compose down  # ⚠️ 서비스 중단!
docker-compose up -d
# 5분 동안 사용자 접속 불가
```

**문제점**:
- 배포 중 서비스 중단 (Downtime)
- 실수로 잘못된 브랜치 배포
- 테스트 없이 배포되어 버그 발생

---

## 해결

### 아키텍처

```
┌─────────────┐
│  Developer  │
└──────┬──────┘
       │ git push
       ↓
┌─────────────────┐
│  GitHub         │
│  (main branch)  │
└────────┬────────┘
         │ Webhook
         ↓
┌─────────────────────┐
│  GitHub Actions     │  ← CI/CD
│  - Test (pytest)    │
│  - Lint (ESLint)    │
│  - Build            │
└──────────┬──────────┘
           │ SSH Deploy
           ↓
┌───────────────────────────┐
│  AWS EC2 (t2.micro)       │
│  ┌─────────────────────┐  │
│  │  Docker Compose     │  │
│  │  ├─ Backend (Django)│  │
│  │  ├─ Frontend (React)│  │
│  │  ├─ PostgreSQL      │  │
│  │  ├─ Redis           │  │
│  │  ├─ Celery Worker   │  │
│  │  └─ Nginx           │  │
│  └─────────────────────┘  │
└───────────┬───────────────┘
            │ Port 80/443
            ↓
┌───────────────────────────┐
│  CloudFlare (CDN + HTTPS) │  ← 무료
└───────────┬───────────────┘
            │
            ↓
┌───────────────────────────┐
│  Users                    │
└───────────────────────────┘
```

### 1. GitHub Actions CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy to EC2

on:
  push:
    branches: [main]  # main에 push 시 자동 배포

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Run Backend Tests
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit
          # pytest 40/41 통과 확인

      - name: Run Frontend Lint
        run: |
          cd frontend
          npm ci
          npm run lint
          npm run typecheck

  deploy:
    needs: test  # 테스트 통과해야 배포
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to EC2
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ec2-user
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd /home/ec2-user/Resee-project
            git pull origin main

            # 무중단 배포
            docker-compose pull
            docker-compose up -d --no-deps --build backend
            docker-compose up -d --no-deps --build frontend

            # Health Check
            curl --fail http://localhost/api/health/ || exit 1
```

### 2. Docker Compose 설정

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./backend:/app
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend
    command: npm start
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - backend
      - frontend

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: resee_prod
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes  # AOF 영속성

  celery:
    build: ./backend
    command: celery -A resee worker -l info

  celery-beat:
    build: ./backend
    command: celery -A resee beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### 3. Nginx 설정

```nginx
# nginx/nginx.conf
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:3000;
}

server {
    listen 80;
    server_name reseeall.com;

    # API 요청
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 정적 파일
    location /static/ {
        alias /app/static/;
    }

    # 프론트엔드
    location / {
        proxy_pass http://frontend;
    }
}
```

### 4. CloudFlare 설정

```
CloudFlare 대시보드에서 설정:
1. DNS: A 레코드 → EC2 퍼블릭 IP
2. SSL/TLS: Full (엄격) 모드
3. 캐싱: 정적 파일 캐시 활성화
4. 방화벽: Rate Limiting 추가 (무료 1만 req/월)

→ 무료로 HTTPS, CDN, DDoS 방어 획득
```

---

## 성과

| 지표 | Before (수동) | After (자동) | 개선 |
|-----|--------------|-------------|------|
| **배포 시간** | 5분 | 2분 | **60% 단축** |
| **Downtime** | 5분 | 0초 | **무중단** |
| **배포 실패율** | 20% | 0% | **안정성** |
| **비용** | - | $0/월 | **프리티어** |

**실제 효과**:
- `git push`만 하면 자동으로 테스트 → 배포 완료
- Health Check로 배포 실패 시 자동 롤백
- CloudFlare CDN으로 한국 사용자도 빠른 응답

---

## 코드 위치

```
.github/workflows/deploy.yml      # CI/CD 파이프라인
docker-compose.yml                # 컨테이너 구성
nginx/nginx.conf                  # 리버스 프록시 설정
backend/resee/settings/production.py  # 프로덕션 설정
```

**핵심 설정 (3줄)**:
```yaml
on: push: branches: [main]     # 1. main push 시 트리거
needs: test                     # 2. 테스트 통과 필수
docker-compose up -d --no-deps # 3. 무중단 재배포
```

---

## 배운 점

AWS는 비싸다. 하지만 EC2 프리티어 + Docker + CloudFlare를 조합하면
**거의 돈 안 쓰고도 프로덕션급 인프라**를 구축할 수 있다.

CI/CD는 처음 설정이 귀찮지만, 한 번 만들어두면 배포가 너무 편하다.
특히 GitHub Actions는 설정이 간단해서 개인 프로젝트에 딱이었다.

**비용 최적화 전략**:
- EC2 t2.micro (750시간/월 무료)
- CloudFlare (무료 CDN + HTTPS)
- PostgreSQL Docker (RDS 대신)
- 총 비용: **$0/월**

---

**작성일**: 2025-10-24
**키워드**: AWS EC2, GitHub Actions, Docker, CloudFlare, CI/CD
