# Phase 2: 운영 인프라 완성 - 설정 가이드

## 개요
Phase 2에서 구현된 운영 인프라(Sentry, JSON 로깅, 자동 백업, Slack 알림)의 설정 및 사용 방법을 안내합니다.

---

## 1. Sentry 에러 추적 설정

### 1.1 Sentry 계정 생성
1. [Sentry.io](https://sentry.io) 접속
2. 무료 계정 생성 (월 5,000 이벤트 무료)
3. 새 프로젝트 생성:
   - **Backend**: Django 선택
   - **Frontend**: React 선택

### 1.2 DSN 발급
프로젝트 생성 후 DSN(Data Source Name) 복사:
```
https://examplePublicKey@o0.ingest.sentry.io/0
```

### 1.3 환경 변수 설정

**.env.prod 파일에 추가**:
```bash
# Backend Sentry
SENTRY_DSN=https://your-backend-dsn@sentry.io/project-id

# Frontend Sentry
REACT_APP_SENTRY_DSN=https://your-frontend-dsn@sentry.io/project-id
```

### 1.4 적용 및 테스트

**서비스 재시작**:
```bash
docker-compose down
docker-compose -f docker-compose.prod.yml up -d
```

**테스트 에러 발생**:
```bash
# Backend 테스트
docker-compose exec backend python manage.py shell
>>> from utils.slack_notifications import send_error_alert
>>> send_error_alert(Exception("Test error"), "Sentry test")

# Frontend 테스트 (브라우저 콘솔)
Sentry.captureException(new Error("Test error"));
```

Sentry 대시보드에서 에러 확인:
- **Issues** → 에러 목록
- **Performance** → 성능 메트릭

### 1.5 Slack 통합 (선택사항)

Sentry에서 Slack 알림 설정:
1. **Settings** → **Integrations** → **Slack**
2. Slack workspace 연결
3. 알림 규칙 설정:
   - Critical errors: 즉시 알림
   - Other errors: 1시간마다 요약

---

## 2. JSON 로깅

### 2.1 현재 설정

JSON 로거가 이미 설정되어 있습니다 (`backend/resee/settings/base.py`):

```python
LOGGING = {
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(funcName)s %(lineno)d %(message)s'
        },
    },
    'handlers': {
        'file_django': {
            'formatter': 'file_format',  # JSON으로 변경 가능
            # ...
        },
    },
}
```

### 2.2 JSON 로깅 활성화 (선택사항)

**base.py 수정**:
```python
'file_django': {
    'level': 'INFO',
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
    'maxBytes': 10 * 1024 * 1024,  # 10MB
    'backupCount': 5,
    'formatter': 'json',  # file_format → json으로 변경
},
```

### 2.3 로그 확인 및 분석

**로그 파일 위치**:
```bash
backend/logs/
├── django.log        # 일반 로그
├── django_error.log  # 에러 로그
├── celery.log        # Celery 로그
└── security.log      # 보안 로그
```

**jq를 사용한 JSON 로그 분석**:
```bash
# jq 설치 (Ubuntu)
sudo apt-get install jq

# 에러 로그만 필터링
cat backend/logs/django.log | jq 'select(.levelname == "ERROR")'

# 특정 시간대 로그 필터링
cat backend/logs/django.log | jq 'select(.asctime > "2025-01-15T10:00:00")'

# 에러 카운트
cat backend/logs/django.log | jq -r '.levelname' | sort | uniq -c
```

---

## 3. Celery 자동 백업 시스템 ✅ **완성 및 테스트됨** (2025-10-15)

### 3.1 시스템 특징

**Celery Beat 기반 백업**:
- **스케줄**: 매일 새벽 3시 자동 실행
- **방식**: pg_dump + gzip 압축
- **위치**: `/tmp/` (컨테이너 내부)
- **알림**: Slack 성공/실패 알림
- **재시도**: 실패 시 3회 재시도 (5분 간격)

**백업 파일 형식**:
```
{database}_{environment}_{timestamp}.sql.gz
예: resee_dev_development_20251015_121644.sql.gz
```

### 3.2 백업 상태 확인

**Celery Beat 로그**:
```bash
docker-compose logs celery-beat | grep backup
```

**최근 백업 파일 확인**:
```bash
docker-compose exec backend ls -lh /tmp/*.sql.gz
```

**백업 무결성 검증**:
```bash
docker-compose exec backend gzip -t /tmp/resee_*.sql.gz && echo "✅ 백업 파일 유효"
```

### 3.3 수동 백업 실행

**Django shell에서 실행**:
```bash
docker-compose exec backend python manage.py shell
```

```python
from review.backup_tasks import backup_database

# Development 백업
result = backup_database('development')
print(result)

# Production 백업
result = backup_database('production')
print(result)
```

**결과 예시**:
```python
{
    'status': 'success',
    'filename': 'resee_dev_development_20251015_121644.sql.gz',
    'size_mb': 0.02
}
```

### 3.4 백업 스케줄 변경

**`backend/resee/celery.py` 수정**:
```python
app.conf.beat_schedule = {
    'backup-database': {
        'task': 'review.backup_tasks.backup_database',
        'schedule': crontab(hour=3, minute=0),  # 시간 변경
        'kwargs': {'environment': 'production'},
    },
}
```

**적용**:
```bash
docker-compose restart celery-beat
```

### 3.5 대체 방법: Shell 스크립트 백업

수동 백업 스크립트도 여전히 사용 가능합니다:

```bash
# Development 백업
bash scripts/backup_db.sh development

# Production 백업
bash scripts/backup_db.sh production
```

**백업 복구**:
```bash
# 최신 백업 복구
bash scripts/restore_db.sh

# 특정 백업 파일 복구
bash scripts/restore_db.sh backups/resee_production_20250115_030000.sql.gz
```

---

## 4. Slack 알림 시스템 ✅ **설정 완료 및 테스트됨** (2025-10-15)

### 4.1 Slack Webhook 설정

1. **Slack Workspace 설정**:
   - Slack workspace에 로그인
   - **Apps** → **Incoming Webhooks** 검색
   - **Add to Slack** 클릭

2. **채널 선택**:
   - 알림을 받을 채널 선택 (예: `#alerts`)
   - **Webhook URL** 복사

3. **환경 변수 설정** (`.env.prod`):
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_DEFAULT_CHANNEL=#alerts
SLACK_BOT_NAME=Resee Alert Bot
```

### 4.2 알림 트리거

자동으로 다음 상황에서 알림이 전송됩니다:

**시스템 헬스**:
- 🔴 Database 연결 실패
- 🔴 Redis 연결 실패
- ⚠️ Disk 사용량 > 80%
- 🔴 Disk 사용량 > 90%
- 🔴 Celery worker 없음

**백업**:
- ✅ 백업 성공 (파일명, 크기, 환경)
- 🔴 백업 실패
- 🔴 백업 무결성 검증 실패
- ⚠️ S3 업로드 실패

**결제** (구현됨, 임계값 설정 시 활성화):
- 🔴 결제 실패 > 10건/시간
- 🔴 환불 급증

**API 성능** (구현됨, 활성화 필요):
- ⚠️ API 응답 시간 > 2초 (p95)
- 🔴 에러율 > 5% (1시간 기준)

**Celery 큐** (구현됨, 활성화 필요):
- ⚠️ 큐 길이 > 100

### 4.3 알림 테스트

**Slack 알림 테스트**:
```bash
docker-compose exec backend python manage.py shell
```

```python
from utils.slack_notifications import slack_notifier

# 기본 알림 테스트
slack_notifier.send_alert("테스트 알림입니다", level='info', title='테스트')

# 에러 알림 테스트
slack_notifier.send_error_alert(Exception("테스트 에러"), context="Slack 테스트")

# 헬스 알림 테스트
slack_notifier.send_health_alert('database', 'degraded', 'Connection timeout')

# 결제 알림 테스트
slack_notifier.send_payment_alert('failure_spike', 15, {'time_window': '1 hour'})
```

### 4.4 알림 임계값 조정

**backend/utils/monitoring.py**:
```python
class MetricsMonitor:
    # 임계값 수정
    ERROR_RATE_THRESHOLD = 5.0  # 5% → 원하는 값으로 변경
    PAYMENT_FAILURE_THRESHOLD = 10  # 10건 → 원하는 값으로 변경
    CELERY_QUEUE_THRESHOLD = 100  # 100개 → 원하는 값으로 변경
    API_RESPONSE_THRESHOLD = 2.0  # 2초 → 원하는 값으로 변경
```

### 4.5 알림 Throttling

동일한 알림이 10분 간격으로만 전송됩니다 (스팸 방지).

**throttling 시간 조정** (`backend/utils/monitoring.py`):
```python
ALERT_THROTTLE_SECONDS = 600  # 10분 → 원하는 값으로 변경
```

---

## 5. 모니터링 대시보드

### 5.1 Health Check 엔드포인트

**기본 헬스체크**:
```bash
curl http://localhost/api/health/
```

**상세 헬스체크**:
```bash
curl http://localhost/api/health/detailed/
```

**응답 예시**:
```json
{
  "status": "healthy",
  "timestamp": 1705305600,
  "services": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5.23
    },
    "cache": {
      "status": "healthy",
      "response_time_ms": 1.12
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2.45
    },
    "disk": {
      "status": "healthy",
      "usage_percent": 65.43,
      "free_gb": 150.23
    },
    "celery": {
      "status": "healthy",
      "active_workers": 1
    }
  }
}
```

### 5.2 메트릭 요약

```bash
docker-compose exec backend python manage.py shell
```

```python
from utils.monitoring import get_metrics_summary

summary = get_metrics_summary()
print(summary)
```

---

## 6. 트러블슈팅

### 6.1 Sentry 에러가 전송되지 않을 때

1. **DSN 확인**:
```bash
docker-compose exec backend python -c "from django.conf import settings; print(settings.SENTRY_DSN)"
```

2. **네트워크 확인**:
```bash
curl https://sentry.io
```

3. **테스트 에러 발생**:
```bash
docker-compose exec backend python manage.py shell
>>> import sentry_sdk
>>> sentry_sdk.capture_exception(Exception("Test"))
```

### 6.2 Slack 알림이 전송되지 않을 때

1. **Webhook URL 확인**:
```bash
echo $SLACK_WEBHOOK_URL
```

2. **수동 테스트**:
```bash
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text": "Test message"}'
```

3. **로그 확인**:
```bash
grep "Slack" backend/logs/django.log
```

### 6.3 백업 실패 시

**Celery 백업 문제**:

1. **Celery Beat 상태 확인**:
```bash
docker-compose ps celery-beat
docker-compose logs celery-beat | tail -30
```

2. **Celery worker 상태**:
```bash
docker-compose ps celery
docker-compose logs celery | grep backup
```

3. **PostgreSQL 연결**:
```bash
docker-compose exec backend python manage.py dbshell
# 또는
docker-compose exec postgres psql -U postgres -l
```

4. **수동 백업 테스트**:
```bash
docker-compose exec backend python manage.py shell -c "from review.backup_tasks import backup_database; backup_database('development')"
```

5. **백업 파일 위치 확인**:
```bash
docker-compose exec backend ls -lh /tmp/*.sql.gz
```

**Shell 스크립트 백업 문제**:

1. **권한 확인**:
```bash
ls -la backups/
chmod +x scripts/backup_db.sh
```

2. **디스크 공간**:
```bash
df -h
```

### 6.4 Celery Beat가 실행되지 않을 때

1. **Celery Beat 컨테이너 시작**:
```bash
docker-compose up -d celery-beat
docker-compose logs celery-beat
```

2. **스케줄 확인**:
```bash
docker-compose exec backend python -c "from resee.celery import app; print(app.conf.beat_schedule)"
```

3. **Redis 연결 확인**:
```bash
docker-compose exec backend python -c "import redis; r = redis.from_url('redis://redis:6379/0'); print(r.ping())"
```

4. **환경 변수 확인**:
```bash
docker-compose exec backend env | grep REDIS
```

---

## 7. 다음 단계

Phase 2 완료 (2025-10-15):
- ✅ 로깅 시스템 완성 (JSON 포맷터 지원)
- ✅ Celery 자동 백업 시스템 구축 (매일 새벽 3시)
- ✅ Slack 알림 통합 (테스트 완료)

**Phase 3 (최적화 & 안정성)**로 진행:
- 프론트엔드 최적화 (React.lazy, 코드 스플리팅)
- 부하 테스트
- 보안 감사
- E2E 테스트

자세한 내용은 [ROADMAP.md](../ROADMAP.md) 참조

---

## 참고 자료

- [Sentry 공식 문서](https://docs.sentry.io/)
- [Python JSON Logger](https://github.com/madzak/python-json-logger)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [PostgreSQL Backup/Restore](https://www.postgresql.org/docs/current/backup.html)
