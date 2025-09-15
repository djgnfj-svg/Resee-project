#!/bin/bash

echo "🔥 DB 부하 테스트 (50명 동시 접속)"
echo "===================================="

BASE_URL="http://localhost:8000/api"
LOGIN_URL="$BASE_URL/auth/token/"
CONTENT_URL="$BASE_URL/content/contents/"

CONCURRENT_USERS=50
REQUESTS_PER_USER=3

echo "📊 테스트 설정:"
echo "- 동시 사용자: $CONCURRENT_USERS명"
echo "- 사용자당 요청: $REQUESTS_PER_USER회"
echo ""

RESULTS_FILE="/tmp/50users_results.txt"
> $RESULTS_FILE

# 토큰 획득
TOKEN=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"testpassword123"}' \
    $LOGIN_URL | sed -n 's/.*"access":"\([^"]*\)".*/\1/p')

echo "🔑 토큰 획득 완료"
echo ""

# 단순 부하 테스트
simple_test() {
    local user_id=$1
    local headers="Authorization: Bearer $TOKEN"

    for req in $(seq 1 $REQUESTS_PER_USER); do
        # Content API만 호출
        response=$(curl -s -w "HTTPCODE:%{http_code}:TIME:%{time_total}" \
            -H "$headers" "$CONTENT_URL")

        http_code=$(echo $response | grep -o "HTTPCODE:[0-9]*" | cut -d: -f2)
        time=$(echo $response | grep -o "TIME:[0-9.]*" | cut -d: -f2)

        echo "User$user_id,Req$req,$http_code,$time" >> $RESULTS_FILE

        sleep 0.1
    done
}

echo "💥 50명 동시 접속 시작!"
start_time=$(date +%s)

# 50명 동시 실행
for user in $(seq 1 $CONCURRENT_USERS); do
    simple_test $user &
done

# 모든 작업 완료 대기
wait

end_time=$(date +%s)
total_time=$((end_time - start_time))

echo ""
echo "⏱️ 테스트 완료! 소요시간: ${total_time}초"
echo ""

# 결과 분석
total_requests=$(wc -l < $RESULTS_FILE)
successful=$(grep ",200," $RESULTS_FILE | wc -l)
failed=$((total_requests - successful))
success_rate=$((successful * 100 / total_requests))

echo "📊 결과:"
echo "  - 총 요청: $total_requests회"
echo "  - 성공: $successful회"
echo "  - 실패: $failed회"
echo "  - 성공률: $success_rate%"

if [ $successful -gt 0 ]; then
    avg_time=$(grep ",200," $RESULTS_FILE | cut -d, -f4 | awk '{sum+=$1; count++} END {printf "%.3f", sum/count}')
    echo "  - 평균 응답시간: ${avg_time}초"
fi

echo ""
echo "💾 리소스 사용량:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep resee-project

# 정리
rm -f $RESULTS_FILE

echo ""
if [ $success_rate -ge 90 ]; then
    echo "✅ DB가 50명을 성공적으로 처리했습니다!"
elif [ $success_rate -ge 70 ]; then
    echo "⚠️ DB가 50명을 처리했지만 일부 문제가 있었습니다."
else
    echo "❌ DB가 50명 처리에 어려움이 있었습니다."
fi