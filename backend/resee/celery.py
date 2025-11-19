"""
Celery configuration for Resee project
"""
import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resee.settings.development')

app = Celery('resee')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Explicitly import tasks from subdirectories
app.autodiscover_tasks(['accounts.email'])

# Note: Using DatabaseScheduler (django-celery-beat) for dynamic task scheduling
# All periodic tasks are managed through Django admin or PeriodicTask model

# Static beat schedule for critical tasks
app.conf.beat_schedule = {
    'hourly-review-notifications': {
        'task': 'review.tasks.send_hourly_notifications',
        'schedule': crontab(minute=0, hour='*'),
    },
}

app.conf.timezone = 'Asia/Seoul'


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
