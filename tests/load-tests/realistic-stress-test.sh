#!/bin/bash

echo "💀 현실적인 스트레스 테스트"
echo "========================="
echo "⚠️ 발견된 문제점들을 반영한 더 정확한 테스트"
echo ""

BASE_URL="http://localhost:8000/api"
LOGIN_URL="$BASE_URL/auth/token/"
CONTENT_URL="$BASE_URL/content/contents/"

# 더 현실적인 설정
CONCURRENT_USERS=30
REQUESTS_PER_USER=5

echo "📊 현실적인 테스트 설정:"
echo "- 동시 사용자: $CONCURRENT_USERS명"
echo "- 사용자당 요청: $REQUESTS_PER_USER회"
echo "- 각 사용자마다 개별 로그인 (토큰 재사용 X)"
echo "- 실제 DB 쿼리 부하"
echo ""

RESULTS_FILE="/tmp/realistic_stress_results.txt"
> $RESULTS_FILE

# 각 사용자가 개별 로그인하는 현실적인 테스트
realistic_user_test() {
    local user_id=$1

    for req in $(seq 1 $REQUESTS_PER_USER); do
        # 1. 매번 새로 로그인 (현실적)
        login_start=$(date +%s.%N)
        login_response=$(curl -s -w "HTTPCODE:%{http_code}:TIME:%{time_total}" \
            -X POST \
            -H "Content-Type: application/json" \
            -d '{"email":"test@example.com","password":"testpassword123"}' \
            $LOGIN_URL)
        login_end=$(date +%s.%N)

        login_code=$(echo $login_response | grep -o "HTTPCODE:[0-9]*" | cut -d: -f2)
        login_time=$(echo $login_response | grep -o "TIME:[0-9.]*" | cut -d: -f2)

        echo "User$user_id,Req$req,LOGIN,$login_code,$login_time" >> $RESULTS_FILE

        if [ "$login_code" = "200" ]; then
            # 토큰 추출
            json_response=$(echo $login_response | sed 's/HTTPCODE:.*TIME:.*//')
            token=$(echo $json_response | sed -n 's/.*"access":"\([^"]*\)".*/\1/p')

            if [ ! -z "$token" ]; then
                # 2. Content API 호출 (캐시 무력화를 위해 timestamp 추가)
                timestamp=$(date +%s%N)
                content_response=$(curl -s -w "HTTPCODE:%{http_code}:TIME:%{time_total}" \
                    -H "Authorization: Bearer $token" \
                    "$CONTENT_URL?nocache=$timestamp")

                content_code=$(echo $content_response | grep -o "HTTPCODE:[0-9]*" | cut -d: -f2)
                content_time=$(echo $content_response | grep -o "TIME:[0-9.]*" | cut -d: -f2)

                echo "User$user_id,Req$req,CONTENT,$content_code,$content_time" >> $RESULTS_FILE

                # 3. 또 다른 Content API 호출 (DB 부하 증가)
                content2_response=$(curl -s -w "HTTPCODE:%{http_code}:TIME:%{time_total}" \
                    -H "Authorization: Bearer $token" \
                    "$CONTENT_URL?page=1&nocache=$timestamp")

                content2_code=$(echo $content2_response | grep -o "HTTPCODE:[0-9]*" | cut -d: -f2)
                content2_time=$(echo $content2_response | grep -o "TIME:[0-9.]*" | cut -d: -f2)

                echo "User$user_id,Req$req,CONTENT2,$content2_code,$content2_time" >> $RESULTS_FILE
            fi
        fi

        # 현실적인 사용자 행동 (랜덤 지연 없음 - 스트레스 테스트)
        sleep 0.01
    done
}

echo "💀 현실적인 스트레스 테스트 시작!"
echo "   ⚠️ 각 사용자가 매번 로그인하므로 DB 부하 높음"
echo ""

start_time=$(date +%s)

# 30명 동시 실행 (각자 개별 로그인)
pids=()
for user in $(seq 1 $CONCURRENT_USERS); do
    realistic_user_test $user &
    pids+=($!)
done

# 진행 상황 모니터링
expected_total=$((CONCURRENT_USERS * REQUESTS_PER_USER * 3))  # LOGIN + CONTENT + CONTENT2
monitor() {
    while true; do
        current=$(wc -l < $RESULTS_FILE 2>/dev/null || echo 0)
        percentage=$((current * 100 / expected_total))
        printf "\r💀 현실적 부하: $current/$expected_total ($percentage%%) "

        running=0
        for pid in "${pids[@]}"; do
            if kill -0 $pid 2>/dev/null; then
                running=$((running + 1))
            fi
        done

        if [ $running -eq 0 ]; then
            break
        fi
        sleep 1
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
echo "⏱️ 현실적인 스트레스 테스트 완료! 소요시간: ${total_time}초"
echo ""

# 결과 분석
echo "📈 === 현실적인 스트레스 테스트 결과 ==="
echo ""

total_requests=$(wc -l < $RESULTS_FILE)
successful=$(grep ",200," $RESULTS_FILE | wc -l)
failed=$((total_requests - successful))
success_rate=$((successful * 100 / total_requests))

echo "📊 전체 통계:"
echo "  - 총 요청: $total_requests회"
echo "  - 성공: $successful회"
echo "  - 실패: $failed회"
echo "  - 성공률: $success_rate%"
echo "  - 초당 처리: $((total_requests / total_time)) requests/s"
echo ""

# API별 상세 분석
for api in LOGIN CONTENT CONTENT2; do
    api_total=$(grep ",$api," $RESULTS_FILE | wc -l)
    api_success=$(grep ",$api,200," $RESULTS_FILE | wc -l)
    if [ $api_total -gt 0 ]; then
        api_rate=$((api_success * 100 / api_total))
        avg_time=$(grep ",$api,200," $RESULTS_FILE | cut -d, -f5 | awk '{sum+=$1; count++} END {if(count>0) printf "%.3f", sum/count; else print "0"}')
        max_time=$(grep ",$api,200," $RESULTS_FILE | cut -d, -f5 | sort -n | tail -1)

        echo "🔹 $api API:"
        echo "   - 총 요청: $api_total회"
        echo "   - 성공률: $api_rate%"
        echo "   - 평균: ${avg_time}초"
        echo "   - 최대: ${max_time}초"
    fi
done

echo ""
echo "💾 최종 리소스 사용량:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep resee-project

echo ""
if [ $success_rate -ge 90 ]; then
    echo "✅ 현실적인 스트레스 테스트도 통과했습니다!"
elif [ $success_rate -ge 75 ]; then
    echo "⚠️ 현실적인 부하에서 일부 성능 저하가 있습니다."
else
    echo "❌ 현실적인 부하에서 심각한 성능 문제가 발견되었습니다."
fi

# 정리
rm -f $RESULTS_FILE

echo ""
echo "🎯 현실적인 스트레스 테스트 완료!"