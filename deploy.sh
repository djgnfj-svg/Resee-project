#!/bin/bash

# Resee 간단 배포 스크립트  
# 사용법: ./deploy.sh [DOMAIN]
# 예시: ./deploy.sh mydomain.com

set -e

DOMAIN=${1:-localhost}
echo "🚀 Resee 배포 시작... (도메인: $DOMAIN)"

# Docker Compose 명령 확인
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# .env.prod 파일 생성 (없으면)
if [ ! -f ".env.prod" ]; then
    echo "📝 .env.prod 파일 생성..."
    echo ""
    
    # 대화형 입력
    echo "🔧 필수 설정 정보를 입력해주세요:"
    echo ""
    
    # 도메인 확인
    echo "🌐 현재 도메인: $DOMAIN"
    read -p "   다른 도메인 사용하시겠습니까? (현재 도메인 사용하려면 엔터): " INPUT_DOMAIN
    if [ ! -z "$INPUT_DOMAIN" ]; then
        DOMAIN=$INPUT_DOMAIN
        echo "   → 도메인 변경됨: $DOMAIN"
    fi
    echo ""
    
    # SECRET_KEY 입력
    read -p "🔑 SECRET_KEY 입력 (엔터시 자동생성): " INPUT_SECRET_KEY
    if [ ! -z "$INPUT_SECRET_KEY" ]; then
        SECRET_KEY=$INPUT_SECRET_KEY
    else
        SECRET_KEY=$(openssl rand -base64 50 | tr -d "=+/" | cut -c1-50)
        echo "   → 자동 생성됨: ${SECRET_KEY:0:20}..."
    fi
    echo ""
    
    # Google OAuth (선택사항)
    read -p "🔗 Google OAuth Client ID (선택사항, 엔터로 건너뛰기): " GOOGLE_CLIENT_ID
    echo ""
    
    # 랜덤 DB 패스워드 생성
    DB_PASSWORD=$(openssl rand -base64 20 | tr -d "=+/" | cut -c1-16)
    
    echo "🔐 생성된 보안 정보:"
    echo "   SECRET_KEY: ${SECRET_KEY:0:20}..."
    echo "   DB_PASSWORD: $DB_PASSWORD"
    echo ""
    
    cat > .env.prod << EOF
SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=${DOMAIN},localhost,127.0.0.1
DATABASE_URL=postgresql://resee_user:${DB_PASSWORD}@postgres:5432/resee_db
POSTGRES_DB=resee_db
POSTGRES_USER=resee_user
POSTGRES_PASSWORD=${DB_PASSWORD}
REDIS_URL=redis://redis:6379/0
ANTHROPIC_API_KEY=
REACT_APP_API_URL=http://${DOMAIN}/api
REACT_APP_GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
TIME_ZONE=Asia/Seoul
EOF
    
    echo "✅ .env.prod 파일이 생성되었습니다!"
    echo ""
else
    echo "📋 기존 .env.prod 파일을 사용합니다."
    echo ""
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
echo "📱 앱 접속: http://${DOMAIN}"
echo "🔧 관리자: http://${DOMAIN}/admin"
echo "👤 슈퍼유저 생성: $COMPOSE_CMD -f docker-compose.prod.yml exec backend python manage.py createsuperuser"