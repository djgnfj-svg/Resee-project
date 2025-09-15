#!/bin/bash

echo "🚀 Resee 서비스 부하 테스트 시작"
echo "=================================="

# 테스트 설정
HEALTH_URL="http://localhost:8000/api/health/"
FRONTEND_URL="http://localhost:3000/"
LOGIN_URL="http://localhost:8000/api/auth/token/"
API_URL="http://localhost:8000/api/content/contents/"

# 결과 저장 변수
total_requests=0
successful_requests=0
failed_requests=0
total_time=0

# 헬스체크 테스트 함수
test_health_check() {
    echo "1️⃣ 헬스체크 API 테스트 (20회 요청)"
    local count=0
    local success=0

    for i in {1..20}; do
        start_time=$(date +%s.%N)
        response=$(curl -s -o /dev/null -w "%{http_code}:%{time_total}" $HEALTH_URL)
        end_time=$(date +%s.%N)

        http_code=$(echo $response | cut -d: -f1)
        response_time=$(echo $response | cut -d: -f2)

        count=$((count + 1))
        if [ "$http_code" = "200" ]; then
            success=$((success + 1))
        fi

        printf "Request $i: HTTP $http_code, ${response_time}s\n"
        sleep 0.1  # 0.1초 간격
    done

    echo "헬스체크 결과: $success/$count 성공"
    echo ""
}

# 프론트엔드 테스트 함수
test_frontend() {
    echo "2️⃣ 프론트엔드 페이지 테스트 (10회 요청)"
    local count=0
    local success=0

    for i in {1..10}; do
        response=$(curl -s -o /dev/null -w "%{http_code}:%{time_total}" $FRONTEND_URL)
        http_code=$(echo $response | cut -d: -f1)
        response_time=$(echo $response | cut -d: -f2)

        count=$((count + 1))
        if [ "$http_code" = "200" ]; then
            success=$((success + 1))
        fi

        printf "Request $i: HTTP $http_code, ${response_time}s\n"
        sleep 0.2  # 0.2초 간격
    done

    echo "프론트엔드 결과: $success/$count 성공"
    echo ""
}

# 로그인 API 테스트 함수
test_login_api() {
    echo "3️⃣ 로그인 API 테스트 (5회 요청)"
    local count=0
    local success=0

    for i in {1..5}; do
        response=$(curl -s -o /dev/null -w "%{http_code}:%{time_total}" \
            -X POST \
            -H "Content-Type: application/json" \
            -d '{"email":"test@example.com","password":"testpassword123"}' \
            $LOGIN_URL)

        http_code=$(echo $response | cut -d: -f1)
        response_time=$(echo $response | cut -d: -f2)

        count=$((count + 1))
        if [ "$http_code" = "200" ]; then
            success=$((success + 1))
        fi

        printf "Request $i: HTTP $http_code, ${response_time}s\n"
        sleep 0.3  # 0.3초 간격
    done

    echo "로그인 API 결과: $success/$count 성공"
    echo ""
}

# 동시 요청 테스트
test_concurrent_requests() {
    echo "4️⃣ 동시 요청 테스트 (5개 프로세스로 헬스체크)"
    local pids=()

    # 5개의 백그라운드 프로세스로 동시 요청
    for i in {1..5}; do
        (
            for j in {1..3}; do
                curl -s -o /dev/null -w "Process $i, Request $j: %{http_code}, %{time_total}s\n" $HEALTH_URL
                sleep 0.1
            done
        ) &
        pids+=($!)
    done

    # 모든 백그라운드 프로세스 완료 대기
    for pid in "${pids[@]}"; do
        wait $pid
    done

    echo "동시 요청 테스트 완료"
    echo ""
}

# 메인 실행
main() {
    test_health_check
    test_frontend
    test_login_api
    test_concurrent_requests

    echo "🎉 부하 테스트 완료!"
    echo "=================================="
    echo "💡 결과 해석:"
    echo "- HTTP 200: 성공"
    echo "- 응답시간 < 0.1초: 매우 빠름"
    echo "- 응답시간 < 0.5초: 양호"
    echo "- 응답시간 > 1초: 느림 (최적화 필요)"
    echo ""
    echo "🔍 Docker 컨테이너 리소스 사용량:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
}

main