#!/bin/bash

# 🚀 Resee 프로덕션 서버 자동 설정 스크립트
# Ubuntu 20.04+ 지원

set -e  # 에러 발생 시 스크립트 중단

echo "🚀 Resee 프로덕션 서버 설정을 시작합니다..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 시스템 정보 확인
log_info "시스템 정보 확인 중..."
echo "OS: $(lsb_release -d | cut -f2)"
echo "Kernel: $(uname -r)"
echo "Architecture: $(uname -m)"
echo "Memory: $(free -h | awk '/^Mem:/ {print $2}')"
echo "Disk: $(df -h / | awk 'NR==2 {print $2}')"

# 루트 권한 확인
if [[ $EUID -eq 0 ]]; then
   log_error "이 스크립트를 root로 실행하지 마세요. sudo 권한이 있는 일반 사용자로 실행하세요."
   exit 1
fi

# sudo 권한 확인
if ! sudo -n true 2>/dev/null; then
    log_error "sudo 권한이 필요합니다."
    exit 1
fi

log_success "시스템 요구사항 확인 완료"

# 1. 시스템 업데이트
log_info "시스템 패키지 업데이트 중..."
sudo apt update && sudo apt upgrade -y
log_success "시스템 업데이트 완료"

# 2. 필수 패키지 설치
log_info "필수 패키지 설치 중..."
sudo apt install -y \
    curl \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    ufw \
    htop \
    tree \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

log_success "필수 패키지 설치 완료"

# 3. Docker 설치
log_info "Docker 설치 중..."
if ! command -v docker &> /dev/null; then
    # Docker GPG 키 추가
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Docker 저장소 추가
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Docker 설치
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io
    
    # 사용자를 docker 그룹에 추가
    sudo usermod -aG docker $USER
    
    log_success "Docker 설치 완료"
else
    log_warning "Docker가 이미 설치되어 있습니다."
fi

# 4. Docker Compose 설치
log_info "Docker Compose 설치 중..."
if ! command -v docker-compose &> /dev/null; then
    # 최신 버전 확인 및 설치
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    log_success "Docker Compose v${DOCKER_COMPOSE_VERSION} 설치 완료"
else
    log_warning "Docker Compose가 이미 설치되어 있습니다."
fi

# 5. 방화벽 설정
log_info "방화벽 설정 중..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw --force enable

log_success "방화벽 설정 완료 (SSH, HTTP, HTTPS 허용)"

# 6. 디렉토리 구조 생성
log_info "필요한 디렉토리 생성 중..."
sudo mkdir -p /opt/Resee
sudo mkdir -p /var/log/resee
sudo mkdir -p /backups/postgresql
sudo mkdir -p /backups/redis
sudo mkdir -p /backups/application

# 소유권 설정
sudo chown -R $USER:$USER /opt/Resee
sudo chown -R $USER:$USER /var/log/resee
sudo chown -R $USER:$USER /backups

log_success "디렉토리 구조 생성 완료"

# 7. 시스템 서비스 활성화
log_info "시스템 서비스 활성화 중..."
sudo systemctl enable nginx
sudo systemctl enable docker

log_success "시스템 서비스 활성화 완료"

# 8. 성능 최적화 설정
log_info "시스템 성능 최적화 설정 중..."

# 파일 디스크립터 제한 증가
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# 커널 파라미터 최적화
sudo tee -a /etc/sysctl.conf << EOF

# Resee 성능 최적화
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 8192
vm.swappiness = 10
vm.vfs_cache_pressure = 50
EOF

sudo sysctl -p

log_success "성능 최적화 설정 완료"

# 9. 로그 로테이션 설정
log_info "로그 로테이션 설정 중..."
sudo tee /etc/logrotate.d/resee << EOF
/var/log/resee/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 644 $USER $USER
    postrotate
        # Docker 컨테이너 로그 재시작 신호 (필요시)
        /usr/bin/docker-compose -f /opt/Resee/docker-compose.production.yml kill -s USR1 nginx 2>/dev/null || true
    endscript
}
EOF

log_success "로그 로테이션 설정 완료"

# 10. 시간대 설정
log_info "시간대 설정 중..."
sudo timedatectl set-timezone Asia/Seoul
log_success "시간대를 Asia/Seoul로 설정 완료"

# 11. 자동 업데이트 설정 (보안 패치만)
log_info "자동 보안 업데이트 설정 중..."
sudo apt install -y unattended-upgrades
echo 'Unattended-Upgrade::Automatic-Reboot "false";' | sudo tee -a /etc/apt/apt.conf.d/50unattended-upgrades

log_success "자동 보안 업데이트 설정 완료"

# 12. 상태 확인
log_info "설치된 구성요소 버전 확인..."
echo "Docker: $(docker --version)"
echo "Docker Compose: $(docker-compose --version)"
echo "Nginx: $(nginx -v 2>&1)"
echo "Certbot: $(certbot --version)"
echo "UFW: $(sudo ufw --version)"

# 13. 다음 단계 안내
echo ""
echo "🎉 서버 설정이 완료되었습니다!"
echo ""
echo "📋 다음 단계:"
echo "1. 터미널을 다시 시작하거나 다음 명령어 실행: newgrp docker"
echo "2. 소스 코드 다운로드: cd /opt && git clone <your-repo-url> Resee"
echo "3. 환경 변수 설정: cp .env.production.example .env.production && nano .env.production"
echo "4. SSL 인증서 발급: sudo certbot --nginx -d yourdomain.com"
echo "5. 애플리케이션 배포: docker-compose -f docker-compose.production.yml up -d"
echo ""
echo "📖 자세한 내용은 DEPLOYMENT_STEP_BY_STEP.md 파일을 참조하세요."
echo ""

# 14. 재부팅 필요 여부 확인
if [ -f /var/run/reboot-required ]; then
    log_warning "시스템 재부팅이 필요합니다. 다음 명령어를 실행하세요: sudo reboot"
fi

log_success "서버 설정 스크립트 실행 완료!"

# 그룹 변경 적용 (Docker 그룹)
echo ""
echo "💡 Docker 그룹 권한을 적용하기 위해 다음 중 하나를 선택하세요:"
echo "   1) 터미널 재시작"
echo "   2) 다음 명령어 실행: newgrp docker"
echo "   3) 시스템 재부팅 (권장)"