# ECS Auto Rollback 배포 설정 (Railway-style)

## 📌 개요

AWS ECS에 Railway처럼 자동 롤백이 되는 무중단 배포 설정을 추가했습니다.

**핵심 기능:**
- ✅ New 컨테이너 Health Check 실패 시 자동 롤백
- ✅ Old/New 동시 실행으로 무중단 배포
- ✅ Circuit Breaker를 통한 자동 장애 감지

---

## 🔧 설정된 내용

### 1. Deployment Circuit Breaker 추가

**변경 파일:** `.github/workflows/deploy.yml.disabled`

```yaml
# Before (자동 롤백 없음)
aws ecs update-service \
  --force-new-deployment

# After (자동 롤백 활성화)
aws ecs update-service \
  --deployment-configuration "\
    minimumHealthyPercent=50,\
    maximumPercent=200,\
    deploymentCircuitBreaker={enable=true,rollback=true}" \
  --force-new-deployment
```

**서비스별 설정:**

| 서비스 | minimumHealthyPercent | maximumPercent | 설명 |
|--------|----------------------|----------------|------|
| **Backend** | 50% | 200% | 최소 절반 유지, 최대 2배 실행 |
| **Celery Worker** | 50% | 200% | 동일 (무중단 워커 교체) |
| **Celery Beat** | 0% | 100% | 단일 인스턴스 (동시 실행 방지) |

### 2. Health Check 설정 (Task Definition 추가 필요)

**파일:** `scripts/task-definition-healthcheck.json`

```json
{
  "healthCheck": {
    "command": [
      "CMD-SHELL",
      "curl -f http://localhost:8000/api/health/ || exit 1"
    ],
    "interval": 30,
    "timeout": 5,
    "retries": 3,
    "startPeriod": 60
  }
}
```

**동작:**
- 30초마다 `/api/health/` 체크
- 3번 연속 실패 시 unhealthy 판정
- Circuit Breaker가 감지하여 자동 롤백

### 3. 배포 검증 로직 강화

**개선 내용:**
- Circuit Breaker 상태 확인
- Health Check 3회 재시도
- Rollback 이벤트 감지

---

## 📊 동작 방식 (Before vs After)

### Before (위험한 배포)

```
배포 시작
  ↓
Old 즉시 종료 ❌
  ↓
New 시작
  ↓
New 실패? → 서비스 다운! ❌
```

### After (안전한 배포)

```
배포 시작
  ↓
Old 50% 유지 ✅
  ↓
New 시작 (최대 200%)
  ↓
Health Check 실행
  ↓
┌─────────────────┐
│ Health Pass?    │
└─────────────────┘
  ↓ YES      ↓ NO
트래픽 전환   자동 롤백 ✅
  ↓          ↓
Old 종료    Old 유지
```

---

## 🚀 적용 방법

### Step 1: ECS Service에 Circuit Breaker 설정 (원타임)

**Option A: AWS CLI로 영구 설정**
```bash
# Backend Service
aws ecs update-service \
  --cluster resee-cluster \
  --service resee-backend-service \
  --deployment-configuration \
    minimumHealthyPercent=50,\
    maximumPercent=200,\
    deploymentCircuitBreaker={enable=true,rollback=true} \
  --region ap-northeast-2

# Celery Worker Service
aws ecs update-service \
  --cluster resee-cluster \
  --service resee-celery-worker-service \
  --deployment-configuration \
    minimumHealthyPercent=50,\
    maximumPercent=200,\
    deploymentCircuitBreaker={enable=true,rollback=true} \
  --region ap-northeast-2

# Celery Beat Service (단일 인스턴스)
aws ecs update-service \
  --cluster resee-cluster \
  --service resee-celery-beat-service \
  --deployment-configuration \
    minimumHealthyPercent=0,\
    maximumPercent=100,\
    deploymentCircuitBreaker={enable=true,rollback=true} \
  --region ap-northeast-2
```

**Option B: AWS Console에서 설정**
1. ECS > Clusters > `resee-cluster`
2. Services > `resee-backend-service` > Update Service
3. Deployment configuration:
   - Minimum healthy percent: `50`
   - Maximum percent: `200`
   - Enable deployment circuit breaker: ✅
   - Enable rollback on failure: ✅

### Step 2: Task Definition에 Health Check 추가

**방법 1: AWS Console**
1. ECS > Task Definitions > `resee-backend-task`
2. Create new revision
3. Container definitions > `resee-backend` > Edit
4. Health Check 섹션:
   - Command: `CMD-SHELL,curl -f http://localhost:8000/api/health/ || exit 1`
   - Interval: `30`
   - Timeout: `5`
   - Start period: `60`
   - Retries: `3`

**방법 2: AWS CLI (추천)**
```bash
# 1. 현재 Task Definition 가져오기
aws ecs describe-task-definition \
  --task-definition resee-backend-task \
  --region ap-northeast-2 > current-task-def.json

# 2. Health Check 추가 (jq 사용)
cat current-task-def.json | jq '.taskDefinition |
  .containerDefinitions[0].healthCheck = {
    "command": ["CMD-SHELL", "curl -f http://localhost:8000/api/health/ || exit 1"],
    "interval": 30,
    "timeout": 5,
    "retries": 3,
    "startPeriod": 60
  } |
  del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)' \
  > new-task-def.json

# 3. 새 Task Definition 등록
aws ecs register-task-definition \
  --cli-input-json file://new-task-def.json \
  --region ap-northeast-2
```

**방법 3: 템플릿 사용**
```bash
# scripts/task-definition-healthcheck.json 참고
cp scripts/task-definition-healthcheck.json my-task-def.json
# ... 수정 후 등록
aws ecs register-task-definition \
  --cli-input-json file://my-task-def.json
```

### Step 3: GitHub Actions Workflow 활성화 (선택사항)

```bash
# 레거시 ECS 배포를 사용하려면 활성화
mv .github/workflows/deploy.yml.disabled \
   .github/workflows/deploy.yml
```

---

## 🧪 테스트 방법

### 1. 정상 배포 테스트

```bash
# 1. Deploy 실행 (GitHub Actions 또는 AWS CLI)
git push origin main

# 2. ECS 콘솔에서 확인
# Events 탭에서 다음 메시지 확인:
#   "service resee-backend-service has reached a steady state"

# 3. Health Check 확인
curl https://reseeall.com/api/health/
# 200 OK 확인
```

### 2. 자동 롤백 테스트

**시나리오: 일부러 Health Check 실패시키기**

```bash
# 1. Task Definition에 잘못된 Health Check 추가
{
  "healthCheck": {
    "command": ["CMD-SHELL", "exit 1"],  # 무조건 실패
    "retries": 2
  }
}

# 2. 배포 실행
aws ecs update-service \
  --cluster resee-cluster \
  --service resee-backend-service \
  --task-definition resee-backend-task:LATEST \
  --force-new-deployment

# 3. ECS Events 모니터링
watch -n 5 'aws ecs describe-services \
  --cluster resee-cluster \
  --service resee-backend-service \
  --query "services[0].events[0:5]"'

# 예상 결과:
# - "service resee-backend-service deployment circuit breaker triggered"
# - "service resee-backend-service has begun draining connections on 1 tasks"
# - "service resee-backend-service has started 1 tasks (OLD VERSION)"
# → 자동으로 이전 버전으로 롤백됨! ✅
```

---

## 📈 모니터링

### CloudWatch Logs 확인

```bash
# Circuit Breaker 이벤트 검색
aws logs filter-log-events \
  --log-group-name /ecs/resee-backend \
  --filter-pattern "circuit breaker" \
  --region ap-northeast-2
```

### ECS Service Events

```bash
# 최근 배포 이벤트 확인
aws ecs describe-services \
  --cluster resee-cluster \
  --service resee-backend-service \
  --region ap-northeast-2 \
  --query 'services[0].events[0:10]'
```

### Health Check 상태

```bash
# Running Tasks의 Health Check 상태
aws ecs describe-tasks \
  --cluster resee-cluster \
  --tasks $(aws ecs list-tasks \
    --cluster resee-cluster \
    --service-name resee-backend-service \
    --query 'taskArns[0]' \
    --output text) \
  --query 'tasks[0].healthStatus'
```

---

## ⚠️ 주의사항

### 1. Celery Beat는 단일 인스턴스
```yaml
minimumHealthyPercent=0  # Old 종료 후 New 시작
maximumPercent=100       # 동시 실행 방지
```
- Beat는 중복 실행 시 스케줄 충돌 발생
- 짧은 다운타임 허용 (일반적으로 <30초)

### 2. Health Check Timeout 고려
```json
"startPeriod": 60  // Django 초기화 시간 고려
```
- Django 앱 시작에 시간이 걸릴 수 있음
- `startPeriod` 동안은 Health Check 실패해도 무시

### 3. ALB Health Check와 별개
- Task Definition Health Check: ECS가 컨테이너 상태 체크
- ALB Target Group Health Check: 로드밸런서가 트래픽 라우팅 결정
- 둘 다 설정하는 것이 베스트 프랙티스

### 4. 첫 배포 시 확인 사항
```bash
# Service 설정 확인
aws ecs describe-services \
  --cluster resee-cluster \
  --service resee-backend-service \
  --query 'services[0].deploymentConfiguration'

# 예상 출력:
{
  "deploymentCircuitBreaker": {
    "enable": true,
    "rollback": true
  },
  "minimumHealthyPercent": 50,
  "maximumPercent": 200
}
```

---

## 🎯 예상 질문 (면접 대비)

### Q1. Circuit Breaker는 어떻게 실패를 감지하나?
**A:**
1. Task의 Health Check 실패 모니터링
2. Essential 컨테이너 종료 감지
3. 연속 실패 횟수가 임계값 초과 시 트리거

### Q2. minimumHealthyPercent=50은 어떻게 동작하나?
**A:**
- 현재 2개 태스크 실행 중
- 배포 시작: 최소 1개(50%) 유지 필수
- New 1개 시작 → Old 1개 종료
- New 1개 더 시작 → Old 1개 더 종료
- 결과: 항상 최소 1개 이상 실행 (무중단)

### Q3. Railway vs ECS Circuit Breaker 차이는?
**A:**

| 항목 | Railway | ECS Circuit Breaker |
|------|---------|---------------------|
| **트리거** | Health Check 실패 | Health Check + 컨테이너 크래시 |
| **롤백 속도** | 즉시 (~10초) | 느림 (~2-3분, retries 대기) |
| **설정 간편성** | 자동 | 수동 설정 필요 |
| **비용** | 배포 시간 과금 | 무료 (AWS 기본 기능) |

### Q4. Health Check 없으면 Circuit Breaker가 안 되나?
**A:**
- Health Check 없으면 **컨테이너 크래시만** 감지
- 예: Django가 실행 중이지만 500 에러 → 감지 못 함
- **반드시 Health Check 설정 필요**

### Q5. 프로덕션 적용 전 체크리스트는?
**A:**
1. ✅ Task Definition에 Health Check 추가
2. ✅ Service에 Circuit Breaker 설정
3. ✅ 테스트 환경에서 롤백 테스트
4. ✅ CloudWatch Alarms 설정 (Circuit Breaker 트리거 시 알림)
5. ✅ 배포 시간대 계획 (트래픽 낮은 시간)

---

## 📚 참고 자료

- [AWS ECS Circuit Breaker 공식 문서](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html)
- [ECS Health Check 설정](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_HealthCheck.html)
- [Rolling Update 전략](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-ecs.html)

---

## 🔄 롤백 방법 (긴급 시)

### 자동 롤백 실패 시 수동 롤백

```bash
# 1. 이전 Task Definition 버전 확인
aws ecs list-task-definitions \
  --family-prefix resee-backend-task \
  --sort DESC

# 2. 이전 버전으로 롤백
aws ecs update-service \
  --cluster resee-cluster \
  --service resee-backend-service \
  --task-definition resee-backend-task:PREVIOUS_REVISION \
  --force-new-deployment

# 3. 안정화 대기
aws ecs wait services-stable \
  --cluster resee-cluster \
  --services resee-backend-service
```

---

**마이그레이션 완료 체크리스트:**
- [ ] Step 1: Circuit Breaker 설정 (AWS CLI/Console)
- [ ] Step 2: Health Check 추가 (Task Definition)
- [ ] Step 3: 테스트 환경에서 검증
- [ ] Step 4: 프로덕션 배포
- [ ] Step 5: 모니터링 설정 (CloudWatch Alarms)
