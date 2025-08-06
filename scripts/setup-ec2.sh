#!/bin/bash

# EC2 자동 배포 스크립트
# Ubuntu 22.04 LTS 기준

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 설정 변수
GITHUB_REPO=${1:-"https://github.com/djgnfj-svg/Resee.git"}
INSTALL_DIR="/opt/Resee"
DOMAIN=${2:-"localhost"}

echo -e "${BLUE}================================================"
echo -e "    🚀 Resee EC2 자동 배포 스크립트"
echo -e "================================================${NC}"
echo ""
echo -e "${GREEN}Repository: ${GITHUB_REPO}${NC}"
echo -e "${GREEN}Install Dir: ${INSTALL_DIR}${NC}"
echo -e "${GREEN}Domain: ${DOMAIN}${NC}"
echo ""

# 사용자 확인
read -p "계속 진행하시겠습니까? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}배포가 취소되었습니다.${NC}"
    exit 1
fi

# 1. 시스템 업데이트
echo -e "\n${YELLOW}[1/10] 시스템 업데이트 중...${NC}"
sudo apt update && sudo apt upgrade -y

# 2. 필수 패키지 설치
echo -e "\n${YELLOW}[2/10] 필수 패키지 설치 중...${NC}"
sudo apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    htop \
    tree \
    vim \
    net-tools

# 3. Docker 설치
echo -e "\n${YELLOW}[3/10] Docker 설치 중...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}✅ Docker 설치 완료${NC}"
else
    echo -e "${GREEN}✅ Docker 이미 설치됨${NC}"
fi

# 4. Docker Compose 설치
echo -e "\n${YELLOW}[4/10] Docker Compose 설치 중...${NC}"
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
    sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✅ Docker Compose ${DOCKER_COMPOSE_VERSION} 설치 완료${NC}"
else
    echo -e "${GREEN}✅ Docker Compose 이미 설치됨${NC}"
fi

# 5. 디렉토리 생성
echo -e "\n${YELLOW}[5/10] 디렉토리 구조 생성 중...${NC}"
sudo mkdir -p ${INSTALL_DIR} /var/log/resee /backups/postgresql
sudo chown -R $USER:$USER ${INSTALL_DIR} /var/log/resee /backups

# 6. Git 저장소 클론
echo -e "\n${YELLOW}[6/10] 소스코드 다운로드 중...${NC}"
if [ -d "${INSTALL_DIR}/.git" ]; then
    echo -e "${YELLOW}기존 저장소가 있습니다. 업데이트 중...${NC}"
    cd ${INSTALL_DIR}
    git pull origin main
else
    sudo rm -rf ${INSTALL_DIR}/*
    git clone ${GITHUB_REPO} ${INSTALL_DIR}
    cd ${INSTALL_DIR}
fi

# 7. 환경 변수 파일 생성
echo -e "\n${YELLOW}[7/10] 환경 변수 설정 중...${NC}"
if [ ! -f "${INSTALL_DIR}/.env" ]; then
    # .env.example 복사
    if [ -f "${INSTALL_DIR}/.env.example" ]; then
        cp ${INSTALL_DIR}/.env.example ${INSTALL_DIR}/.env
    else
        # 기본 .env 파일 생성
        cat > ${INSTALL_DIR}/.env << EOF
# Django 설정
SECRET_KEY=django-insecure-$(openssl rand -hex 32)
DEBUG=False
ALLOWED_HOSTS=${DOMAIN},localhost,127.0.0.1

# 데이터베이스
POSTGRES_DB=resee_db
POSTGRES_USER=resee_user
POSTGRES_PASSWORD=$(openssl rand -base64 32)
DATABASE_URL=postgresql://resee_user:$(openssl rand -base64 32)@db:5432/resee_db

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=amqp://resee:$(openssl rand -base64 32)@rabbitmq:5672//
CELERY_RESULT_BACKEND=redis://redis:6379/0

# RabbitMQ
RABBITMQ_DEFAULT_USER=resee
RABBITMQ_DEFAULT_PASS=$(openssl rand -base64 32)

# Frontend
REACT_APP_API_URL=http://${DOMAIN}:8000/api

# CORS
CORS_ALLOWED_ORIGINS=http://${DOMAIN}:3000,http://${DOMAIN}

# Email (임시 설정 - 실제 배포 시 변경 필요)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Google OAuth (실제 배포 시 설정 필요)
GOOGLE_OAUTH2_CLIENT_ID=your-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret
REACT_APP_GOOGLE_CLIENT_ID=your-client-id

# AI (선택사항)
ANTHROPIC_API_KEY=your-api-key
EOF
    fi
    echo -e "${GREEN}✅ 환경 변수 파일 생성 완료${NC}"
    echo -e "${YELLOW}⚠️  .env 파일을 확인하고 필요한 값을 수정하세요!${NC}"
fi

# 8. 실행 권한 부여
echo -e "\n${YELLOW}[8/10] 스크립트 실행 권한 설정 중...${NC}"
chmod +x ${INSTALL_DIR}/scripts/*.sh 2>/dev/null || true

# 9. Docker 환경 초기화
echo -e "\n${YELLOW}[9/10] Docker 환경 초기화 중...${NC}"
cd ${INSTALL_DIR}

# init-docker.sh 실행
if [ -f "${INSTALL_DIR}/scripts/init-docker.sh" ]; then
    bash ${INSTALL_DIR}/scripts/init-docker.sh
else
    # init-docker.sh가 없으면 수동 실행
    docker-compose down -v 2>/dev/null || true
    docker-compose build --no-cache
    docker-compose up -d db redis rabbitmq
    sleep 30
    docker-compose run --rm backend python manage.py migrate
    docker-compose run --rm backend python manage.py collectstatic --noinput
    docker-compose run --rm backend python manage.py create_test_users
    docker-compose up -d
fi

# 10. Systemd 서비스 등록
echo -e "\n${YELLOW}[10/10] Systemd 서비스 등록 중...${NC}"
sudo tee /etc/systemd/system/resee.service > /dev/null << EOF
[Unit]
Description=Resee Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${INSTALL_DIR}
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
ExecReload=/usr/local/bin/docker-compose restart
TimeoutStartSec=0
User=$USER

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable resee.service

# 완료 메시지
echo -e "\n${GREEN}================================================"
echo -e "    ✅ EC2 배포 완료!"
echo -e "================================================${NC}"
echo ""
echo -e "${GREEN}📝 설치 정보:${NC}"
echo -e "  - 설치 경로: ${INSTALL_DIR}"
echo -e "  - 로그 경로: /var/log/resee/"
echo -e "  - 백업 경로: /backups/"
echo ""
echo -e "${GREEN}🔗 접속 URL:${NC}"
echo -e "  - Frontend: http://${DOMAIN}:3000"
echo -e "  - Backend API: http://${DOMAIN}:8000/api/"
echo -e "  - Admin Panel: http://${DOMAIN}:8000/admin/"
echo ""
echo -e "${GREEN}📋 서비스 관리 명령어:${NC}"
echo -e "  - 시작: sudo systemctl start resee"
echo -e "  - 중지: sudo systemctl stop resee"
echo -e "  - 재시작: sudo systemctl restart resee"
echo -e "  - 상태 확인: sudo systemctl status resee"
echo -e "  - 로그 확인: cd ${INSTALL_DIR} && docker-compose logs -f"
echo ""
echo -e "${YELLOW}⚠️  주의사항:${NC}"
echo -e "  1. .env 파일에서 SECRET_KEY, 비밀번호 등을 변경하세요"
echo -e "  2. Google OAuth 설정을 완료하세요"
echo -e "  3. 프로덕션 환경에서는 DEBUG=False로 설정하세요"
echo -e "  4. AWS ALB 사용 시 ALLOWED_HOSTS에 ALB 도메인을 추가하세요"
echo ""
echo -e "${GREEN}🚀 배포가 완료되었습니다!${NC}"
echo -e "${YELLOW}Docker 그룹 적용을 위해 로그아웃 후 다시 로그인하세요.${NC}"