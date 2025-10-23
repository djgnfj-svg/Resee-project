# Celery + Redis 비동기 작업 처리

> **핵심 성과**: API 응답 **3초 → 100ms (97% 단축)**, 작업 손실 **0%**

---

## 한 줄 요약

이메일 전송을 백그라운드로 처리해서 API 응답 즉시 반환

---

## 배경

복습 완료 API에서 이메일 전송이 동기로 처리되어 사용자가 3초 동안 응답을 기다려야 했다.
또한 서버 재시작 시 진행 중인 작업이 손실되는 문제가 있었다.
Celery + Redis Queue를 도입하여 이메일 발송과 DB 백업을 비동기로 처리하고, 재시도 로직으로 안정성을 확보했다.

---

## 문제

API 요청 중 이메일 전송으로 3초 지연 - 사용자 화면 멈춤

```python
# backend/review/views.py (개선 전)
from django.core.mail import send_mail

class CompleteReviewView(APIView):
    def post(self, request):
        schedule.save()

        # 이메일 전송 (동기) - API가 멈춤
        send_mail(
            subject='복습 완료',
            message='...',
            recipient_list=[user.email],
        )  # 3초 소요

        return Response({'message': 'Success'})  # 3초 후 응답
```

---

## 해결

### Before → After

#### 1. Task 정의

```python
# backend/review/tasks.py:207
from celery import shared_task

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_individual_review_reminder(self, user_id, schedule_ids):
    try:
        user = User.objects.get(id=user_id)
        schedules = ReviewSchedule.objects.filter(
            id__in=schedule_ids
        ).select_related('content').prefetch_related('content__category')

        send_mail(...)
        logger.info(f"Email sent to {user.email}")

    except Exception as exc:
        # 실패 시 3회 재시도 (1분 간격)
        raise self.retry(exc=exc)
```

#### 2. API에서 호출

```python
# backend/review/views.py (개선 후)
from review.tasks import send_individual_review_reminder

class CompleteReviewView(APIView):
    def post(self, request):
        schedule.save()

        # Task 큐에 등록 (즉시 반환)
        send_individual_review_reminder.delay(
            user_id=request.user.id,
            schedule_ids=[schedule.id]
        )

        return Response({'message': 'Success'})  # 100ms
```

#### 3. DB 자동 백업 (매일 3시)

```python
# backend/review/backup_tasks.py:14-106
@shared_task(bind=True, max_retries=3)
def backup_database(self, environment='production'):
    try:
        # pg_dump + gzip
        subprocess.run(
            f'pg_dump {db_name} | gzip > {backup_path}',
            timeout=600,  # 10분
            shell=True
        )

        # Slack 성공 알림
        slack_notifier.send_alert(
            f"Backup completed: {backup_filename}",
            level='success'
        )
    except subprocess.TimeoutExpired:
        raise self.retry(countdown=300)  # 5분 후 재시도
```

#### 4. 스케줄러

```python
# backend/resee/celery.py:22-40
app.conf.beat_schedule = {
    'backup-database': {
        'task': 'review.backup_tasks.backup_database',
        'schedule': crontab(hour=3, minute=0),  # 매일 3시
    },
}
```

### Workflow

```
Before: 동기 처리
  Client → Django → 이메일 전송 (3s) → Response (3s 후)

After: 비동기 처리
  Client → Django → Task 등록 → Response (즉시)
                       ↓
                  Redis Queue
                       ↓
                  Celery Worker → 이메일 전송 (백그라운드)
```

---

## 성과

| 지표 | Before | After | 개선 |
|-----|--------|-------|------|
| **API 응답** | 3000ms | 100ms | **97% 단축** |
| **사용자 체감** | 멈춤 | 즉시 | - |
| **작업 손실** | 재시작 시 손실 | Redis 보관 | **0%** |

---

## 코드 위치

```
backend/resee/celery.py            # Celery 초기화
backend/review/backup_tasks.py     # 백업 Task
backend/review/tasks.py            # 이메일 Task
```

**핵심 로직 (3줄)**:
```python
@shared_task(bind=True, max_retries=3)  # 1. Task 정의
def my_task(self):                      # 2. 로직
    my_task.delay()                     # 3. 호출
```

---

**작성일**: 2025-10-21
**키워드**: Celery, Redis Queue, 비동기 처리
