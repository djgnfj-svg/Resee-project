#!/bin/bash

echo "🔥🔥🔥 DB 극한 부하 테스트 (50명 동시 접속)"
echo "==========================================="

BASE_URL="http://localhost:8000/api"
LOGIN_URL="$BASE_URL/auth/token/"
CONTENT_URL="$BASE_URL/content/contents/"
CATEGORY_URL="$BASE_URL/content/categories/"
REVIEW_URL="$BASE_URL/review/today/"

# 극한 부하 설정
CONCURRENT_USERS=50
REQUESTS_PER_USER=5

echo "💀 극한 테스트 설정:"
echo "- 동시 사용자: $CONCURRENT_USERS명"
echo "- 사용자당 요청: $REQUESTS_PER_USER회"
echo "- 총 예상 DB 쿼리: $((CONCURRENT_USERS * REQUESTS_PER_USER * 3))회"
echo ""

RESULTS_FILE="/tmp/extreme_db_results.txt"
> $RESULTS_FILE

# 토큰 캐시 (모든 사용자가 동일 토큰 사용하여 로그인 부하 감소)
TOKEN=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"testpassword123"}' \
    $LOGIN_URL | sed -n 's/.*"access":"\([^"]*\)".*/\1/p')

echo "🔑 토큰 획득 완료"
echo ""

# DB 집중 테스트
extreme_db_test() {
    local user_id=$1
    local headers="Authorization: Bearer $TOKEN"

    for req in $(seq 1 $REQUESTS_PER_USER); do
        # 3개 API 동시 호출로 DB 부하 극대화

        # 1. Content 조회 (DB 쿼리)
        curl -s -w "U$user_id,R$req,CONTENT,%{http_code},%{time_total}\n" \
            -H "$headers" "$CONTENT_URL" >> $RESULTS_FILE &

        # 2. Category 조회 (DB 쿼리)
        curl -s -w "U$user_id,R$req,CATEGORY,%{http_code},%{time_total}\n" \
            -H "$headers" "$CATEGORY_URL" >> $RESULTS_FILE &

        # 3. Review 조회 (복잡한 DB 쿼리)
        curl -s -w "U$user_id,R$req,REVIEW,%{http_code},%{time_total}\n" \
            -H "$headers" "$REVIEW_URL" >> $RESULTS_FILE &

        wait  # 3개 요청 완료 대기
        sleep 0.05  # 약간의 지연
    done
}

echo "💥 50명 동시 접속 시작!"
echo ""

# DB 상태 확인 (시작 전)
echo "📊 시작 전 DB 상태:"
docker exec resee-project-db-1 psql -U resee -d resee_db -c "SELECT count(*) as connections FROM pg_stat_activity;" 2>/dev/null || echo "DB 연결 수 확인 실패"
echo ""

start_time=$(date +%s)

# 50명 동시 실행
pids=()
for user in $(seq 1 $CONCURRENT_USERS); do
    extreme_db_test $user &
    pids+=($!)
done

# 진행 모니터링
expected_total=$((CONCURRENT_USERS * REQUESTS_PER_USER * 3))
monitor() {
    while true; do
        current=$(wc -l < $RESULTS_FILE 2>/dev/null || echo 0)
        percentage=$((current * 100 / expected_total))
        printf "\r⚡ DB 쿼리 진행: $current/$expected_total ($percentage%%) "

        # 실시간 리소스 모니터링
        if [ $((current % 50)) -eq 0 ] && [ $current -gt 0 ]; then
            echo ""
            echo "📊 실시간 DB 상태:"
            docker stats --no-stream --format "{{.Name}}: CPU {{.CPUPerc}}, MEM {{.MemUsage}}" | grep db
        fi

        running=0
        for pid in "${pids[@]}"; do
            if kill -0 $pid 2>/dev/null; then
                running=$((running + 1))
            fi
        done

        if [ $running -eq 0 ]; then
            break
        fi
        sleep 0.5
    done
    echo ""
}

monitor &
monitor_pid=$!

# 모든 프로세스 완료 대기
for pid in "${pids[@]}"; do
    wait $pid
done

kill $monitor_pid 2>/dev/null

end_time=$(date +%s)
total_time=$((end_time - start_time))

echo ""
echo "⏱️ 극한 테스트 완료! 소요시간: ${total_time}초"
echo ""

# 결과 분석
echo "📈 === 50명 동시 접속 결과 분석 ==="
echo ""

total_requests=$(wc -l < $RESULTS_FILE)
successful=$(grep ",200," $RESULTS_FILE | wc -l)
failed=$((total_requests - successful))
success_rate=$((successful * 100 / total_requests))

echo "📊 전체 통계:"
echo "  - 총 DB 쿼리: $total_requests회"
echo "  - 성공: $successful회"
echo "  - 실패: $failed회"
echo "  - 성공률: $success_rate%"
echo "  - 초당 처리: $((total_requests / total_time)) queries/s"
echo ""

# API별 분석
for api in CONTENT CATEGORY REVIEW; do
    api_total=$(grep ",$api," $RESULTS_FILE | wc -l)
    api_success=$(grep ",$api,200," $RESULTS_FILE | wc -l)
    if [ $api_total -gt 0 ]; then
        api_rate=$((api_success * 100 / api_total))
        avg_time=$(grep ",$api,200," $RESULTS_FILE | cut -d, -f5 | awk '{sum+=$1; count++} END {if(count>0) printf "%.3f", sum/count; else print "0"}')
        echo "🔹 $api API:"
        echo "   - 요청: $api_total회"
        echo "   - 성공률: $api_rate%"
        echo "   - 평균 응답: ${avg_time}초"
    fi
done

echo ""
echo "💾 최종 리소스 사용량:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep resee-project

echo ""
echo "📊 최종 DB 연결 상태:"
docker exec resee-project-db-1 psql -U resee -d resee_db -c "SELECT count(*) as connections FROM pg_stat_activity;" 2>/dev/null || echo "DB 연결 수 확인 실패"

echo ""
if [ $success_rate -ge 90 ]; then
    echo "✅ DB가 50명 동시 접속을 성공적으로 처리했습니다!"
elif [ $success_rate -ge 70 ]; then
    echo "⚠️ DB가 50명을 처리했지만 일부 실패가 있었습니다."
else
    echo "❌ DB가 50명 동시 접속에서 어려움을 겪었습니다."
fi

# 정리
rm -f $RESULTS_FILE

echo ""
echo "🎉 DB 극한 부하 테스트 완료!"