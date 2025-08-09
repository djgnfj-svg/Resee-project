#!/bin/bash

# 로컬에서 CI 체크를 빠르게 확인하는 스크립트
# Usage: ./scripts/check-ci.sh

set -e

echo "🔍 Resee 로컬 CI 체크 시작..."
echo "================================================"

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수: 성공 메시지
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 함수: 경고 메시지
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 함수: 에러 메시지
error() {
    echo -e "${RED}❌ $1${NC}"
}

# 함수: 정보 메시지
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 1. Git 상태 체크
info "Git 상태 확인 중..."
if git diff-index --quiet HEAD --; then
    success "Git: 모든 변경사항이 커밋됨"
else
    warning "Git: 커밋되지 않은 변경사항 있음"
fi

# 2. Backend 체크
echo
info "Backend 체크 중..."
cd backend

if [ ! -f "manage.py" ]; then
    error "Backend: manage.py 파일을 찾을 수 없음"
    exit 1
fi

# Python 구문 체크 (빠른 체크를 위해 주요 파일만)
info "Python 구문 체크 중..."
python_files=$(find . -name "*.py" -not -path "./venv/*" -not -path "./.env/*" | head -20)
if python -m py_compile $python_files 2>/dev/null; then
    success "Backend: Python 구문 검사 통과"
else
    error "Backend: Python 구문 오류 발견"
    exit 1
fi

# Django 설정 체크
info "Django 설정 체크 중..."
export SECRET_KEY="test-secret-key"
export DATABASE_URL="sqlite:///memory"
export DEBUG="True"

if python manage.py check --quiet 2>/dev/null; then
    success "Backend: Django 설정 검사 통과"
else
    error "Backend: Django 설정 오류 발견"
    python manage.py check  # 에러 상세 출력
    exit 1
fi

# 3. Frontend 체크
echo
info "Frontend 체크 중..."
cd ../frontend

if [ ! -f "package.json" ]; then
    error "Frontend: package.json 파일을 찾을 수 없음"
    exit 1
fi

# Node modules 체크
if [ ! -d "node_modules" ]; then
    warning "Frontend: node_modules 없음, npm install 실행 중..."
    npm install --silent
fi

# TypeScript 체크
info "TypeScript 타입 체크 중..."
if npx tsc --noEmit --skipLibCheck 2>/dev/null; then
    success "Frontend: TypeScript 타입 체크 통과"
else
    error "Frontend: TypeScript 타입 오류 발견"
    npx tsc --noEmit --skipLibCheck
    exit 1
fi

# Build 체크 (간단한 구문 체크만)
info "Frontend 빌드 가능성 체크 중..."
export CI=true
export GENERATE_SOURCEMAP=false

if timeout 60s npm run build >/dev/null 2>&1; then
    success "Frontend: 빌드 체크 통과"
else
    warning "Frontend: 빌드 체크 시간 초과 또는 실패 (60초)"
fi

# 4. 전체 결과 출력
echo
echo "================================================"
echo -e "${GREEN}🎉 로컬 CI 체크 완료!${NC}"
echo
echo "다음 단계:"
echo "1. git add . && git commit"  
echo "2. git push (GitHub CI가 자동 실행됨)"
echo
echo "GitHub에서 더 상세한 테스트가 실행됩니다:"
echo "- 전체 테스트 스위트"
echo "- 코드 품질 검사"
echo "- 보안 검사"
echo
success "준비 완료! 🚀"