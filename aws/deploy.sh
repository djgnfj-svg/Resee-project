#!/bin/bash

# Resee AWS 배포 스크립트
set -e

# 설정 변수
PROJECT_NAME="resee"
ENVIRONMENT="production"
AWS_REGION="ap-northeast-2"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}-backend"

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

# 필수 도구 확인
check_requirements() {
    log_info "필수 도구 확인 중..."
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI가 설치되지 않았습니다."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker가 설치되지 않았습니다."
        exit 1
    fi
    
    # AWS 자격 증명 확인
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS 자격 증명이 설정되지 않았습니다."
        exit 1
    fi
    
    log_info "모든 필수 도구가 설치되어 있습니다."
}

# ECR 리포지토리 생성
create_ecr_repository() {
    log_info "ECR 리포지토리 생성 중..."
    
    if aws ecr describe-repositories --repository-names "${PROJECT_NAME}-backend" --region $AWS_REGION &> /dev/null; then
        log_info "ECR 리포지토리가 이미 존재합니다."
    else
        aws ecr create-repository \
            --repository-name "${PROJECT_NAME}-backend" \
            --region $AWS_REGION \
            --image-scanning-configuration scanOnPush=true
        log_info "ECR 리포지토리가 생성되었습니다."
    fi
}

# Docker 이미지 빌드 및 푸시
build_and_push_image() {
    log_info "Docker 이미지 빌드 중..."
    
    # ECR 로그인
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY
    
    # 이미지 빌드
    docker build -t "${PROJECT_NAME}-backend:latest" -f backend/Dockerfile backend/
    
    # 태그 지정
    docker tag "${PROJECT_NAME}-backend:latest" "${ECR_REPOSITORY}:latest"
    docker tag "${PROJECT_NAME}-backend:latest" "${ECR_REPOSITORY}:$(date +%Y%m%d-%H%M%S)"
    
    # ECR에 푸시
    log_info "Docker 이미지 푸시 중..."
    docker push "${ECR_REPOSITORY}:latest"
    docker push "${ECR_REPOSITORY}:$(date +%Y%m%d-%H%M%S)"
    
    log_info "Docker 이미지가 푸시되었습니다."
}

# Secrets Manager에 시크릿 생성
create_secrets() {
    log_info "AWS Secrets Manager에 시크릿 생성 중..."
    
    # 시크릿 목록
    secrets=(
        "resee/django-secret-key"
        "resee/database-url"
        "resee/redis-url"
        "resee/celery-broker-url"
        "resee/anthropic-api-key"
        "resee/stripe-secret-key"
        "resee/stripe-webhook-secret"
        "resee/aws-access-key-id"
        "resee/aws-secret-access-key"
    )
    
    for secret in "${secrets[@]}"; do
        if aws secretsmanager describe-secret --secret-id "$secret" --region $AWS_REGION &> /dev/null; then
            log_info "시크릿 $secret이 이미 존재합니다."
        else
            aws secretsmanager create-secret \
                --name "$secret" \
                --description "Resee production secret" \
                --secret-string "CHANGE_ME" \
                --region $AWS_REGION
            log_warn "시크릿 $secret이 생성되었습니다. 실제 값으로 업데이트해야 합니다."
        fi
    done
}

# CloudFormation 스택 배포
deploy_infrastructure() {
    log_info "CloudFormation 인프라 배포 중..."
    
    # 스택 존재 여부 확인
    if aws cloudformation describe-stacks --stack-name "${PROJECT_NAME}-${ENVIRONMENT}" --region $AWS_REGION &> /dev/null; then
        log_info "기존 스택 업데이트 중..."
        aws cloudformation update-stack \
            --stack-name "${PROJECT_NAME}-${ENVIRONMENT}" \
            --template-body file://aws/cloudformation-infrastructure.yaml \
            --parameters ParameterKey=ProjectName,ParameterValue=$PROJECT_NAME \
                        ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
                        ParameterKey=DomainName,ParameterValue=resee.com \
                        ParameterKey=DBPassword,ParameterValue=CHANGE_ME_SECURE_PASSWORD \
            --capabilities CAPABILITY_NAMED_IAM \
            --region $AWS_REGION
    else
        log_info "새 스택 생성 중..."
        aws cloudformation create-stack \
            --stack-name "${PROJECT_NAME}-${ENVIRONMENT}" \
            --template-body file://aws/cloudformation-infrastructure.yaml \
            --parameters ParameterKey=ProjectName,ParameterValue=$PROJECT_NAME \
                        ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
                        ParameterKey=DomainName,ParameterValue=resee.com \
                        ParameterKey=DBPassword,ParameterValue=CHANGE_ME_SECURE_PASSWORD \
            --capabilities CAPABILITY_NAMED_IAM \
            --region $AWS_REGION
    fi
    
    log_info "CloudFormation 스택 배포 대기 중..."
    aws cloudformation wait stack-create-complete \
        --stack-name "${PROJECT_NAME}-${ENVIRONMENT}" \
        --region $AWS_REGION || \
    aws cloudformation wait stack-update-complete \
        --stack-name "${PROJECT_NAME}-${ENVIRONMENT}" \
        --region $AWS_REGION
    
    log_info "인프라 배포가 완료되었습니다."
}

# ECS 서비스 배포
deploy_ecs_service() {
    log_info "ECS 서비스 배포 중..."
    
    # Task Definition 등록
    sed "s/YOUR_ACCOUNT_ID/${AWS_ACCOUNT_ID}/g" aws/ecs-task-definition.json > aws/ecs-task-definition-updated.json
    
    aws ecs register-task-definition \
        --cli-input-json file://aws/ecs-task-definition-updated.json \
        --region $AWS_REGION
    
    # 서비스 존재 여부 확인
    if aws ecs describe-services \
        --cluster "${PROJECT_NAME}-${ENVIRONMENT}-cluster" \
        --services "${PROJECT_NAME}-${ENVIRONMENT}-service" \
        --region $AWS_REGION \
        --query 'services[0].status' \
        --output text 2>/dev/null | grep -q "ACTIVE"; then
        
        log_info "기존 ECS 서비스 업데이트 중..."
        aws ecs update-service \
            --cluster "${PROJECT_NAME}-${ENVIRONMENT}-cluster" \
            --service "${PROJECT_NAME}-${ENVIRONMENT}-service" \
            --task-definition "resee-backend" \
            --region $AWS_REGION
    else
        log_info "새 ECS 서비스 생성 중..."
        
        # CloudFormation 출력에서 필요한 값들 가져오기
        SUBNET_1=$(aws cloudformation describe-stacks \
            --stack-name "${PROJECT_NAME}-${ENVIRONMENT}" \
            --query 'Stacks[0].Outputs[?OutputKey==`PrivateSubnet1Id`].OutputValue' \
            --output text --region $AWS_REGION)
        
        SUBNET_2=$(aws cloudformation describe-stacks \
            --stack-name "${PROJECT_NAME}-${ENVIRONMENT}" \
            --query 'Stacks[0].Outputs[?OutputKey==`PrivateSubnet2Id`].OutputValue' \
            --output text --region $AWS_REGION)
        
        SECURITY_GROUP=$(aws cloudformation describe-stacks \
            --stack-name "${PROJECT_NAME}-${ENVIRONMENT}" \
            --query 'Stacks[0].Outputs[?OutputKey==`ECSSecurityGroupId`].OutputValue' \
            --output text --region $AWS_REGION)
        
        TARGET_GROUP_ARN=$(aws cloudformation describe-stacks \
            --stack-name "${PROJECT_NAME}-${ENVIRONMENT}" \
            --query 'Stacks[0].Outputs[?OutputKey==`ALBTargetGroupArn`].OutputValue' \
            --output text --region $AWS_REGION)
        
        aws ecs create-service \
            --cluster "${PROJECT_NAME}-${ENVIRONMENT}-cluster" \
            --service-name "${PROJECT_NAME}-${ENVIRONMENT}-service" \
            --task-definition "resee-backend" \
            --desired-count 2 \
            --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2],securityGroups=[$SECURITY_GROUP],assignPublicIp=DISABLED}" \
            --load-balancers "targetGroupArn=$TARGET_GROUP_ARN,containerName=backend,containerPort=8000" \
            --region $AWS_REGION
    fi
    
    log_info "ECS 서비스 배포가 완료되었습니다."
}

# 배포 상태 확인
check_deployment() {
    log_info "배포 상태 확인 중..."
    
    # ECS 서비스 상태 확인
    aws ecs wait services-stable \
        --cluster "${PROJECT_NAME}-${ENVIRONMENT}-cluster" \
        --services "${PROJECT_NAME}-${ENVIRONMENT}-service" \
        --region $AWS_REGION
    
    # ALB DNS 이름 가져오기
    ALB_DNS=$(aws cloudformation describe-stacks \
        --stack-name "${PROJECT_NAME}-${ENVIRONMENT}" \
        --query 'Stacks[0].Outputs[?OutputKey==`ALBDNSName`].OutputValue' \
        --output text --region $AWS_REGION)
    
    log_info "배포가 성공적으로 완료되었습니다!"
    log_info "ALB URL: http://$ALB_DNS"
    log_info "헬스체크 URL: http://$ALB_DNS/api/health/"
}

# 메인 함수
main() {
    log_info "Resee AWS 배포 시작..."
    
    case "${1:-all}" in
        "check")
            check_requirements
            ;;
        "ecr")
            check_requirements
            create_ecr_repository
            ;;
        "build")
            check_requirements
            create_ecr_repository
            build_and_push_image
            ;;
        "secrets")
            check_requirements
            create_secrets
            ;;
        "infra")
            check_requirements
            deploy_infrastructure
            ;;
        "service")
            check_requirements
            deploy_ecs_service
            ;;
        "status")
            check_deployment
            ;;
        "all")
            check_requirements
            create_ecr_repository
            build_and_push_image
            create_secrets
            deploy_infrastructure
            deploy_ecs_service
            check_deployment
            ;;
        *)
            echo "사용법: $0 {check|ecr|build|secrets|infra|service|status|all}"
            echo "  check   - 필수 도구 확인"
            echo "  ecr     - ECR 리포지토리 생성"
            echo "  build   - Docker 이미지 빌드 및 푸시"
            echo "  secrets - AWS Secrets Manager 시크릿 생성"
            echo "  infra   - CloudFormation 인프라 배포"
            echo "  service - ECS 서비스 배포"
            echo "  status  - 배포 상태 확인"
            echo "  all     - 전체 배포 프로세스 실행"
            exit 1
            ;;
    esac
}

# 스크립트 실행
main "$@"