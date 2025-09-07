#!/bin/bash

# Resee 간단 배포 스크립트
# 사용법: ./deploy.sh

set -e

echo "🚀 Resee 배포 시작..."

# Docker Compose 명령 확인
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# .env.prod 파일 생성 (없으면)
if [ ! -f ".env.prod" ]; then
    echo "📝 .env.prod 파일 생성..."
    
    SECRET_KEY=$(openssl rand -base64 50 | tr -d "=+/" | cut -c1-50)
    DB_PASSWORD=$(openssl rand -base64 20 | tr -d "=+/" | cut -c1-16)
    
    cat > .env.prod << EOF
SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://resee_user:${DB_PASSWORD}@postgres:5432/resee_db
POSTGRES_DB=resee_db
POSTGRES_USER=resee_user
POSTGRES_PASSWORD=${DB_PASSWORD}
REDIS_URL=redis://redis:6379/0
ANTHROPIC_API_KEY=your_anthropic_api_key_here
REACT_APP_API_URL=http://localhost:8000/api
TIME_ZONE=Asia/Seoul
EOF
    
    echo "⚠️  ANTHROPIC_API_KEY를 .env.prod에서 수정하세요"
fi

# 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리..."
$COMPOSE_CMD -f docker-compose.prod.yml down || true

# 빌드 및 시작
echo "🔨 Docker 이미지 빌드..."
$COMPOSE_CMD -f docker-compose.prod.yml build

echo "🚀 서비스 시작..."
$COMPOSE_CMD -f docker-compose.prod.yml up -d

# 마이그레이션
echo "📊 DB 마이그레이션..."
sleep 10
$COMPOSE_CMD -f docker-compose.prod.yml exec -T backend python manage.py migrate

echo "📁 정적 파일 수집..."
$COMPOSE_CMD -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput

echo ""
echo "✅ 배포 완료!"
echo "📱 앱 접속: http://localhost:3000"
echo "🔧 관리자: http://localhost:8000/admin"
echo "👤 슈퍼유저 생성: $COMPOSE_CMD -f docker-compose.prod.yml exec backend python manage.py createsuperuser"