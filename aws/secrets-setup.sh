#!/bin/bash

# AWS Secrets Manager 시크릿 설정 스크립트
set -e

# 설정 변수
AWS_REGION="ap-northeast-2"
PROJECT_NAME="resee"

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 시크릿 생성 함수
create_secret() {
    local secret_name=$1
    local secret_description=$2
    local default_value=${3:-"CHANGE_ME"}
    
    if aws secretsmanager describe-secret --secret-id "$secret_name" --region $AWS_REGION &> /dev/null; then
        log_info "시크릿 $secret_name이 이미 존재합니다."
    else
        aws secretsmanager create-secret \
            --name "$secret_name" \
            --description "$secret_description" \
            --secret-string "$default_value" \
            --region $AWS_REGION > /dev/null
        log_info "시크릿 $secret_name이 생성되었습니다."
    fi
}

# 시크릿 값 업데이트 함수
update_secret() {
    local secret_name=$1
    local secret_value=$2
    
    if [ -n "$secret_value" ] && [ "$secret_value" != "CHANGE_ME" ]; then
        aws secretsmanager update-secret \
            --secret-id "$secret_name" \
            --secret-string "$secret_value" \
            --region $AWS_REGION > /dev/null
        log_info "시크릿 $secret_name이 업데이트되었습니다."
    else
        log_warn "시크릿 $secret_name의 값을 수동으로 설정해야 합니다."
    fi
}

# 메인 함수
main() {
    log_info "AWS Secrets Manager 시크릿 설정 시작..."
    
    # 필수 시크릿들 생성
    create_secret "resee/django-secret-key" "Django SECRET_KEY" "$(openssl rand -base64 32)"
    create_secret "resee/database-url" "PostgreSQL Database URL"
    create_secret "resee/redis-url" "Redis URL"
    create_secret "resee/celery-broker-url" "Celery Broker URL"
    create_secret "resee/anthropic-api-key" "Anthropic API Key"
    create_secret "resee/stripe-secret-key" "Stripe Secret Key"
    create_secret "resee/stripe-webhook-secret" "Stripe Webhook Secret"
    create_secret "resee/aws-access-key-id" "AWS Access Key ID"
    create_secret "resee/aws-secret-access-key" "AWS Secret Access Key"
    
    # 선택적 시크릿들
    create_secret "resee/google-oauth-client-id" "Google OAuth Client ID" ""
    create_secret "resee/google-oauth-client-secret" "Google OAuth Client Secret" ""
    create_secret "resee/sentry-dsn" "Sentry DSN" ""
    create_secret "resee/datadog-api-key" "Datadog API Key" ""
    
    log_info "시크릿 생성이 완료되었습니다."
    echo
    log_warn "다음 시크릿들의 값을 실제 값으로 업데이트해야 합니다:"
    echo "  - resee/database-url"
    echo "  - resee/redis-url"
    echo "  - resee/celery-broker-url"
    echo "  - resee/anthropic-api-key"
    echo "  - resee/stripe-secret-key"
    echo "  - resee/stripe-webhook-secret"
    echo "  - resee/aws-access-key-id"
    echo "  - resee/aws-secret-access-key"
    echo
    echo "AWS 콘솔에서 업데이트하거나 다음 명령어를 사용하세요:"
    echo "aws secretsmanager update-secret --secret-id resee/database-url --secret-string 'postgresql://...'"
}

# 개별 시크릿 업데이트 함수들
update_database_url() {
    local db_endpoint=$1
    local db_password=$2
    local database_url="postgresql://postgres:${db_password}@${db_endpoint}:5432/resee_db"
    update_secret "resee/database-url" "$database_url"
}

update_redis_urls() {
    local redis_endpoint=$1
    update_secret "resee/redis-url" "redis://${redis_endpoint}:6379/0"
    update_secret "resee/celery-broker-url" "redis://${redis_endpoint}:6379/1"
}

# 명령행 인자 처리
case "${1:-create}" in
    "create")
        main
        ;;
    "update-db")
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "사용법: $0 update-db <RDS_ENDPOINT> <DB_PASSWORD>"
            exit 1
        fi
        update_database_url "$2" "$3"
        ;;
    "update-redis")
        if [ -z "$2" ]; then
            echo "사용법: $0 update-redis <REDIS_ENDPOINT>"
            exit 1
        fi
        update_redis_urls "$2"
        ;;
    "list")
        log_info "현재 생성된 시크릿 목록:"
        aws secretsmanager list-secrets \
            --filters Key=name,Values=resee/ \
            --query 'SecretList[].Name' \
            --output table \
            --region $AWS_REGION
        ;;
    *)
        echo "사용법: $0 {create|update-db|update-redis|list}"
        echo "  create        - 모든 시크릿 생성"
        echo "  update-db     - 데이터베이스 URL 업데이트"
        echo "  update-redis  - Redis URL 업데이트"
        echo "  list          - 시크릿 목록 확인"
        exit 1
        ;;
esac