from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
import secrets
from datetime import timedelta


class UserManager(BaseUserManager):
    """Custom user manager for email-only authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with email and password"""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with email and password"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_email_verified', True)  # Superuser는 자동으로 인증됨
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


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
    
    # 이메일 인증 관련 필드
    is_email_verified = models.BooleanField(
        default=False,
        help_text='Whether the email address has been verified'
    )
    email_verification_token = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Token for email verification'
    )
    email_verification_sent_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='When the verification email was sent'
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # No additional required fields for email-only auth
    
    def __str__(self):
        return self.email
    
    def generate_email_verification_token(self):
        """Generate a unique token for email verification"""
        # 32자 길이의 URL-safe 토큰 생성
        token = secrets.token_urlsafe(32)
        self.email_verification_token = token
        self.email_verification_sent_at = timezone.now()
        self.save()
        return token
    
    def verify_email(self, token):
        """Verify email with the given token"""
        if not self.email_verification_token:
            return False
        
        # 토큰 일치 확인
        if self.email_verification_token != token:
            return False
        
        # 토큰 유효기간 확인 (24시간)
        if self.email_verification_sent_at:
            expiry_time = self.email_verification_sent_at + timedelta(hours=24)
            if timezone.now() > expiry_time:
                return False
        
        # 이메일 인증 완료
        self.is_email_verified = True
        self.email_verification_token = None
        self.email_verification_sent_at = None
        self.save()
        return True
    
    def can_resend_verification_email(self):
        """Check if verification email can be resent (5분 간격 제한)"""
        if not self.email_verification_sent_at:
            return True
        
        time_since_sent = timezone.now() - self.email_verification_sent_at
        return time_since_sent > timedelta(minutes=5)