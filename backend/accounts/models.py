from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User model"""
    email = models.EmailField(unique=True)
    timezone = models.CharField(
        max_length=50,
        default='Asia/Seoul',
        help_text='User timezone for scheduling'
    )
    notification_enabled = models.BooleanField(
        default=True,
        help_text='Whether to send review notifications'
    )
    
    def __str__(self):
        return self.username