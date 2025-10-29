# 핵심 기술 상세 설명

## 1. CI/CD 파이프라인 (GitHub Actions)

### 배포 자동화 흐름

```
개발자 코드 푸시 (git push)
    ↓
GitHub Actions Workflow 트리거
    ↓
SSH로 EC2 접속
    ↓
git pull (최신 코드)
    ↓
deploy.sh 실행
    ↓
Docker Compose 재시작
    ↓
성공/실패 알림
```

### GitHub Actions Workflow

`.github/workflows/deploy.yml`:

```yaml
name: Deploy to EC2

on:
  push:
    branches:
      - main
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
          script: |
            cd ${{ secrets.PROJECT_PATH }}
            git pull origin main
            ./deploy.sh
```

**주요 기능**:
- `main` 브랜치 푸시 시 자동 배포
- 수동 실행 가능 (`workflow_dispatch`)
- SSH로 EC2 접속하여 배포 스크립트 실행

### deploy.sh 스크립트

```bash
#!/bin/bash
set -e

git pull origin main

if [ "$ENV" = "production" ]; then
    docker-compose -f docker-compose.prod.yml down
    docker-compose -f docker-compose.prod.yml build --no-cache
    docker-compose -f docker-compose.prod.yml up -d
else
    docker-compose down
    docker-compose build
    docker-compose up -d
fi

docker-compose exec -T backend python manage.py migrate
docker-compose exec -T backend python manage.py collectstatic --noinput

sleep 10
curl -f http://localhost/api/health/ || exit 1

echo "배포 완료!"
```

---

## 2. Cloudflare SSL/TLS

### 비용 절감

**AWS ALB 대신 Cloudflare 무료 플랜 사용**:
- ALB: $16.20/월
- Cloudflare: $0/월
- **월 $16 절약**

**제공 기능**:
- SSL/TLS 자동 인증서 발급 및 갱신
- DNS 관리
- CDN
- DDoS 방어

---

## 3. Docker Compose 구성

### 서비스 구조

```
docker-compose.yml
├── nginx         (포트 80)
├── backend       (Django + Gunicorn)
├── frontend      (React 빌드)
├── postgres      (PostgreSQL 15)
├── redis         (Redis 7)
├── celery        (백그라운드 작업)
└── celery-beat   (스케줄러)
```

### 핵심 서비스 설정

**Nginx**:
- 리버스 프록시 (Django, React 라우팅)
- 정적 파일 서빙
- Rate Limiting

```nginx
location /api/ {
    proxy_pass http://backend:8000;
}

location / {
    root /usr/share/nginx/html;
    try_files $uri /index.html;
}
```

**Django (Gunicorn)**:
```bash
gunicorn resee.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --threads 2 \
  --max-requests 1000 \
  --preload
```

- 2 Workers, 2 Threads: 동시 처리 능력 (t3.medium 4GB RAM)
- max-requests: Worker 재시작으로 메모리 누수 방지
- preload: 앱 사전 로드로 메모리 절약

**PostgreSQL**:
```yaml
postgres:
  image: postgres:15-alpine
  volumes:
    - postgres_data:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
```

- Named Volume으로 데이터 영속성
- Celery Beat으로 매일 S3 백업

**Redis**:
```yaml
redis:
  image: redis:7-alpine
  volumes:
    - redis_data:/data
```

용도:
- Celery 메시지 브로커
- Django Rate Limiting 캐시
- 세션 저장

**Celery**:
```yaml
celery:
  command: celery -A resee worker -l info

celery-beat:
  command: celery -A resee beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

처리 작업:
- 이메일 발송 (리뷰 알림)
- AI API 호출 (콘텐츠 검증, 답변 평가)
- DB 백업 (매일 새벽 3시)

### 네트워크 및 볼륨

**네트워크**:
- 모든 컨테이너가 같은 네트워크
- 서비스 이름으로 DNS 해석 (`backend:8000`, `postgres:5432`)

**볼륨**:
```yaml
volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

### 운영 명령어

```bash
# 시작/중지
docker-compose up -d
docker-compose down
docker-compose restart backend

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f celery

# 마이그레이션
docker-compose exec backend python manage.py migrate

# 백업
docker-compose exec postgres pg_dump -U postgres resee_prod > backup.sql
```

---

## 전체 플로우

### 사용자 요청

```
사용자 → Cloudflare (SSL) → EC2 → Nginx → Django → PostgreSQL/Redis
```

### 배포

```
git push → GitHub Actions → SSH → deploy.sh → Docker Compose 재시작 → Slack 알림
```

### 백그라운드 작업

```
Celery Beat → Redis → Celery Worker → 이메일/AI/백업 → PostgreSQL
```
