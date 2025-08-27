#!/bin/bash

# ================================
# Resee v0.1.0 EC2 간단 배포
# ================================

echo "🚀 Resee EC2 배포 시작"

# 환경변수 확인
if [ ! -f ".env" ]; then
    echo "❌ .env 파일이 없습니다"
    echo "cp .env.example .env 후 실제 값 입력하세요"
    exit 1
fi

# Docker 확인
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되지 않았습니다"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose가 설치되지 않았습니다"
    exit 1
fi

# 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리..."
docker-compose down

# 최신 코드로 빌드 및 실행
echo "🏗️  서비스 빌드 및 실행..."
docker-compose up --build -d

# 헬스체크
echo "🔍 서비스 상태 확인..."
sleep 10

if curl -f http://localhost:8000/api/health/ > /dev/null 2>&1; then
    echo "✅ 백엔드 정상 동작"
else
    echo "❌ 백엔드 오류 발생"
    docker-compose logs backend
    exit 1
fi

if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 프론트엔드 정상 동작"
else
    echo "❌ 프론트엔드 오류 발생"
    docker-compose logs frontend
    exit 1
fi

echo ""
echo "🎉 배포 완료!"
echo "================================"
echo "🌐 웹사이트: http://your-server-ip:3000"
echo "🔧 API: http://your-server-ip:8000"
echo "👨‍💼 관리자: http://your-server-ip:8000/admin"
echo ""
echo "📋 유용한 명령어:"
echo "docker-compose logs -f        # 로그 확인"
echo "docker-compose ps             # 서비스 상태"
echo "docker-compose restart        # 재시작"
echo "docker-compose down           # 정지"