#!/bin/bash

# Resee 프로덕션 배포 스크립트
# 사용법: ./deploy.sh

set -e

echo "🚀 Resee 프로덕션 배포를 시작합니다..."

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "📋 $1"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Docker Compose 명령 확인
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# .env.prod 파일 확인
if [ ! -f ".env.prod" ]; then
    log_error ".env.prod 파일이 존재하지 않습니다!"
    echo "다음 중 하나를 수행해주세요:"
    echo "1. .env.example을 복사: cp .env.example .env.prod"
    echo "2. 기존 .env.prod 파일을 프로젝트 루트로 복사"
    exit 1
fi

log_success ".env.prod 파일을 찾았습니다."

# Swap 메모리 확인 및 추가
log_info "메모리 상태를 확인합니다..."
total_mem=$(free -m | awk 'NR==2{print $2}')
swap_mem=$(free -m | awk 'NR==3{print $2}')

if [ "$total_mem" -lt 4000 ] && [ "$swap_mem" -lt 2000 ]; then
    log_warning "메모리가 부족합니다. Swap 메모리를 추가합니다..."
    
    # 4GB Swap 파일 생성
    sudo fallocate -l 4G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1024 count=4194304
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    
    # 영구 설정 (중복 방지)
    if ! grep -q '/swapfile' /etc/fstab; then
        echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    fi
    
    log_success "Swap 메모리 4GB 추가 완료"
    free -h
else
    log_success "메모리가 충분합니다."
fi

# 환경변수 파일 처리 (핵심!)
log_info ".env.prod를 .env로 복사합니다..."
cp .env.prod .env
log_success "환경변수 설정 완료"

# 기존 컨테이너 정리
log_info "기존 컨테이너 정리 중..."
$COMPOSE_CMD -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true

# 이미지 빌드 및 컨테이너 시작
log_info "Docker 이미지 빌드 및 컨테이너 시작... (5-10분 소요)"
if $COMPOSE_CMD -f docker-compose.prod.yml up -d --build; then
    log_success "컨테이너 시작 완료"
else
    log_error "컨테이너 시작 실패"
    exit 1
fi

# 백엔드 서비스 대기
log_info "백엔드 서비스 시작 대기 중..."
sleep 15

# 헬스체크
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if $COMPOSE_CMD -f docker-compose.prod.yml exec -T backend curl -f http://localhost:8000/api/health/ &>/dev/null; then
        log_success "백엔드 서비스 정상 시작"
        break
    fi
    attempt=$((attempt + 1))
    echo -n "."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    log_error "백엔드 서비스 시작 실패"
    echo "로그 확인:"
    $COMPOSE_CMD -f docker-compose.prod.yml logs backend --tail=20
    exit 1
fi

# 데이터베이스 마이그레이션
log_info "데이터베이스 마이그레이션 실행 중..."
if $COMPOSE_CMD -f docker-compose.prod.yml exec -T backend python manage.py migrate; then
    log_success "데이터베이스 마이그레이션 완료"
else
    log_error "데이터베이스 마이그레이션 실패"
    exit 1
fi

# 정적 파일 수집
log_info "정적 파일 수집 중..."
if $COMPOSE_CMD -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput; then
    log_success "정적 파일 수집 완료"
else
    log_warning "정적 파일 수집 실패했지만 계속 진행"
fi

# 최종 상태 확인
echo ""
echo "=== 🎉 배포 완료! ==="
echo ""
echo "📋 컨테이너 상태:"
$COMPOSE_CMD -f docker-compose.prod.yml ps
echo ""
echo "🌐 접속 정보:"
echo "  메인 사이트: http://reseeall.com"
echo "  API 상태: http://reseeall.com/api/health/"
echo "  관리자: http://reseeall.com/admin/"
echo ""
echo "🔧 관리 명령어:"
echo "  로그 확인: $COMPOSE_CMD -f docker-compose.prod.yml logs -f"
echo "  재시작: $COMPOSE_CMD -f docker-compose.prod.yml restart"
echo "  중지: $COMPOSE_CMD -f docker-compose.prod.yml down"
echo ""

# 슈퍼유저 생성 옵션
read -p "관리자 계정을 지금 생성하시겠습니까? (y/N): " create_admin
if [[ $create_admin =~ ^[Yy]$ ]]; then
    log_info "관리자 계정 생성 중..."
    $COMPOSE_CMD -f docker-compose.prod.yml exec backend python manage.py createsuperuser
fi

log_success "배포가 성공적으로 완료되었습니다! 🚀"