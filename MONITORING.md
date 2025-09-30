# 서버 모니터링 시스템 설정 가이드

## 개요

Resee 프로젝트의 서버 모니터링 시스템은 다음과 같은 구성 요소로 이루어져 있습니다:

- **내부 헬스체크 시스템**: Django 기반 헬스체크 API
- **중앙 로그 수집**: 로그 파일 기반 중앙집중 로깅
- **외부 모니터링**: Uptime Robot을 통한 24/7 가동시간 모니터링

## 1. 내부 헬스체크 시스템

### 1.1 헬스체크 엔드포인트

| 엔드포인트 | 설명 | 권한 |
|-----------|------|------|
| `/api/health/` | 기본 헬스체크 | 공개 |
| `/api/health/detailed/` | 상세 시스템 상태 | 공개 |
| `/api/health/ready/` | 준비 상태 체크 (K8s readiness) | 공개 |
| `/api/health/live/` | 생존 상태 체크 (K8s liveness) | 공개 |

### 1.2 모니터링 서비스

헬스체크 시스템은 다음 서비스들을 모니터링합니다:

- **PostgreSQL Database**: 연결 상태 및 응답 시간
- **Redis**: Celery 브로커 연결 상태
- **Local Memory Cache**: Django 캐시 시스템
- **Celery Workers**: 백그라운드 작업 처리 상태
- **Disk Space**: 디스크 사용량 (80% 경고, 90% 위험)
- **AI Service**: Anthropic API 설정 상태

### 1.3 응답 형태

```json
{
  "status": "healthy",
  "timestamp": 1696161234,
  "services": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5.23
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2.15,
      "url": "redis://***@redis:6379/0"
    },
    "disk": {
      "status": "healthy",
      "usage_percent": 65.4,
      "free_gb": 12.5
    },
    "celery": {
      "status": "healthy",
      "active_workers": 2
    }
  },
  "total_response_time_ms": 15.67
}
```

## 2. 중앙 로그 수집 시스템

### 2.1 로그 파일 구조

```
logs/
├── django.log          # 일반 Django 로그
├── django_error.log    # 에러 로그만
├── celery.log          # Celery 작업 로그
├── security.log        # 보안 관련 로그
└── *.log.1, *.log.2... # 로테이션된 파일들
```

### 2.2 로그 관리 API (관리자 전용)

| 엔드포인트 | 메소드 | 설명 |
|-----------|-------|------|
| `/api/accounts/logs/summary/` | GET | 로그 파일 요약 |
| `/api/accounts/logs/errors/` | GET | 최근 에러 로그 |
| `/api/accounts/logs/file/<filename>/` | GET | 특정 로그 파일 내용 |
| `/api/accounts/logs/cleanup/` | DELETE | 오래된 로그 파일 정리 |
| `/api/accounts/logs/analytics/` | GET | 로그 분석 정보 |

### 2.3 로그 로테이션

- **파일 크기**: 10MB 단위로 로테이션
- **보관 개수**: 5개 (일반), 10개 (보안)
- **자동 압축**: Django의 RotatingFileHandler 사용

### 2.4 로그 설정 관리

```bash
# 로그 디렉토리 초기화
docker-compose exec backend python manage.py setup_logging --create-dirs

# 로깅 시스템 테스트
docker-compose exec backend python manage.py setup_logging --test-logging

# 오래된 로그 정리
docker-compose exec backend python manage.py setup_logging --cleanup
```

## 3. Uptime Robot 설정

### 3.1 계정 설정

1. **Uptime Robot 가입**: https://uptimerobot.com
2. **무료 플랜**: 50개 모니터, 5분 간격 체크
3. **유료 플랜 권장**: 1분 간격, SMS 알림, 더 많은 모니터

### 3.2 모니터 설정

#### 3.2.1 기본 HTTP 모니터

- **Monitor Type**: HTTP(s)
- **URL**: `https://your-domain.com/api/health/`
- **Monitoring Interval**: 5분 (무료) / 1분 (유료)
- **Monitor Timeout**: 30초

#### 3.2.2 상세 헬스체크 모니터

- **Monitor Type**: HTTP(s)
- **URL**: `https://your-domain.com/api/health/detailed/`
- **Monitoring Interval**: 5분
- **Advanced Settings**:
  - **HTTP Status Code**: 200
  - **Keyword Monitoring**: `"status": "healthy"`

#### 3.2.3 Keyword 모니터링 설정

```json
# 모니터링할 키워드들
"should exist": ["status", "healthy"]
"should not exist": ["unhealthy", "degraded", "error"]
```

### 3.3 알림 채널 설정

#### 3.3.1 이메일 알림

- **Type**: Email
- **Email Address**: `admin@yourdomain.com`
- **When to send**:
  - Down
  - Up (문제 해결됨)

#### 3.3.2 슬랙 알림 (선택사항)

1. Slack에서 Incoming Webhook 생성
2. Uptime Robot에서 Webhook 알림 채널 추가
3. Webhook URL 설정

```
Webhook URL: https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
POST Value (or JSON):
{
  "text": "*monitorFriendlyName* is *alertTypeFriendlyName*",
  "username": "Uptime Robot"
}
```

### 3.4 모니터링 설정 예시

```
Monitor 1: 기본 헬스체크
- URL: https://resee.com/api/health/
- Interval: 1분
- Alert When: Down for 2 minutes

Monitor 2: 상세 헬스체크
- URL: https://resee.com/api/health/detailed/
- Interval: 5분
- Keyword: "status": "healthy"
- Alert When: Keyword not found for 5 minutes

Monitor 3: 메인페이지
- URL: https://resee.com/
- Interval: 5분
- Alert When: Down for 2 minutes
```

### 3.5 다운타임 리포트

Uptime Robot은 다음과 같은 리포트를 제공합니다:

- **일일 가동시간**: 지난 24시간 통계
- **월간 가동시간**: 월별 가동률 (99.9% 목표)
- **응답시간 통계**: 평균/최대/최소 응답시간
- **인시던트 로그**: 다운타임 발생 이력

## 4. 통합 모니터링 대시보드

### 4.1 모니터링 URL 통합

프로덕션 환경에서 다음 URL들을 통합 모니터링:

```
# 기본 서비스
https://resee.com/                    # 메인 서비스
https://resee.com/api/health/         # 헬스체크
https://resee.com/api/health/detailed/ # 상세 헬스체크

# 관리자 모니터링 (IP 제한 권장)
https://resee.com/api/accounts/logs/summary/  # 로그 요약
https://resee.com/admin/                      # Django Admin
```

### 4.2 통합 대시보드 구성

**Uptime Robot Public Status Page** 설정:
1. Uptime Robot 대시보드에서 Public Status Page 생성
2. 모니터링 중인 서비스들을 공개 상태 페이지에 추가
3. 사용자들이 실시간 서비스 상태를 확인할 수 있도록 설정

## 5. 장애 대응 프로세스

### 5.1 장애 감지 플로우

```
1. Uptime Robot이 장애 감지
   ↓
2. 즉시 알림 발송 (이메일/슬랙)
   ↓
3. 관리자가 헬스체크 API로 상세 진단
   ↓
4. 로그 분석 API로 원인 파악
   ↓
5. 문제 해결 후 복구 확인
```

### 5.2 장애 시나리오별 대응

#### Database 연결 실패
```bash
# 즉시 점검
docker-compose exec backend python manage.py dbshell

# 로그 확인
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  "https://resee.com/api/accounts/logs/errors/?hours=1"
```

#### Redis 연결 실패
```bash
# Redis 상태 확인
docker-compose exec redis redis-cli ping

# Celery 재시작
docker-compose restart celery celery-beat
```

#### 디스크 공간 부족
```bash
# 로그 정리
curl -X DELETE -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  "https://resee.com/api/accounts/logs/cleanup/?days=7"

# 수동 정리
docker system prune -f
```

## 6. 보안 고려사항

### 6.1 헬스체크 보안

- 기본 헬스체크는 공개 (로드밸런서용)
- 상세 헬스체크는 민감 정보 마스킹 적용
- 로그 관리 API는 관리자 권한 필수

### 6.2 모니터링 보안

- Uptime Robot IP를 방화벽에서 허용
- 알림 채널 설정 시 보안 토큰 사용
- 공개 상태 페이지에서 민감 정보 제외

### 6.3 로그 보안

- 로그 파일에 개인정보/비밀번호 기록 금지
- 로그 파일 권한: 644 (읽기 전용)
- 로그 백업 시 암호화 적용

## 7. 성능 최적화

### 7.1 헬스체크 최적화

- 헬스체크 응답시간 < 5초 유지
- DB 쿼리는 간단한 SELECT 1만 수행
- Redis 연결 타임아웃 3초로 제한

### 7.2 로그 최적화

- 로그 레벨 조정 (INFO 이상만 파일 저장)
- 불필요한 로그 제거 (DEBUG 레벨 비활성화)
- 로그 압축 활성화

## 8. 문제 해결

### 8.1 자주 발생하는 문제

**Q: 헬스체크가 간헐적으로 실패함**
A: 타임아웃 설정 확인, DB 연결 풀 크기 조정

**Q: 로그 파일이 생성되지 않음**
A: 로그 디렉토리 권한 및 경로 확인
```bash
docker-compose exec backend python manage.py setup_logging --create-dirs
```

**Q: Celery 워커가 inactive로 표시됨**
A: Celery 서비스 재시작
```bash
docker-compose restart celery celery-beat
```

### 8.2 디버깅 명령어

```bash
# 헬스체크 테스트
curl http://localhost/api/health/detailed/

# 로그 확인
docker-compose exec backend ls -la /app/../logs/

# 서비스 상태 확인
docker-compose ps
```

---

**주의사항**:
- 모니터링 설정 후에는 반드시 실제 장애 상황을 시뮬레이션해서 알림이 정상 작동하는지 확인하세요.
- 알림 빈도가 너무 높지 않도록 조정하여 알림 피로를 방지하세요.
- 정기적으로 모니터링 설정을 검토하고 업데이트하세요.