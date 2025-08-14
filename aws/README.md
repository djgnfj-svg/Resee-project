# Resee AWS 배포 가이드

## 🚀 배포 개요

이 가이드는 Resee 애플리케이션을 AWS에 프로덕션 배포하는 과정을 설명합니다.

### 주요 AWS 서비스
- **ECS Fargate**: 컨테이너 오케스트레이션
- **RDS PostgreSQL**: 메인 데이터베이스 (Multi-AZ)
- **ElastiCache Redis**: 캐시 및 세션 스토어
- **Application Load Balancer**: 로드 밸런싱 및 HTTPS 터미네이션
- **CloudFront**: CDN 및 정적 파일 제공
- **S3**: 정적 파일 저장소
- **Secrets Manager**: 민감한 정보 관리
- **CloudWatch**: 로깅 및 모니터링

## 📋 사전 요구사항

### 1. 도구 설치
```bash
# AWS CLI 설치 및 설정
aws configure

# Docker 설치
docker --version

# 도메인 등록 (Route 53 또는 외부)
# SSL 인증서 (Certificate Manager)
```

### 2. AWS 계정 설정
- IAM 사용자 생성 (AdministratorAccess 권한)
- AWS CLI 자격 증명 설정
- 리전 설정: `ap-northeast-2` (서울)

## 🏗️ 배포 단계

### 1단계: 인프라 배포
```bash
# CloudFormation으로 인프라 생성
cd aws/
./deploy.sh infra

# 완료까지 약 15-20분 소요
```

### 2단계: 시크릿 설정
```bash
# 시크릿 생성
./secrets-setup.sh create

# 개별 시크릿 값 업데이트
aws secretsmanager update-secret \
  --secret-id resee/anthropic-api-key \
  --secret-string "your-actual-api-key"

# 또는 AWS 콘솔에서 직접 업데이트
```

### 3단계: 데이터베이스 설정
```bash
# RDS 엔드포인트 확인
aws cloudformation describe-stacks \
  --stack-name resee-production \
  --query 'Stacks[0].Outputs[?OutputKey==`RDSEndpoint`].OutputValue' \
  --output text

# 데이터베이스 URL 업데이트
./secrets-setup.sh update-db YOUR_RDS_ENDPOINT YOUR_DB_PASSWORD

# 마이그레이션 실행 (애플리케이션 배포 후)
```

### 4단계: 애플리케이션 배포
```bash
# Docker 이미지 빌드 및 배포
./deploy.sh build

# ECS 서비스 배포
./deploy.sh service

# 배포 상태 확인
./deploy.sh status
```

## 🔧 설정 세부사항

### 환경변수 설정
```bash
# .env.production.template을 참고하여 설정
cp .env.production.template .env.production

# 필수 환경변수들:
# - SECRET_KEY: Django 시크릿 키
# - DATABASE_URL: RDS PostgreSQL URL
# - REDIS_URL: ElastiCache Redis URL
# - STRIPE_SECRET_KEY: Stripe 라이브 키
# - ANTHROPIC_API_KEY: Claude API 키
```

### SSL/HTTPS 설정
1. **Certificate Manager**에서 SSL 인증서 발급
   - 도메인: `resee.com`, `*.resee.com`
   - DNS 검증 사용

2. **ALB Listener** 업데이트
   ```bash
   # HTTPS 리스너 추가 (포트 443)
   aws elbv2 create-listener \
     --load-balancer-arn YOUR_ALB_ARN \
     --protocol HTTPS \
     --port 443 \
     --certificates CertificateArn=YOUR_CERT_ARN \
     --default-actions Type=forward,TargetGroupArn=YOUR_TARGET_GROUP_ARN
   ```

3. **Route 53** DNS 설정
   ```bash
   # A 레코드 생성 (ALB 별칭)
   resee.com -> ALB DNS Name
   www.resee.com -> ALB DNS Name
   ```

### Stripe 웹훅 설정
1. Stripe 대시보드에서 웹훅 엔드포인트 추가
   - URL: `https://resee.com/api/payments/webhook/`
   - 이벤트: `payment_intent.succeeded`, `invoice.payment_succeeded` 등

2. 웹훅 시크릿 업데이트
   ```bash
   aws secretsmanager update-secret \
     --secret-id resee/stripe-webhook-secret \
     --secret-string "whsec_your_webhook_secret"
   ```

## 📊 모니터링 설정

### CloudWatch 대시보드
```bash
# 커스텀 대시보드 생성
aws cloudwatch put-dashboard \
  --dashboard-name "Resee-Production" \
  --dashboard-body file://cloudwatch-dashboard.json
```

### 알람 설정
```bash
# CPU 사용률 알람
aws cloudwatch put-metric-alarm \
  --alarm-name "Resee-HighCPU" \
  --alarm-description "ECS CPU usage too high" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold
```

## 🔐 보안 체크리스트

### 네트워크 보안
- ✅ Private 서브넷에 ECS 태스크 배치
- ✅ Security Group 최소 권한 원칙
- ✅ ALB에서 HTTPS 강제 리다이렉트
- ✅ WAF 설정 (SQL 인젝션, XSS 방어)

### 데이터 보안
- ✅ RDS 암호화 활성화
- ✅ S3 버킷 암호화
- ✅ Secrets Manager 사용
- ✅ IAM 역할 최소 권한

### 애플리케이션 보안
- ✅ Django SECURITY_* 설정
- ✅ CORS 정책 적용
- ✅ Rate Limiting 활성화
- ✅ 정기적인 보안 업데이트

## 💰 비용 최적화

### 예상 월간 비용 (서울 리전)
```
ECS Fargate (2 tasks, 1 vCPU, 2GB): $70-90
RDS PostgreSQL (db.t3.medium): $150-200
ElastiCache Redis (cache.t3.micro): $15-20
ALB: $20-25
CloudFront: $5-15
S3: $5-10
기타 (Secrets Manager, CloudWatch): $10-15

총 예상 비용: $275-375/월
```

### 비용 절약 팁
1. **Reserved Instances** 사용 (RDS 30-60% 절약)
2. **Spot Instances** 활용 (비중요 워크로드)
3. **CloudWatch Logs** 보존 기간 설정
4. **S3 Lifecycle Policy** 설정
5. **정기적인 비용 검토** (Cost Explorer)

## 🔄 운영 및 유지보수

### 정기 작업
```bash
# 주간: 로그 확인
aws logs filter-log-events \
  --log-group-name /ecs/resee-backend \
  --start-time $(date -d '7 days ago' +%s)000

# 월간: 비용 리포트
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '1 month ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost

# 분기: 보안 감사
aws config get-compliance-details-by-config-rule \
  --config-rule-name securityhub-*
```

### 백업 및 복구
```bash
# RDS 스냅샷 (자동 백업 활성화됨)
aws rds create-db-snapshot \
  --db-instance-identifier resee-production-db \
  --db-snapshot-identifier resee-manual-backup-$(date +%Y%m%d)

# 애플리케이션 코드 백업 (Git + ECR)
git tag v$(date +%Y%m%d)
git push origin --tags
```

### 장애 대응
1. **CloudWatch 알람** 확인
2. **ECS 서비스 상태** 점검
3. **애플리케이션 로그** 분석
4. **롤백 절차** (이전 태스크 정의로 복원)

## 📞 지원 및 문의

### 문제 해결
- AWS Support (Business/Enterprise)
- CloudFormation 스택 이벤트 확인
- ECS 서비스 이벤트 로그 검토

### 연락처
- 기술 문의: DevOps 팀
- 비상 연락처: On-call 엔지니어

---

**중요**: 이 문서는 프로덕션 환경 배포를 위한 가이드입니다. 테스트 환경에서 충분히 검증한 후 프로덕션에 적용하세요.