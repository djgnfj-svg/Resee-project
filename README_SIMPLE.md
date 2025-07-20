# Resee - 간단 배포 가이드

과학적 복습 플랫폼 Resee입니다.

## 🚀 빠른 시작

```bash
# 시작
./start.sh

# 중지
docker-compose down
```

## 📱 접속 주소

- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000/api
- **RabbitMQ 관리**: http://localhost:15672 (resee/resee_password)

## 📋 필요사항

- Docker
- Docker Compose

## 🔧 주요 명령어

```bash
# 시작
./start.sh

# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f frontend
docker-compose logs -f backend

# 중지
docker-compose down

# 완전 정리 (데이터 포함)
docker-compose down -v
```

## 🗂️ 서비스 구성

- **Frontend**: React (포트 3000)
- **Backend**: Django (포트 8000)
- **Database**: PostgreSQL (포트 5432)
- **Cache**: Redis (포트 6379)
- **Queue**: RabbitMQ (포트 5672, 관리 15672)
- **Worker**: Celery

## 💡 트러블슈팅

### 서비스가 시작되지 않을 때
```bash
docker-compose down -v
./start.sh
```

### 포트 충돌 시
다른 서비스들을 중지하고 다시 시작하세요.

### 데이터베이스 문제 시
```bash
docker-compose down -v  # 데이터 초기화
./start.sh
```

끝!