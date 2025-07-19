from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User model with email-only authentication"""
    email = models.EmailField(unique=True)
    username = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text='Optional username field'
    )
    timezone = models.CharField(
        max_length=50,
        default='Asia/Seoul',
        help_text='User timezone for scheduling'
    )
    notification_enabled = models.BooleanField(
        default=True,
        help_text='Whether to send review notifications'
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Required for createsuperuser command
    
    def __str__(self):
        return self.email