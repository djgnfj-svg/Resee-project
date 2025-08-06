#!/bin/bash

# 색상 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Resee Docker 환경 초기화 시작${NC}"
echo "=================================="

# 1. 기존 컨테이너 및 볼륨 정리
echo -e "\n${YELLOW}1. 기존 Docker 환경 정리 중...${NC}"
docker-compose down -v 2>/dev/null || true
docker system prune -f --volumes

# 2. 환경 변수 파일 확인
echo -e "\n${YELLOW}2. 환경 변수 파일 확인...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}.env 파일이 없습니다. .env.example에서 복사합니다...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env 파일 생성 완료${NC}"
fi

# 3. Docker 이미지 빌드
echo -e "\n${YELLOW}3. Docker 이미지 빌드 중... (5-10분 소요)${NC}"
docker-compose build --no-cache

# 4. 데이터베이스 서비스 먼저 시작
echo -e "\n${YELLOW}4. 데이터베이스 서비스 시작 중...${NC}"
docker-compose up -d db redis rabbitmq

# 데이터베이스 준비 대기
echo -e "${YELLOW}데이터베이스 초기화 대기 중 (30초)...${NC}"
sleep 30

# 5. 데이터베이스 마이그레이션
echo -e "\n${YELLOW}5. 데이터베이스 마이그레이션 실행 중...${NC}"
docker-compose run --rm backend python manage.py migrate

# 6. 정적 파일 수집
echo -e "\n${YELLOW}6. 정적 파일 수집 중...${NC}"
docker-compose run --rm backend python manage.py collectstatic --noinput

# 7. 테스트 사용자 생성
echo -e "\n${YELLOW}7. 테스트 사용자 생성 중...${NC}"
docker-compose run --rm backend python manage.py create_test_users

# 8. 모든 서비스 시작
echo -e "\n${YELLOW}8. 모든 서비스 시작 중...${NC}"
docker-compose up -d

# 9. 서비스 상태 확인
echo -e "\n${YELLOW}9. 서비스 상태 확인...${NC}"
sleep 10
docker-compose ps

# 10. 헬스체크
echo -e "\n${YELLOW}10. 헬스체크 실행 중...${NC}"
sleep 5

# Backend 헬스체크
if curl -f http://localhost:8000/api/health/ 2>/dev/null; then
    echo -e "${GREEN}✅ Backend 정상 작동${NC}"
else
    echo -e "${RED}❌ Backend 응답 없음${NC}"
fi

# Frontend 헬스체크
if curl -f http://localhost:3000 2>/dev/null | grep -q "Resee"; then
    echo -e "${GREEN}✅ Frontend 정상 작동${NC}"
else
    echo -e "${RED}❌ Frontend 응답 없음${NC}"
fi

echo -e "\n${GREEN}=================================="
echo -e "🎉 Docker 환경 초기화 완료!"
echo -e "==================================${NC}"
echo ""
echo -e "${GREEN}📝 테스트 계정 정보:${NC}"
echo "  - admin@resee.com / admin123! (관리자)"
echo "  - test@resee.com / test123! (일반 사용자)"
echo "  - demo@resee.com / demo123! (데모 사용자)"
echo ""
echo -e "${GREEN}🔗 접속 URL:${NC}"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000/api/"
echo "  - Admin Panel: http://localhost:8000/admin/"
echo ""
echo -e "${GREEN}📋 유용한 명령어:${NC}"
echo "  - 로그 확인: docker-compose logs -f [서비스명]"
echo "  - 쉘 접속: docker-compose exec [서비스명] bash"
echo "  - 재시작: docker-compose restart [서비스명]"
echo "  - 중지: docker-compose down"
echo ""