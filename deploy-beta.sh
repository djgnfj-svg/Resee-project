#!/bin/bash

# Resee 베타 배포 스크립트
# 작성자: Claude Code
# 버전: 1.0

set -e  # 에러 발생 시 스크립트 중단

echo "🚀 Resee 베타 배포를 시작합니다..."
echo "========================================"

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

# 환경 확인
check_prerequisites() {
    log_info "필수 요구사항을 확인합니다..."
    
    # Docker 확인
    if ! command -v docker &> /dev/null; then
        log_error "Docker가 설치되지 않았습니다."
        exit 1
    fi
    
    # Docker Compose 확인
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose가 설치되지 않았습니다."
        exit 1
    fi
    
    # .env.beta 파일 확인
    if [ ! -f ".env.beta" ]; then
        log_error ".env.beta 파일이 없습니다."
        log_info "다음 명령어로 템플릿을 복사하세요:"
        log_info "cp .env.example .env.beta"
        exit 1
    fi
    
    log_success "모든 필수 요구사항이 충족되었습니다."
}

# Git 상태 확인
check_git_status() {
    log_info "Git 상태를 확인합니다..."
    
    # 변경사항 확인
    if [ -n "$(git status --porcelain)" ]; then
        log_warning "커밋되지 않은 변경사항이 있습니다."
        read -p "계속 진행하시겠습니까? (y/N): " confirm
        if [[ ! $confirm =~ ^[Yy]$ ]]; then
            log_info "배포를 취소합니다."
            exit 0
        fi
    fi
    
    # 현재 브랜치 확인
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    log_info "현재 브랜치: $current_branch"
}

# 코드 품질 검사
run_quality_checks() {
    log_info "코드 품질 검사를 실행합니다..."
    
    # 백엔드 테스트
    log_info "백엔드 테스트 실행 중..."
    if docker-compose -f docker-compose.yml exec -T backend python -m pytest --tb=short; then
        log_success "백엔드 테스트 통과"
    else
        log_error "백엔드 테스트 실패"
        exit 1
    fi
    
    # 프론트엔드 테스트
    log_info "프론트엔드 테스트 실행 중..."
    if docker-compose -f docker-compose.yml exec -T frontend npm run test:ci; then
        log_success "프론트엔드 테스트 통과"
    else
        log_error "프론트엔드 테스트 실패"
        exit 1
    fi
    
    # 코드 형식 검사
    log_info "백엔드 코드 형식 검사 중..."
    docker-compose -f docker-compose.yml exec -T backend black . --check
    docker-compose -f docker-compose.yml exec -T backend flake8
    
    log_info "프론트엔드 코드 검사 중..."
    docker-compose -f docker-compose.yml exec -T frontend npm run lint
    docker-compose -f docker-compose.yml exec -T frontend npm run typecheck
    
    log_success "모든 코드 품질 검사 통과"
}

# 이미지 빌드
build_images() {
    log_info "Docker 이미지를 빌드합니다..."
    
    # 기존 컨테이너 정리
    log_info "기존 컨테이너를 정리합니다..."
    docker-compose -f docker-compose.yml down --remove-orphans
    
    # 이미지 빌드
    log_info "새 이미지를 빌드합니다..."
    docker-compose -f docker-compose.yml build --no-cache
    
    log_success "Docker 이미지 빌드 완료"
}

# 베타 환경 배포
deploy_beta() {
    log_info "베타 환경으로 배포합니다..."
    
    # 환경변수 파일 복사
    cp .env.beta .env
    
    # 서비스 시작
    log_info "서비스를 시작합니다..."
    docker-compose -f docker-compose.yml up -d
    
    # 데이터베이스 마이그레이션
    log_info "데이터베이스 마이그레이션을 실행합니다..."
    sleep 10  # 서비스 시작 대기
    docker-compose -f docker-compose.yml exec -T backend python manage.py migrate
    
    # 정적 파일 수집
    log_info "정적 파일을 수집합니다..."
    docker-compose -f docker-compose.yml exec -T backend python manage.py collectstatic --noinput
    
    log_success "베타 환경 배포 완료"
}

# 헬스체크
health_check() {
    log_info "서비스 헬스체크를 실행합니다..."
    
    # 서비스 상태 확인
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "헬스체크 시도 $attempt/$max_attempts..."
        
        # 백엔드 헬스체크
        if curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
            log_success "백엔드 서비스 정상"
            backend_healthy=true
        else
            backend_healthy=false
        fi
        
        # 프론트엔드 헬스체크
        if curl -f http://localhost:3000/ > /dev/null 2>&1; then
            log_success "프론트엔드 서비스 정상"
            frontend_healthy=true
        else
            frontend_healthy=false
        fi
        
        if [ "$backend_healthy" = true ] && [ "$frontend_healthy" = true ]; then
            log_success "모든 서비스가 정상적으로 실행되고 있습니다!"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "헬스체크 실패: 서비스가 정상적으로 시작되지 않았습니다."
            log_info "로그를 확인하세요: docker-compose logs"
            exit 1
        fi
        
        sleep 5
        ((attempt++))
    done
}

# 배포 정보 출력
show_deployment_info() {
    log_success "배포가 완료되었습니다!"
    echo
    echo "========================================"
    echo "🎉 Resee 베타 환경 배포 완료"
    echo "========================================"
    echo
    echo "📍 서비스 URL:"
    echo "   - 프론트엔드: http://localhost:3000"
    echo "   - 백엔드 API: http://localhost:8000"
    echo "   - 백엔드 Admin: http://localhost:8000/admin/"
    echo
    echo "🔧 관리 명령어:"
    echo "   - 로그 확인: docker-compose logs -f"
    echo "   - 서비스 중단: docker-compose down"
    echo "   - 서비스 재시작: docker-compose restart"
    echo
    echo "📊 모니터링:"
    echo "   - 시스템 상태: http://localhost:8000/health/"
    echo "   - 컨테이너 상태: docker-compose ps"
    echo
    echo "========================================"
}

# 롤백 함수
rollback() {
    log_warning "배포 중 오류가 발생했습니다. 롤백을 실행합니다..."
    docker-compose -f docker-compose.yml down
    log_info "롤백이 완료되었습니다."
    exit 1
}

# 메인 실행
main() {
    # 인터럽트 시그널 핸들러
    trap rollback INT TERM ERR
    
    log_info "베타 배포를 시작합니다..."
    
    # 1단계: 필수 요구사항 확인
    check_prerequisites
    
    # 2단계: Git 상태 확인
    check_git_status
    
    # 3단계: 코드 품질 검사 (선택적)
    if [[ "${SKIP_TESTS:-}" != "true" ]]; then
        read -p "코드 품질 검사를 실행하시겠습니까? (Y/n): " run_tests
        if [[ ! $run_tests =~ ^[Nn]$ ]]; then
            run_quality_checks
        fi
    fi
    
    # 4단계: 이미지 빌드
    build_images
    
    # 5단계: 베타 환경 배포
    deploy_beta
    
    # 6단계: 헬스체크
    health_check
    
    # 7단계: 배포 정보 출력
    show_deployment_info
    
    log_success "베타 배포가 성공적으로 완료되었습니다! 🎉"
}

# 스크립트 실행
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi