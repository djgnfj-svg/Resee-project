#!/bin/bash

echo "💪 백엔드 집약적 부하 테스트"
echo "==========================="

BASE_URL="http://localhost:8000/api"
LOGIN_URL="$BASE_URL/auth/token/"
CONTENT_URL="$BASE_URL/content/contents/"
CATEGORY_URL="$BASE_URL/content/categories/"

# 더 강한 부하 설정
CONCURRENT_USERS=20
REQUESTS_PER_USER=10
TOTAL_REQUESTS=$((CONCURRENT_USERS * REQUESTS_PER_USER))

echo "📊 집약적 테스트 설정:"
echo "- 동시 사용자: $CONCURRENT_USERS명"
echo "- 사용자당 요청: $REQUESTS_PER_USER회"
echo "- 총 요청 수: $TOTAL_REQUESTS회"
echo ""

RESULTS_FILE="/tmp/intensive_backend_results.txt"
> $RESULTS_FILE

# 토큰 획득
get_token() {
    curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"testpassword123"}' \
        $LOGIN_URL | sed -n 's/.*"access":"\([^"]*\)".*/\1/p'
}

# 집약적 API 테스트 (동일한 API를 반복 호출)
intensive_api_test() {
    local user_id=$1
    local api_name=$2
    local url=$3

    local token=$(get_token)
    if [ -z "$token" ]; then
        return
    fi

    local headers="Authorization: Bearer $token"

    for req in $(seq 1 $REQUESTS_PER_USER); do
        local response=$(curl -s -w "HTTPCODE:%{http_code}:TIME:%{time_total}" \
            -H "$headers" \
            "$url")

        local http_code=$(echo $response | grep -o "HTTPCODE:[0-9]*" | cut -d: -f2)
        local response_time=$(echo $response | grep -o "TIME:[0-9.]*" | cut -d: -f2)

        echo "User$user_id,Req$req,$api_name,$http_code,$response_time" >> $RESULTS_FILE

        # 최소 지연으로 빠른 연속 요청
        sleep 0.01
    done
}

# 개별 API별 집약적 테스트
run_intensive_test() {
    local api_name=$1
    local url=$2

    echo "🔥 $api_name API 집약적 테스트 시작..."
    echo "   - $CONCURRENT_USERS명이 각각 $REQUESTS_PER_USER번 연속 호출"

    local start_time=$(date +%s)

    local pids=()
    for user in $(seq 1 $CONCURRENT_USERS); do
        intensive_api_test $user $api_name $url &
        pids+=($!)
    done

    # 진행 상황 모니터링
    local expected_for_this_api=$TOTAL_REQUESTS
    while true; do
        local current=$(grep ",$api_name," $RESULTS_FILE 2>/dev/null | wc -l)
        local percentage=$((current * 100 / expected_for_this_api))
        printf "\r   🔄 진행: $current/$expected_for_this_api ($percentage%%) "

        if [ $current -ge $expected_for_this_api ]; then
            break
        fi
        sleep 0.5
    done
    echo ""

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

    # 응답시간 분포
    local times=$(grep ",$api_name,200," $RESULTS_FILE | cut -d, -f5)
    local min_time=$(echo "$times" | sort -n | head -1)
    local max_time=$(echo "$times" | sort -n | tail -1)

    echo ""
    echo "📈 $api_name API 집약적 테스트 결과:"
    echo "  - 총 요청: $total_calls회"
    echo "  - 성공: $successful_calls회 ($success_rate%)"
    echo "  - 실패: $failed_calls회"
    echo "  - 소요시간: ${total_time}초"
    echo "  - 초당 요청수: ${rps} req/s"
    echo "  - 평균 응답시간: ${avg_time}초"
    echo "  - 최소 응답시간: ${min_time}초"
    echo "  - 최대 응답시간: ${max_time}초"

    # 성능 등급
    if [ $success_rate -ge 98 ] && [ $(echo "$avg_time < 0.1" | bc -l 2>/dev/null || echo 0) -eq 1 ]; then
        echo "  - 성능 등급: 🏆 S급 (완벽)"
    elif [ $success_rate -ge 95 ] && [ $(echo "$avg_time < 0.2" | bc -l 2>/dev/null || echo 0) -eq 1 ]; then
        echo "  - 성능 등급: ⭐ A급 (우수)"
    elif [ $success_rate -ge 90 ] && [ $(echo "$avg_time < 0.5" | bc -l 2>/dev/null || echo 0) -eq 1 ]; then
        echo "  - 성능 등급: ✅ B급 (양호)"
    else
        echo "  - 성능 등급: ⚠️ C급 (개선 필요)"
    fi
    echo ""

    # 현재 리소스 사용량
    echo "📊 현재 Docker 리소스 사용량:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep resee-project
    echo ""

    # 테스트 간 쿨다운
    echo "⏸️ 5초 쿨다운..."
    sleep 5
}

# 메인 실행
main() {
    echo "🚀 집약적 백엔드 부하 테스트 시작!"
    echo ""

    # 1. 컨텐츠 API 집약적 테스트
    run_intensive_test "CONTENT" "$CONTENT_URL"

    # 2. 카테고리 API 집약적 테스트
    run_intensive_test "CATEGORY" "$CATEGORY_URL"

    # 3. 혼합 부하 테스트 (두 API 동시)
    echo "🌪️ 혼합 부하 테스트 시작..."
    echo "   - CONTENT와 CATEGORY API 동시 호출"

    local mixed_start_time=$(date +%s)

    # CONTENT API 부하
    for user in $(seq 1 $((CONCURRENT_USERS / 2))); do
        intensive_api_test $user "MIXED_CONTENT" "$CONTENT_URL" &
    done

    # CATEGORY API 부하
    for user in $(seq $((CONCURRENT_USERS / 2 + 1)) $CONCURRENT_USERS); do
        intensive_api_test $user "MIXED_CATEGORY" "$CATEGORY_URL" &
    done

    wait  # 모든 백그라운드 작업 완료 대기

    local mixed_end_time=$(date +%s)
    local mixed_total_time=$((mixed_end_time - mixed_start_time))

    echo "🌪️ 혼합 부하 테스트 완료 (${mixed_total_time}초)"
    echo ""

    # 최종 결과 요약
    echo "🏁 === 최종 집약적 테스트 결과 ==="
    local final_total=$(wc -l < $RESULTS_FILE)
    local final_success=$(grep ",200," $RESULTS_FILE | wc -l)
    local final_success_rate=$((final_success * 100 / final_total))

    echo "📊 전체 통계:"
    echo "  - 총 API 호출: $final_total회"
    echo "  - 총 성공: $final_success회"
    echo "  - 전체 성공률: $final_success_rate%"
    echo ""

    echo "🔥 최대 부하 시 Docker 리소스:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep resee-project
    echo ""

    if [ $final_success_rate -ge 95 ]; then
        echo "🎯 결론: 백엔드가 집약적 부하를 우수하게 처리했습니다! 🎉"
    elif [ $final_success_rate -ge 85 ]; then
        echo "🎯 결론: 백엔드가 집약적 부하를 양호하게 처리했습니다. ✅"
    else
        echo "🎯 결론: 집약적 부하에서 성능 개선이 필요합니다. ⚠️"
    fi
}

# 실행
main

# 정리
rm -f $RESULTS_FILE

echo ""
echo "🎉 집약적 백엔드 부하 테스트 완료!"