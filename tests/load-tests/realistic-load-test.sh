#!/bin/bash

echo "🎯 Resee 실제 시나리오 부하 테스트"
echo "=================================="

# API 엔드포인트들
HEALTH_URL="http://localhost:8000/api/health/"
LOGIN_URL="http://localhost:8000/api/auth/token/"
CONTENTS_URL="http://localhost:8000/api/content/contents/"
CATEGORIES_URL="http://localhost:8000/api/content/categories/"
REVIEW_URL="http://localhost:8000/api/review/today/"
DASHBOARD_URL="http://localhost:8000/api/analytics/dashboard/"

CONCURRENT_USERS=10
REQUESTS_PER_USER=3

echo "📊 실제 사용자 시나리오 테스트:"
echo "- 동시 사용자: $CONCURRENT_USERS명"
echo "- 사용자당 시나리오: $REQUESTS_PER_USER회 반복"
echo ""

# 결과 저장
RESULTS_FILE="/tmp/realistic_test_results.txt"
> $RESULTS_FILE

# 실제 사용자 시나리오 함수
user_scenario() {
    local user_id=$1
    local scenario_num=$2

    # 1. 로그인
    login_start=$(date +%s.%N)
    login_response=$(curl -s -w "HTTPCODE:%{http_code}:TIME:%{time_total}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"testpassword123"}' \
        $LOGIN_URL)
    login_end=$(date +%s.%N)

    login_code=$(echo $login_response | grep -o "HTTPCODE:[0-9]*" | cut -d: -f2)
    login_time=$(echo $login_response | grep -o "TIME:[0-9.]*" | cut -d: -f2)

    echo "User$user_id,Scenario$scenario_num,LOGIN,$login_code,$login_time" >> $RESULTS_FILE

    if [ "$login_code" = "200" ]; then
        # JSON 응답에서 토큰 추출
        json_response=$(echo $login_response | sed 's/HTTPCODE:.*TIME:.*//')
        token=$(echo $json_response | sed -n 's/.*"access":"\([^"]*\)".*/\1/p')

        if [ ! -z "$token" ]; then
            headers="Authorization: Bearer $token"

            # 2. 콘텐츠 목록 조회
            contents_response=$(curl -s -o /dev/null -w "%{http_code}:%{time_total}" \
                -H "$headers" \
                $CONTENTS_URL)
            contents_code=$(echo $contents_response | cut -d: -f1)
            contents_time=$(echo $contents_response | cut -d: -f2)
            echo "User$user_id,Scenario$scenario_num,CONTENTS,$contents_code,$contents_time" >> $RESULTS_FILE

            # 3. 카테고리 조회
            categories_response=$(curl -s -o /dev/null -w "%{http_code}:%{time_total}" \
                -H "$headers" \
                $CATEGORIES_URL)
            categories_code=$(echo $categories_response | cut -d: -f1)
            categories_time=$(echo $categories_response | cut -d: -f2)
            echo "User$user_id,Scenario$scenario_num,CATEGORIES,$categories_code,$categories_time" >> $RESULTS_FILE

            # 4. 오늘의 복습 조회
            review_response=$(curl -s -o /dev/null -w "%{http_code}:%{time_total}" \
                -H "$headers" \
                $REVIEW_URL)
            review_code=$(echo $review_response | cut -d: -f1)
            review_time=$(echo $review_response | cut -d: -f2)
            echo "User$user_id,Scenario$scenario_num,REVIEW,$review_code,$review_time" >> $RESULTS_FILE

            # 5. 대시보드 분석
            dashboard_response=$(curl -s -o /dev/null -w "%{http_code}:%{time_total}" \
                -H "$headers" \
                $DASHBOARD_URL)
            dashboard_code=$(echo $dashboard_response | cut -d: -f1)
            dashboard_time=$(echo $dashboard_response | cut -d: -f2)
            echo "User$user_id,Scenario$scenario_num,DASHBOARD,$dashboard_code,$dashboard_time" >> $RESULTS_FILE
        else
            echo "User$user_id,Scenario$scenario_num,TOKEN_EXTRACT,FAILED,0" >> $RESULTS_FILE
        fi
    fi

    # 사용자별 랜덤 대기 (0.5-2초)
    sleep_time=$(shuf -i 5-20 -n 1)
    sleep 0.$sleep_time
}

echo "🚀 실제 시나리오 테스트 시작..."
start_time=$(date +%s)

# 병렬 사용자 시뮬레이션
pids=()
for user in $(seq 1 $CONCURRENT_USERS); do
    (
        for scenario in $(seq 1 $REQUESTS_PER_USER); do
            user_scenario $user $scenario
        done
    ) &
    pids+=($!)
done

# 진행 상황 모니터링
total_expected=$((CONCURRENT_USERS * REQUESTS_PER_USER * 5)) # 5 API calls per scenario
monitor_realistic() {
    while true; do
        current_requests=$(wc -l < $RESULTS_FILE 2>/dev/null || echo 0)
        percentage=$((current_requests * 100 / total_expected))
        printf "\r🔄 API 호출 진행: $current_requests/$total_expected ($percentage%%) "

        # 모든 프로세스 완료 확인
        running_processes=0
        for pid in "${pids[@]}"; do
            if kill -0 $pid 2>/dev/null; then
                running_processes=$((running_processes + 1))
            fi
        done

        if [ $running_processes -eq 0 ]; then
            break
        fi
        sleep 1
    done
    echo ""
}

# 모니터링 시작
monitor_realistic &
monitor_pid=$!

# 모든 프로세스 완료 대기
for pid in "${pids[@]}"; do
    wait $pid
done

# 모니터링 종료
kill $monitor_pid 2>/dev/null

end_time=$(date +%s)
total_time=$((end_time - start_time))

echo ""
echo "⏱️ 실제 시나리오 테스트 완료! 총 소요 시간: ${total_time}초"
echo ""

# 결과 분석
echo "📈 API별 결과 분석..."

if [ -f $RESULTS_FILE ]; then
    total_calls=$(wc -l < $RESULTS_FILE)

    echo ""
    echo "📊 === API별 성능 분석 ==="

    for api in LOGIN CONTENTS CATEGORIES REVIEW DASHBOARD; do
        api_calls=$(grep ",$api," $RESULTS_FILE | wc -l)
        successful_calls=$(grep ",$api,200," $RESULTS_FILE | wc -l)
        failed_calls=$((api_calls - successful_calls))

        if [ $api_calls -gt 0 ]; then
            success_rate=$((successful_calls * 100 / api_calls))
            avg_time=$(grep ",$api,200," $RESULTS_FILE | cut -d, -f5 | awk '{sum+=$1} END {if(NR>0) print sum/NR; else print 0}')

            echo ""
            echo "🔗 $api API:"
            echo "  - 총 호출: $api_calls회"
            echo "  - 성공: $successful_calls회"
            echo "  - 실패: $failed_calls회"
            echo "  - 성공률: $success_rate%"
            echo "  - 평균 응답시간: ${avg_time}초"

            # 성능 평가
            if [ $success_rate -ge 95 ]; then
                echo "  - 평가: ✅ 우수"
            elif [ $success_rate -ge 90 ]; then
                echo "  - 평가: ⚠️ 양호"
            else
                echo "  - 평가: ❌ 개선 필요"
            fi
        fi
    done

    echo ""
    echo "🎯 전체 결과:"
    echo "- 총 API 호출: $total_calls회"
    echo "- 초당 API 호출: $((total_calls / total_time)) calls/s"
    echo ""

    echo "🔍 최종 리소스 사용량:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep resee-project
else
    echo "❌ 결과 파일을 찾을 수 없습니다."
fi

# 정리
rm -f $RESULTS_FILE

echo ""
echo "🎉 실제 시나리오 테스트 완료!"