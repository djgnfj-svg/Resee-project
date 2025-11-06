import hashlib
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.crypto import get_random_string

from resee.models import BaseModel, TimestampMixin

# Import legal models to make them discoverable by Django migrations
from .legal.legal_models import (
    LegalDocument,
    UserConsent,
    DataDeletionRequest,
    DataExportRequest,
    CookieConsent,
)


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

        Security: Token is hashed with SHA-256 before storage to prevent
        unauthorized access if database is compromised.
        """
        # 32자 길이의 URL-safe 토큰 생성 (사용자에게 전송할 원본)
        token = secrets.token_urlsafe(32)

        # 🔒 보안: DB에는 해시만 저장 (SHA-256)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        self.email_verification_token = token_hash
        self.email_verification_sent_at = timezone.now()
        self.save()

        # 원본 토큰만 반환 (이메일로 전송)
        return token
    
    def verify_email(self, token):
        """Verify email with the given token.

        Security:
        - Uses constant-time comparison to prevent timing attacks
        - Validates token hash instead of plaintext
        - Checks expiration before comparison
        """
        if not self.email_verification_token:
            return False

        # 🔒 보안: 입력받은 토큰을 해싱하여 저장된 해시와 비교
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # 🔒 보안: Constant-time 비교 (timing attack 방어)
        if not secrets.compare_digest(self.email_verification_token, token_hash):
            return False

        # 토큰 유효기간 확인
        if self.email_verification_sent_at:
            expiry_time = self.email_verification_sent_at + timedelta(
                days=settings.EMAIL_VERIFICATION_TIMEOUT_DAYS
            )
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
    
    def get_max_review_interval(self):
        """Get maximum review interval based on subscription"""
        from .subscription.services import SubscriptionService
        return SubscriptionService(self).get_max_review_interval()

    def has_active_subscription(self):
        """Check if user has an active subscription"""
        from .subscription.services import SubscriptionService
        return SubscriptionService(self).has_active_subscription()
    
    def can_upgrade_subscription(self):
        """Check if user can upgrade subscription"""
        from .subscription.services import PermissionService
        return PermissionService(self).can_upgrade_subscription()


    def get_content_limit(self):
        """Get content creation limit based on subscription tier"""
        from .subscription.services import PermissionService
        return PermissionService(self).get_content_limit()

    def can_create_content(self):
        """Check if user can create more content based on subscription limit"""
        from .subscription.services import PermissionService
        return PermissionService(self).can_create_content()

    def get_content_usage(self):
        """Get content usage statistics for the user"""
        from .subscription.services import PermissionService
        return PermissionService(self).get_content_usage()

    def get_category_limit(self):
        """Get category creation limit based on subscription tier"""
        from .subscription.services import PermissionService
        return PermissionService(self).get_category_limit()

    def can_create_category(self):
        """Check if user can create more categories based on subscription limit"""
        from .subscription.services import PermissionService
        return PermissionService(self).can_create_category()

    def get_category_usage(self):
        """Get category usage statistics for the user"""
        from .subscription.services import PermissionService
        return PermissionService(self).get_category_usage()


class SubscriptionTier(models.TextChoices):
    """Subscription tier choices with Ebbinghaus-optimized intervals"""
    FREE = 'free', 'FREE'
    BASIC = 'basic', 'BASIC'
    PRO = 'pro', 'PRO'


class BillingCycle(models.TextChoices):
    """Billing cycle options"""
    MONTHLY = 'monthly', '월간'
    YEARLY = 'yearly', '연간'


class Subscription(BaseModel):
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
        # Ebbinghaus-optimized maximum intervals for each tier
        tier_max_intervals = {
            SubscriptionTier.FREE: 3,     # Basic spaced repetition
            SubscriptionTier.BASIC: 90,   # Medium-term memory retention
            SubscriptionTier.PRO: 180,    # Complete long-term retention (6 months)
        }

        # Defensive code: Infer tier from max_interval_days if tier is invalid
        valid_tiers = [choice[0] for choice in SubscriptionTier.choices]
        if self.tier not in valid_tiers:
            # Reverse mapping: max_interval_days -> tier
            interval_to_tier = {v: k for k, v in tier_max_intervals.items()}
            inferred_tier = interval_to_tier.get(self.max_interval_days)

            if inferred_tier:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f'Invalid tier "{self.tier}" for {self.user.email}. '
                    f'Inferred tier "{inferred_tier}" from max_interval_days={self.max_interval_days}'
                )
                self.tier = inferred_tier

        # Set max_interval_days based on tier
        if self.tier in tier_max_intervals:
            self.max_interval_days = tier_max_intervals[self.tier]

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



class BillingSchedule(BaseModel):
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






# Signal to create free subscription for new users
@receiver(post_save, sender=User)
def create_user_subscription(sender, instance, created, **kwargs):
    """Create a BASIC subscription for new users"""
    if created and not hasattr(instance, 'subscription'):
        Subscription.objects.create(
            user=instance,
            tier=SubscriptionTier.BASIC,
            max_interval_days=90
        )


@receiver(post_save, sender=Subscription)
def adjust_review_schedules_on_subscription_change(sender, instance, created, **kwargs):
    """Adjust existing review schedules when subscription tier changes"""
    if not created:  # Only for updates, not new subscriptions
        from datetime import timedelta

        from django.utils import timezone

        from review.models import ReviewSchedule
        from review.utils import get_review_intervals

        # Get new intervals for the updated subscription
        new_intervals = get_review_intervals(instance.user)
        new_max_interval = instance.max_interval_days
        
        # Get all active review schedules for this user
        schedules = ReviewSchedule.objects.filter(
            user=instance.user,
            is_active=True
        )
        
        for schedule in schedules:
            schedule_changed = False
            
            # Check if current interval_index exceeds new tier limits
            if schedule.interval_index >= len(new_intervals):
                schedule.interval_index = len(new_intervals) - 1
                schedule_changed = True
            
            # Get the current interval for this schedule
            current_interval = new_intervals[schedule.interval_index]
            
            # Check if current interval exceeds new max interval
            if current_interval > new_max_interval:
                # Find the highest allowed interval
                allowed_intervals = [i for i in new_intervals if i <= new_max_interval]
                if allowed_intervals:
                    max_allowed_interval = max(allowed_intervals)
                    try:
                        schedule.interval_index = new_intervals.index(max_allowed_interval)
                        current_interval = max_allowed_interval
                        schedule_changed = True
                    except ValueError:
                        # Fallback to the last allowed interval
                        schedule.interval_index = len(allowed_intervals) - 1
                        current_interval = allowed_intervals[-1]
                        schedule_changed = True
            
            # If schedule was changed, update the next_review_date
            if schedule_changed:
                # Keep the review due soon if it was already due
                if schedule.next_review_date <= timezone.now():
                    # Keep it due today/now
                    pass
                else:
                    # Recalculate next review date with new interval
                    # Use a reasonable base date (either creation date or now minus interval)
                    base_date = timezone.now()
                    if schedule.created_at:
                        # Calculate how far we should be from creation based on new interval
                        days_since_creation = (timezone.now() - schedule.created_at).days
                        if days_since_creation < current_interval:
                            base_date = schedule.created_at
                    
                    schedule.next_review_date = base_date + timedelta(days=current_interval)
                
                schedule.save()
        
        # Log the adjustment for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Adjusted {schedules.count()} review schedules for user {instance.user.email} "
                   f"due to subscription change to {instance.tier} (max: {new_max_interval} days)")


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