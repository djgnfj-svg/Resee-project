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

# Explicitly import backup_tasks module
app.autodiscover_tasks(['review'], related_name='backup_tasks')

# Beat schedule configuration
app.conf.beat_schedule = {
    'send-hourly-notifications': {
        'task': 'review.tasks.send_hourly_notifications',
        'schedule': crontab(minute=0),  # 매시간 정각
    },
    'backup-database': {
        'task': 'review.backup_tasks.backup_database',
        'schedule': crontab(hour=3, minute=0),  # 매일 새벽 3시
        'kwargs': {'environment': 'production'},
    },
}

app.conf.timezone = 'Asia/Seoul'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')