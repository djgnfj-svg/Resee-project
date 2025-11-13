import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.crypto import get_random_string

from resee.models import TimestampMixin

# Legal models removed - using static pages in frontend instead


class UserManager(BaseUserManager):
    """Custom user manager for email-only authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_email_verified', True)  # Superuser는 자동으로 인증됨
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model with email-only authentication."""
    email = models.EmailField(unique=True)
    username = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text='Optional username field'
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
    
    # 학습 목표 설정
    weekly_goal = models.IntegerField(
        default=7,
        help_text='주간 복습 목표 횟수'
    )

    # 약관 동의 관련 필드
    terms_agreed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='이용약관 동의 일시'
    )
    privacy_agreed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='개인정보처리방침 동의 일시'
    )


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # No additional required fields for email-only auth
    
    objects = UserManager()
    
    def __str__(self):
        return self.email
    
    def generate_email_verification_token(self):
        """Generate a unique token for email verification.

        Delegates to EmailVerificationService.
        """
        from .email.verification_service import EmailVerificationService
        service = EmailVerificationService(self)
        return service.generate_verification_token()

    def verify_email(self, token):
        """Verify email with the given token.

        Delegates to EmailVerificationService.
        """
        from .email.verification_service import EmailVerificationService
        service = EmailVerificationService(self)
        success, _ = service.verify_email(token)
        return success

    def can_resend_verification_email(self):
        """Check if verification email can be resent.

        Delegates to EmailVerificationService.
        """
        from .email.verification_service import EmailVerificationService
        service = EmailVerificationService(self)
        can_resend, _ = service.can_resend_verification()
        return can_resend
    


class SubscriptionTier(models.TextChoices):
    """Subscription tier choices with Ebbinghaus-optimized intervals"""
    FREE = 'free', 'Free (3일)'
    BASIC = 'basic', 'Basic (90일)'
    PRO = 'pro', 'Pro (180일)'


class BillingCycle(models.TextChoices):
    """Billing cycle options"""
    MONTHLY = 'monthly', '월간'
    YEARLY = 'yearly', '연간'


class Subscription(TimestampMixin):
    """User subscription model"""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    tier = models.CharField(
        max_length=20,
        choices=SubscriptionTier.choices,
        default=SubscriptionTier.FREE,
        help_text='Subscription tier'
    )
    max_interval_days = models.IntegerField(
        default=3,
        help_text='Maximum review interval in days'
    )
    start_date = models.DateTimeField(
        auto_now_add=True,
        help_text='Subscription start date'
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Subscription end date (null for unlimited)'
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Amount paid for subscription'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether the subscription is active'
    )
    auto_renewal = models.BooleanField(
        default=True,
        help_text='Whether to auto-renew subscription'
    )
    next_billing_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Next automatic billing date'
    )
    payment_method = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='Payment method identifier (e.g., CARD-1234)'
    )
    billing_cycle = models.CharField(
        max_length=20,
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
        help_text='Billing cycle frequency'
    )
    next_billing_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Next billing amount'
    )
    
    class Meta:
        db_table = 'accounts_subscription'
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
    
    def __str__(self):
        return f"{self.user.email} - {self.get_tier_display()}"
    
    def is_expired(self):
        """Check if subscription is expired"""
        if not self.end_date:
            return False
        return timezone.now() > self.end_date
    
    def days_remaining(self):
        """Calculate days remaining in subscription"""
        if not self.end_date:
            return None
        
        remaining = (self.end_date - timezone.now()).days
        return max(0, remaining)
    
    def save(self, *args, **kwargs):
        """Override save to set max_interval_days based on tier using Ebbinghaus forgetting curve"""
        from .constants import TIER_MAX_INTERVALS
        from .subscription import tier_utils

        # Validate and set max_interval_days based on tier
        if self.tier in TIER_MAX_INTERVALS:
            self.max_interval_days = tier_utils.get_max_interval(self.tier)
        else:
            # Defensive: log warning for invalid tier
            logger = logging.getLogger(__name__)
            logger.warning(
                f'Invalid tier "{self.tier}" for {self.user.email}. '
                f'Using FREE tier defaults.'
            )
            self.tier = SubscriptionTier.FREE
            self.max_interval_days = tier_utils.get_max_interval(SubscriptionTier.FREE)

        super().save(*args, **kwargs)


class PaymentHistory(models.Model):
    """Track subscription payment and change history"""
    
    class PaymentType(models.TextChoices):
        UPGRADE = 'upgrade', '업그레이드'
        DOWNGRADE = 'downgrade', '다운그레이드'
        CANCELLATION = 'cancellation', '구독 취소'
        RENEWAL = 'renewal', '갱신'
        INITIAL = 'initial', '최초 구독'
        REFUND = 'refund', '환불'
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payment_history'
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
        help_text='Type of payment or subscription change'
    )
    from_tier = models.CharField(
        max_length=20,
        choices=SubscriptionTier.choices,
        null=True,
        blank=True,
        help_text='Previous subscription tier'
    )
    to_tier = models.CharField(
        max_length=20,
        choices=SubscriptionTier.choices,
        help_text='New subscription tier'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Payment amount (0 for free tier)'
    )
    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Refund amount for downgrades'
    )
    billing_cycle = models.CharField(
        max_length=20,
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
        help_text='Billing cycle for this payment'
    )
    payment_method_used = models.CharField(
        max_length=100,
        blank=True,
        help_text='Payment method used for this transaction'
    )
    gateway_payment_id = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Payment ID from gateway (Toss, Stripe, etc.)'
    )
    gateway_order_id = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Order ID from gateway'
    )
    description = models.TextField(
        blank=True,
        help_text='Additional details about the payment'
    )
    notes = models.TextField(
        blank=True,
        help_text='Internal notes about the transaction'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Transaction date and time'
    )
    
    class Meta:
        db_table = 'accounts_payment_history'
        verbose_name = 'Payment History'
        verbose_name_plural = 'Payment Histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_payment_type_display()} - {self.created_at}"
    
    @property
    def tier_display(self):
        """Get display text for tier change"""
        if self.from_tier and self.from_tier != self.to_tier:
            from_display = dict(SubscriptionTier.choices).get(self.from_tier, self.from_tier)
            to_display = dict(SubscriptionTier.choices).get(self.to_tier, self.to_tier)
            return f"{from_display} → {to_display}"
        else:
            return dict(SubscriptionTier.choices).get(self.to_tier, self.to_tier)



class BillingSchedule(TimestampMixin):
    """Track future billing schedules and payments"""
    
    class ScheduleStatus(models.TextChoices):
        PENDING = 'pending', '대기'
        COMPLETED = 'completed', '완료'
        FAILED = 'failed', '실패'
        CANCELLED = 'cancelled', '취소'
        PREPAID = 'prepaid', '선불'
    
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='billing_schedules'
    )
    scheduled_date = models.DateTimeField(
        help_text='Date when billing should occur'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Amount to be billed'
    )
    billing_cycle = models.CharField(
        max_length=20,
        choices=BillingCycle.choices,
        help_text='Billing cycle for this schedule'
    )
    status = models.CharField(
        max_length=20,
        choices=ScheduleStatus.choices,
        default=ScheduleStatus.PENDING,
        help_text='Status of this billing schedule'
    )
    tier_at_billing = models.CharField(
        max_length=20,
        choices=SubscriptionTier.choices,
        help_text='Subscription tier when billing occurs'
    )
    payment_method = models.CharField(
        max_length=100,
        blank=True,
        help_text='Payment method to use for billing'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about this billing schedule'
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this billing was processed'
    )
    
    class Meta:
        db_table = 'accounts_billing_schedule'
        verbose_name = 'Billing Schedule'
        verbose_name_plural = 'Billing Schedules'
        ordering = ['scheduled_date']
        indexes = [
            models.Index(fields=['subscription', 'scheduled_date']),
            models.Index(fields=['status', 'scheduled_date']),
        ]
    
    def __str__(self):
        return f"{self.subscription.user.email} - {self.scheduled_date} - {self.amount}"
    
    def is_due(self):
        """Check if this billing schedule is due"""
        return timezone.now() >= self.scheduled_date and self.status == self.ScheduleStatus.PENDING
    
    def can_be_processed(self):
        """Check if this billing can be processed"""
        return (
            self.status == self.ScheduleStatus.PENDING and
            self.subscription.is_active and
            not self.subscription.is_expired()
        )






# Signal to create basic subscription for new users
@receiver(post_save, sender=User)
def create_user_subscription(sender, instance, created, **kwargs):
    """Create a basic subscription for new users"""
    if created and not hasattr(instance, 'subscription'):
        Subscription.objects.create(
            user=instance,
            tier=SubscriptionTier.BASIC,
            max_interval_days=90
        )


@receiver(post_save, sender=Subscription)
def adjust_review_schedules_on_subscription_change(sender, instance, created, **kwargs):
    """
    Trigger async task to adjust review schedules when subscription tier changes.

    This signal delegates the heavy lifting to a Celery task to prevent
    blocking the API response when subscription is updated.
    """
    if not created:  # Only for updates, not new subscriptions
        # Import task lazily to avoid circular imports
        from review.tasks import adjust_review_schedules_on_subscription_change as adjust_task

        # Queue the adjustment task asynchronously
        adjust_task.delay(instance.id)

        logger = logging.getLogger(__name__)
        logger.info(
            f"Queued review schedule adjustment for user {instance.user.email} "
            f"subscription change to {instance.tier}"
        )


class NotificationPreference(TimestampMixin):
    """사용자별 이메일 알림 설정"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preference'
    )

    # 기본 알림 설정
    email_notifications_enabled = models.BooleanField(
        default=True,
        help_text='이메일 알림 전체 활성화/비활성화'
    )

    # 복습 알림 설정
    daily_reminder_enabled = models.BooleanField(
        default=True,
        help_text='일일 복습 알림 활성화'
    )
    daily_reminder_time = models.TimeField(
        default='09:00',
        help_text='일일 복습 알림 시간'
    )

    # 저녁 리마인더 설정
    evening_reminder_enabled = models.BooleanField(
        default=True,
        help_text='저녁 복습 리마인더 활성화'
    )
    evening_reminder_time = models.TimeField(
        default='20:00',
        help_text='저녁 복습 리마인더 시간'
    )

    # 주간 요약 설정
    weekly_summary_enabled = models.BooleanField(
        default=True,
        help_text='주간 요약 이메일 활성화'
    )
    weekly_summary_day = models.IntegerField(
        default=1,  # 월요일
        choices=[
            (1, '월요일'),
            (2, '화요일'),
            (3, '수요일'),
            (4, '목요일'),
            (5, '금요일'),
            (6, '토요일'),
            (0, '일요일'),
        ],
        help_text='주간 요약 발송 요일'
    )
    weekly_summary_time = models.TimeField(
        default='09:00',
        help_text='주간 요약 발송 시간'
    )

    # 구독 해지 토큰
    unsubscribe_token = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        help_text='이메일 구독 해지용 토큰'
    )

    class Meta:
        db_table = 'accounts_notification_preference'
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'

    def __str__(self):
        return f"{self.user.email} - Notifications"

    def save(self, *args, **kwargs):
        # 구독 해지 토큰 자동 생성
        if not self.unsubscribe_token:
            self.unsubscribe_token = get_random_string(64)
        super().save(*args, **kwargs)

    def generate_unsubscribe_url(self):
        """구독 해지 URL 생성"""
        from django.conf import settings
        return f"{settings.FRONTEND_URL}/unsubscribe?token={self.unsubscribe_token}"


@receiver(post_save, sender=User)
def create_notification_preference(sender, instance, created, **kwargs):
    """사용자 생성시 알림 설정 자동 생성"""
    if created:
        NotificationPreference.objects.create(user=instance)