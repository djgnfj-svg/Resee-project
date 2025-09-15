#!/bin/bash

echo "🚀 백엔드 API 부하 테스트"
echo "=========================="

# API 엔드포인트들
BASE_URL="http://localhost:8000/api"
HEALTH_URL="$BASE_URL/health/"
LOGIN_URL="$BASE_URL/auth/token/"
REGISTER_URL="$BASE_URL/auth/register/"
CONTENT_URL="$BASE_URL/content/contents/"
CATEGORY_URL="$BASE_URL/content/categories/"

# 테스트 설정
CONCURRENT_USERS=15
REQUESTS_PER_USER=5
TOTAL_REQUESTS=$((CONCURRENT_USERS * REQUESTS_PER_USER))

echo "📊 테스트 설정:"
echo "- 동시 사용자: $CONCURRENT_USERS명"
echo "- 사용자당 요청: $REQUESTS_PER_USER회"
echo "- 총 요청 수: $TOTAL_REQUESTS회"
echo ""

# 결과 파일
RESULTS_FILE="/tmp/backend_load_results.txt"
> $RESULTS_FILE

# 개별 API 테스트 함수
test_api_endpoint() {
    local api_name=$1
    local url=$2
    local method=$3
    local data=$4
    local user_num=$5
    local req_num=$6

    local curl_cmd="curl -s -w \"HTTPCODE:%{http_code}:TIME:%{time_total}\" -X $method"

    if [ "$data" != "NONE" ]; then
        curl_cmd="$curl_cmd -H \"Content-Type: application/json\" -d '$data'"
    fi

    curl_cmd="$curl_cmd $url"

    local response=$(eval $curl_cmd)
    local http_code=$(echo $response | grep -o "HTTPCODE:[0-9]*" | cut -d: -f2)
    local response_time=$(echo $response | grep -o "TIME:[0-9.]*" | cut -d: -f2)

    echo "User$user_num,Req$req_num,$api_name,$http_code,$response_time" >> $RESULTS_FILE
}

# 부하 테스트 실행
run_load_test() {
    local api_name=$1
    local url=$2
    local method=$3
    local data=$4

    echo "🔥 $api_name API 부하 테스트 시작..."
    local start_time=$(date +%s)

    local pids=()
    for user in $(seq 1 $CONCURRENT_USERS); do
        (
            for req in $(seq 1 $REQUESTS_PER_USER); do
                test_api_endpoint "$api_name" "$url" "$method" "$data" "$user" "$req"
                sleep 0.$(shuf -i 1-3 -n 1)  # 랜덤 지연
            done
        ) &
        pids+=($!)
    done

    # 모든 프로세스 완료 대기
    for pid in "${pids[@]}"; do
        wait $pid
    done

    local end_time=$(date +%s)
    local total_time=$((end_time - start_time))

    # 결과 분석
    local total_calls=$(grep ",$api_name," $RESULTS_FILE | wc -l)
    local successful_calls=$(grep ",$api_name,200," $RESULTS_FILE | wc -l)
    local failed_calls=$((total_calls - successful_calls))
    local success_rate=$((successful_calls * 100 / total_calls))
    local avg_time=$(grep ",$api_name,200," $RESULTS_FILE | cut -d, -f5 | awk '{sum+=$1} END {if(NR>0) print sum/NR; else print 0}')
    local rps=$((total_calls / total_time))

    echo ""
    echo "📈 $api_name API 결과:"
    echo "  - 총 요청: $total_calls회"
    echo "  - 성공: $successful_calls회"
    echo "  - 실패: $failed_calls회"
    echo "  - 성공률: $success_rate%"
    echo "  - 평균 응답시간: ${avg_time}초"
    echo "  - 초당 요청수: ${rps} req/s"
    echo "  - 소요 시간: ${total_time}초"

    # 성능 평가
    if [ $success_rate -ge 95 ]; then
        echo "  - 평가: ✅ 우수"
    elif [ $success_rate -ge 90 ]; then
        echo "  - 평가: ⚠️ 양호"
    else
        echo "  - 평가: ❌ 개선 필요"
    fi
    echo ""
}

# 메인 실행
main() {
    echo "🚀 백엔드 부하 테스트 시작..."
    echo ""

    # 1. 헬스체크 API
    run_load_test "HEALTH" "$HEALTH_URL" "GET" "NONE"

    # 2. 회원가입 API (가벼운 부하 - 실제로는 DB에 영향)
    echo "⚠️ 회원가입 API는 실제 데이터 생성으로 인해 스킵합니다."
    echo ""

    # 3. 로그인 API
    run_load_test "LOGIN" "$LOGIN_URL" "POST" '{"email":"test@example.com","password":"testpassword123"}'

    # 4. 컨텐츠 목록 API (인증 없이)
    run_load_test "CONTENT_UNAUTH" "$CONTENT_URL" "GET" "NONE"

    # 5. 카테고리 목록 API (인증 없이)
    run_load_test "CATEGORY_UNAUTH" "$CATEGORY_URL" "GET" "NONE"

    echo "🎉 백엔드 부하 테스트 완료!"
    echo ""

    # 전체 요약
    local total_requests=$(wc -l < $RESULTS_FILE)
    local total_successful=$(grep ",200," $RESULTS_FILE | wc -l)
    local overall_success_rate=$((total_successful * 100 / total_requests))

    echo "📊 === 전체 결과 요약 ==="
    echo "🔢 총 API 호출: $total_requests회"
    echo "✅ 총 성공: $total_successful회"
    echo "❌ 총 실패: $((total_requests - total_successful))회"
    echo "📈 전체 성공률: $overall_success_rate%"
    echo ""

    echo "🔍 Docker 리소스 사용량:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep resee-project
    echo ""

    # 응답시간 분포
    echo "⏱️ API별 응답시간 분포:"
    for api in HEALTH LOGIN CONTENT_UNAUTH CATEGORY_UNAUTH; do
        local times=$(grep ",$api,200," $RESULTS_FILE 2>/dev/null | cut -d, -f5)
        if [ ! -z "$times" ]; then
            local min_time=$(echo "$times" | sort -n | head -1)
            local max_time=$(echo "$times" | sort -n | tail -1)
            echo "  $api: 최소 ${min_time}s, 최대 ${max_time}s"
        fi
    done
}

# 실행
main

# 정리
rm -f $RESULTS_FILE