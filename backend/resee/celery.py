"""
Celery configuration for Resee project
"""
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resee.settings.development')

app = Celery('resee')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Beat schedule configuration
app.conf.beat_schedule = {
    'send-daily-review-reminders': {
        'task': 'review.tasks.send_daily_review_reminders',
        'schedule': crontab(hour=9, minute=0),  # 매일 오전 9시
    },
    'send-evening-review-reminders': {
        'task': 'review.tasks.send_evening_review_reminders',
        'schedule': crontab(hour=20, minute=0),  # 매일 오후 8시
    },
    'backup-database': {
        'task': 'review.backup_tasks.backup_database',
        'schedule': crontab(hour=3, minute=0),  # 매일 새벽 3시
        'kwargs': {'environment': os.environ.get('ENVIRONMENT', 'production')},
    },
}

app.conf.timezone = 'Asia/Seoul'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')