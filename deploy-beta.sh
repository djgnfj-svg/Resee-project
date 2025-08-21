#!/bin/bash

# ====================================
# Resee Beta 배포 스크립트
# ====================================

set -e  # 에러 발생시 스크립트 중단

echo "🚀 Resee Beta 배포를 시작합니다..."

# 1. 환경변수 파일 확인
if [ ! -f ".env.beta" ]; then
    echo "❌ .env.beta 파일이 없습니다!"
    echo "💡 .env.beta.example을 참고하여 .env.beta 파일을 생성하세요."
    exit 1
fi

# 2. Docker와 Docker Compose 확인
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되어 있지 않습니다!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose가 설치되어 있지 않습니다!"
    exit 1
fi

# 3. 환경변수 로드
echo "🔧 환경변수를 로드합니다..."
export $(cat .env.beta | grep -v '^#' | xargs)

# 4. 필수 환경변수 확인
required_vars=("DATABASE_URL" "SECRET_KEY" "ALLOWED_HOSTS" "ANTHROPIC_API_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ 필수 환경변수 $var가 설정되지 않았습니다!"
        exit 1
    fi
done

# 5. 이전 컨테이너 정리
echo "🧹 이전 컨테이너를 정리합니다..."
docker-compose -f docker-compose.beta.yml down --remove-orphans

# 6. 이미지 빌드
echo "🔨 Docker 이미지를 빌드합니다..."
docker-compose -f docker-compose.beta.yml build --no-cache

# 7. 데이터베이스 연결 테스트 (Docker 컨테이너 사용)
echo "📊 데이터베이스 연결을 테스트합니다..."
if ! docker run --rm -e DATABASE_URL="$DATABASE_URL" python:3.11-slim bash -c "
pip install psycopg2-binary >/dev/null 2>&1 && python -c '
import psycopg2
from urllib.parse import urlparse
url = urlparse(\"$DATABASE_URL\")
conn = psycopg2.connect(
    host=url.hostname,
    port=url.port,
    user=url.username,
    password=url.password,
    database=url.path[1:]
)
conn.close()
print(\"✅ 데이터베이스 연결 성공!\")
'" 2>/dev/null; then
    echo "❌ 데이터베이스 연결에 실패했습니다!"
    echo "💡 DATABASE_URL을 확인하고 RDS 보안그룹에서 접근을 허용했는지 확인하세요."
    echo "💡 또는 --skip-db-test 옵션을 사용하여 DB 테스트를 건너뛸 수 있습니다."
    if [[ "$1" != "--skip-db-test" ]]; then
        exit 1
    fi
fi

# 8. 컨테이너 시작
echo "🚀 컨테이너를 시작합니다..."
docker-compose -f docker-compose.beta.yml up -d

# 9. 헬스체크
echo "🏥 서비스 상태를 확인합니다..."
sleep 30

# 백엔드 헬스체크
if curl -f http://localhost/api/health/ >/dev/null 2>&1; then
    echo "✅ 백엔드가 정상적으로 실행중입니다!"
else
    echo "❌ 백엔드 헬스체크 실패!"
    echo "📋 로그를 확인하세요:"
    docker-compose -f docker-compose.beta.yml logs backend
    exit 1
fi

# 프론트엔드 헬스체크
if curl -f http://localhost/ >/dev/null 2>&1; then
    echo "✅ 프론트엔드가 정상적으로 실행중입니다!"
else
    echo "❌ 프론트엔드 헬스체크 실패!"
    echo "📋 로그를 확인하세요:"
    docker-compose -f docker-compose.beta.yml logs frontend
    exit 1
fi

# 10. 배포 완료
echo ""
echo "🎉 Beta 배포가 완료되었습니다!"
echo ""
echo "📋 서비스 정보:"
echo "   🌐 웹사이트: http://$(echo $ALLOWED_HOSTS | cut -d',' -f1)"
echo "   🔧 관리자: http://$(echo $ALLOWED_HOSTS | cut -d',' -f1)/admin/"
echo "   📊 API: http://$(echo $ALLOWED_HOSTS | cut -d',' -f1)/api/"
echo ""
echo "📊 모니터링 명령어:"
echo "   docker-compose -f docker-compose.beta.yml ps"
echo "   docker-compose -f docker-compose.beta.yml logs -f"
echo ""
echo "🛑 중단 명령어:"
echo "   docker-compose -f docker-compose.beta.yml down"
echo ""

# 11. 사용자 생성 안내
echo "👤 첫 관리자 계정을 생성하려면:"
echo "   docker-compose -f docker-compose.beta.yml exec backend python manage.py createsuperuser"
echo ""

echo "✨ 배포가 성공적으로 완료되었습니다!"