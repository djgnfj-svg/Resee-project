#!/bin/bash

echo "🔥 Resee 스트레스 테스트 (고부하)"
echo "=================================="

# 테스트 설정
HEALTH_URL="http://localhost:8000/api/health/"
CONCURRENT_USERS=20
REQUESTS_PER_USER=10
TOTAL_REQUESTS=$((CONCURRENT_USERS * REQUESTS_PER_USER))

echo "📊 테스트 설정:"
echo "- 동시 사용자: $CONCURRENT_USERS명"
echo "- 사용자당 요청: $REQUESTS_PER_USER회"
echo "- 총 요청 수: $TOTAL_REQUESTS회"
echo ""

# 결과 수집 파일
RESULTS_FILE="/tmp/stress_test_results.txt"
> $RESULTS_FILE

echo "🚀 스트레스 테스트 시작..."
start_time=$(date +%s)

# 병렬 프로세스 시작
pids=()
for user in $(seq 1 $CONCURRENT_USERS); do
    (
        for req in $(seq 1 $REQUESTS_PER_USER); do
            request_start=$(date +%s.%N)
            response=$(curl -s -o /dev/null -w "%{http_code}:%{time_total}" $HEALTH_URL)
            request_end=$(date +%s.%N)

            http_code=$(echo $response | cut -d: -f1)
            response_time=$(echo $response | cut -d: -f2)

            echo "$user,$req,$http_code,$response_time" >> $RESULTS_FILE

            # 작은 랜덤 지연 (실제 사용자 시뮬레이션)
            sleep 0.$(shuf -i 1-5 -n 1)
        done
    ) &
    pids+=($!)
done

# 진행 상황 모니터링
monitor_progress() {
    while true; do
        current_requests=$(wc -l < $RESULTS_FILE 2>/dev/null || echo 0)
        percentage=$((current_requests * 100 / TOTAL_REQUESTS))
        printf "\r🔄 진행 상황: $current_requests/$TOTAL_REQUESTS ($percentage%%) "

        if [ $current_requests -ge $TOTAL_REQUESTS ]; then
            break
        fi
        sleep 1
    done
    echo ""
}

# 백그라운드에서 진행 상황 모니터링
monitor_progress &
monitor_pid=$!

# 모든 프로세스 완료 대기
for pid in "${pids[@]}"; do
    wait $pid
done

# 모니터링 프로세스 종료
kill $monitor_pid 2>/dev/null

end_time=$(date +%s)
total_time=$((end_time - start_time))

echo ""
echo "⏱️ 테스트 완료! 총 소요 시간: ${total_time}초"
echo ""

# 결과 분석
echo "📈 결과 분석 중..."

if [ -f $RESULTS_FILE ]; then
    total_requests=$(wc -l < $RESULTS_FILE)
    successful_requests=$(grep -c "200" $RESULTS_FILE)
    failed_requests=$((total_requests - successful_requests))
    success_rate=$((successful_requests * 100 / total_requests))

    # 응답 시간 통계 (200 응답만)
    response_times=$(grep "200" $RESULTS_FILE | cut -d, -f4)

    if [ ! -z "$response_times" ]; then
        min_time=$(echo "$response_times" | sort -n | head -1)
        max_time=$(echo "$response_times" | sort -n | tail -1)
        avg_time=$(echo "$response_times" | awk '{sum+=$1} END {print sum/NR}')

        # 95th percentile (간단 계산)
        percentile_95=$(echo "$response_times" | sort -n | awk 'NR==int(NR*0.95){print; exit}')
    else
        min_time=0
        max_time=0
        avg_time=0
        percentile_95=0
    fi

    requests_per_second=$((total_requests / total_time))

    echo ""
    echo "📊 === 스트레스 테스트 결과 요약 ==="
    echo "🔢 총 요청 수: $total_requests"
    echo "✅ 성공 요청: $successful_requests"
    echo "❌ 실패 요청: $failed_requests"
    echo "📈 성공률: $success_rate%"
    echo "🚀 초당 요청수: $requests_per_second req/s"
    echo ""
    echo "⏱️ 응답 시간 통계 (성공 요청만):"
    echo "- 최소: ${min_time}초"
    echo "- 최대: ${max_time}초"
    echo "- 평균: ${avg_time}초"
    echo "- 95th: ${percentile_95}초"
    echo ""

    # 성능 평가
    echo "🎯 성능 평가:"
    if [ $success_rate -ge 95 ]; then
        echo "✅ 성공률 우수 ($success_rate%)"
    elif [ $success_rate -ge 90 ]; then
        echo "⚠️ 성공률 양호 ($success_rate%)"
    else
        echo "❌ 성공률 개선 필요 ($success_rate%)"
    fi

    avg_time_ms=$(echo "$avg_time * 1000" | bc 2>/dev/null || echo "0")
    if (( $(echo "$avg_time < 0.1" | bc -l 2>/dev/null || echo 0) )); then
        echo "✅ 응답시간 매우 우수 (평균 ${avg_time}초)"
    elif (( $(echo "$avg_time < 0.5" | bc -l 2>/dev/null || echo 0) )); then
        echo "✅ 응답시간 우수 (평균 ${avg_time}초)"
    elif (( $(echo "$avg_time < 1.0" | bc -l 2>/dev/null || echo 0) )); then
        echo "⚠️ 응답시간 양호 (평균 ${avg_time}초)"
    else
        echo "❌ 응답시간 개선 필요 (평균 ${avg_time}초)"
    fi

    echo ""
    echo "🔍 최종 Docker 리소스 사용량:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep resee-project

else
    echo "❌ 결과 파일을 찾을 수 없습니다."
fi

# 정리
rm -f $RESULTS_FILE

echo ""
echo "🎉 스트레스 테스트 완료!"