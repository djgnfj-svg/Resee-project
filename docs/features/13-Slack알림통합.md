# Slack 알림 통합

## 핵심 개념

**Slack Webhook 기반 실시간 시스템 알림**을 제공합니다.
헬스 체크, 백업, 결제, API 성능 등 9가지 이상의 알림 유형을 지원하며, 심각도에 따라 색상과 이모지가 자동으로 설정됩니다.

## 주요 기능

- **9가지 알림 유형**:
  - 일반 알림 (send_alert)
  - 에러 알림 (send_error_alert)
  - 헬스 체크 알림 (send_health_alert)
  - 결제 알림 (send_payment_alert)
  - Celery 큐 알림 (send_celery_alert)
  - API 성능 알림 (send_api_performance_alert)
  - 에러율 알림 (send_error_rate_alert)
  - 백업 성공/실패 알림
  - 디스크 용량 알림
- **심각도 레벨**:
  - error (빨강)
  - warning (노랑)
  - info (파랑)
  - success (초록)
- **알림 포맷**:
  - 제목, 메시지, 타임스탬프
  - 추가 필드 (key-value)
  - 이모지 자동 설정

## 동작 흐름

```
1. 시스템 이벤트 발생 (예: DB 연결 실패)
   ↓
2. slack_notifier.send_health_alert() 호출
   ↓
3. 심각도 레벨에 따라 색상/이모지 선택
   ↓
4. Slack 메시지 페이로드 생성
   ↓
5. Webhook URL로 POST 요청
   ↓
6. Slack 채널에 알림 표시
```

## 사용 예시

```python
from utils.slack_notifications import slack_notifier

# 헬스 체크 알림
slack_notifier.send_health_alert(
    service='database',
    status='down',
    details='Connection timeout after 30s'
)

# 백업 성공 알림
slack_notifier.send_alert(
    "Database backup completed\n"
    "• File: backup_20251020.sql.gz\n"
    "• Size: 15.32 MB",
    level='success',
    title='Backup Success'
)

# API 성능 알림
slack_notifier.send_api_performance_alert(
    endpoint='/api/review/submit/',
    response_time=3.5,
    threshold=2.0
)

# 에러 알림
try:
    # some code
except Exception as e:
    slack_notifier.send_error_alert(e, context='User registration')
```

## 알림 레벨 매핑

```python
# 색상
color_map = {
    'error': '#DC2626',    # red-600
    'warning': '#F59E0B',  # amber-500
    'info': '#3B82F6',     # blue-500
    'success': '#10B981'   # green-500
}

# 이모지
emoji_map = {
    'error': '🔴',
    'warning': '⚠️',
    'info': 'ℹ️',
    'success': '✅'
}
```

## 관련 파일

- `backend/utils/slack_notifications.py` - Slack 알림 서비스
- `backend/review/backup_tasks.py` - 백업 알림 사용
- `backend/accounts/health/health_views.py` - 헬스 체크 알림 사용

## 환경 변수

```bash
# .env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_DEFAULT_CHANNEL=#alerts  # 선택적
SLACK_BOT_NAME=Resee Alert Bot  # 선택적
```

## Slack 알림 예시

**데이터베이스 연결 실패**:
```
🔴 Health Check Alert: database

Service: database
Status: DOWN
Details: Connection timeout after 30s

Resee Monitoring • Oct 20, 2025 3:00 AM
```

**백업 성공**:
```
✅ Backup Success

Database backup completed successfully
• Environment: production
• File: resee_prod_production_20251020_030000.sql.gz
• Size: 15.32 MB

Resee Monitoring • Oct 20, 2025 3:05 AM
```

**API 성능 저하**:
```
⚠️ API Performance Alert

Endpoint: /api/review/submit/
Response Time: 3.50s
Threshold: 2.00s

Resee Monitoring • Oct 20, 2025 10:15 AM
```

## 알림 트리거 조건

1. **DB 연결 실패**: 헬스 체크 실패 시
2. **Redis 연결 실패**: Redis ping 실패 시
3. **디스크 용량 부족**: 80% 초과 시
4. **Celery 작업 실패**: 재시도 3회 후 실패 시
5. **백업 실패**: pg_dump 실패 시
6. **결제 실패**: 결제 승인 실패 시
7. **API 응답 지연**: 2초 초과 시
8. **에러율 급증**: 10개/분 초과 시
9. **Celery 큐 적체**: 100개 초과 시

## 비활성화

환경 변수에서 `SLACK_WEBHOOK_URL`을 설정하지 않으면 알림이 비활성화됩니다.
로그에 "Slack notifications are disabled" 메시지가 기록됩니다.
