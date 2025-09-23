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
    
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # No additional required fields for email-only auth
    
    objects = UserManager()
    
    def __str__(self):
        return self.email
    
    def generate_email_verification_token(self):
        """Generate a unique token for email verification."""
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
    
    def get_max_review_interval(self):
        """Get maximum review interval based on subscription"""
        from .services import SubscriptionService
        return SubscriptionService(self).get_max_review_interval()

    def has_active_subscription(self):
        """Check if user has an active subscription"""
        from .services import SubscriptionService
        return SubscriptionService(self).has_active_subscription()
    
    def can_upgrade_subscription(self):
        """Check if user can upgrade subscription"""
        from .services import PermissionService
        return PermissionService(self).can_upgrade_subscription()

    def can_use_ai_features(self):
        """Check if user can use AI features based on subscription"""
        from .services import PermissionService
        return PermissionService(self).can_use_ai_features()
    
    def get_ai_question_limit(self):
        """Get AI question generation limit per day based on subscription tier"""
        from .services import PermissionService
        return PermissionService(self).get_ai_question_limit()

    def get_ai_features_list(self):
        """Get list of AI features available for user's subscription tier"""
        from .services import PermissionService
        return PermissionService(self).get_ai_features_list()

    def get_content_limit(self):
        """Get content creation limit based on subscription tier"""
        from .services import PermissionService
        return PermissionService(self).get_content_limit()

    def can_create_content(self):
        """Check if user can create more content based on subscription limit"""
        from .services import PermissionService
        return PermissionService(self).can_create_content()

    def get_content_usage(self):
        """Get content usage statistics for the user"""
        from .services import PermissionService
        return PermissionService(self).get_content_usage()

    def get_category_limit(self):
        """Get category creation limit based on subscription tier"""
        from .services import PermissionService
        return PermissionService(self).get_category_limit()

    def can_create_category(self):
        """Check if user can create more categories based on subscription limit"""
        from .services import PermissionService
        return PermissionService(self).can_create_category()

    def get_category_usage(self):
        """Get category usage statistics for the user"""
        from .services import PermissionService
        return PermissionService(self).get_category_usage()


class SubscriptionTier(models.TextChoices):
    """Subscription tier choices with Ebbinghaus-optimized intervals"""
    FREE = 'free', 'Free (3일)'
    BASIC = 'basic', 'Basic (90일)'
    PRO = 'pro', 'Pro (180일)'


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


class AIUsageTracking(BaseModel):
    """Track daily AI feature usage per user"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_usage_records'
    )
    date = models.DateField(
        default=timezone.now,
        help_text='Date of usage'
    )
    questions_generated = models.IntegerField(
        default=0,
        help_text='Number of AI questions generated on this date'
    )
    evaluations_performed = models.IntegerField(
        default=0,
        help_text='Number of AI evaluations performed on this date'
    )
    
    class Meta:
        db_table = 'accounts_ai_usage_tracking'
        unique_together = ['user', 'date']
        verbose_name = 'AI Usage Tracking'
        verbose_name_plural = 'AI Usage Trackings'
        indexes = [
            models.Index(fields=['user', 'date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.date}: {self.questions_generated} questions"
    
    @classmethod
    def get_or_create_for_today(cls, user):
        """Get or create usage record for today"""
        today = timezone.now().date()
        usage, created = cls.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                'questions_generated': 0,
                'evaluations_performed': 0
            }
        )
        return usage
    
    def can_generate_questions(self, count=1):
        """Check if user can generate more questions today"""
        daily_limit = self.user.get_ai_question_limit()
        if daily_limit == 0:
            return False
        return (self.questions_generated + count) <= daily_limit
    
    def increment_questions(self, count=1):
        """Increment question generation count"""
        if self.can_generate_questions(count):
            self.questions_generated += count
            self.save()
            return True
        return False
    
    def increment_evaluations(self, count=1):
        """Increment evaluation count"""
        self.evaluations_performed += count
        self.save()
        return True
    
    def get_usage_summary(self):
        """Get detailed usage summary for today"""
        daily_limit = self.user.get_ai_question_limit()
        remaining = max(0, daily_limit - self.questions_generated)
        
        return {
            'date': self.date,
            'questions_generated': self.questions_generated,
            'evaluations_performed': self.evaluations_performed,
            'daily_limit': daily_limit,
            'remaining': remaining,
            'usage_percentage': (self.questions_generated / daily_limit * 100) if daily_limit > 0 else 0,
            'tier': self.user.subscription.tier,
        }
    
    @classmethod
    def get_user_weekly_usage(cls, user, weeks=1):
        """Get user's usage for the past weeks"""
        from datetime import timedelta
        end_date = timezone.now().date()
        start_date = end_date - timedelta(weeks=weeks * 7)
        
        usage_records = cls.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        total_questions = sum(record.questions_generated for record in usage_records)
        total_evaluations = sum(record.evaluations_performed for record in usage_records)
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_questions': total_questions,
            'total_evaluations': total_evaluations,
            'daily_records': [record.get_usage_summary() for record in usage_records],
            'average_daily_questions': total_questions / (weeks * 7) if weeks > 0 else 0,
        }


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


class EmailSubscription(models.Model):
    """Email subscription for launch notifications and marketing"""
    email = models.EmailField(
        unique=True,
        help_text='Email address for subscription notifications'
    )
    subscribed_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the email was subscribed'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether the subscription is active'
    )
    unsubscribed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the user unsubscribed'
    )
    source = models.CharField(
        max_length=100,
        default='subscription_page',
        help_text='Source of the email subscription'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address when subscribed'
    )
    user_agent = models.TextField(
        blank=True,
        help_text='User agent when subscribed'
    )
    
    class Meta:
        db_table = 'accounts_email_subscription'
        verbose_name = 'Email Subscription'
        verbose_name_plural = 'Email Subscriptions'
        ordering = ['-subscribed_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active', '-subscribed_at']),
        ]
    
    def __str__(self):
        status = "Active" if self.is_active else "Unsubscribed"
        return f"{self.email} - {status}"
    
    def unsubscribe(self):
        """Unsubscribe this email"""
        self.is_active = False
        self.unsubscribed_at = timezone.now()
        self.save()

    
    @classmethod
    def get_active_count(cls):
        """Get total count of active subscriptions"""
        return cls.objects.filter(is_active=True).count()
    
    @classmethod
    def subscribe_email(cls, email, source='subscription_page', ip_address=None, user_agent=''):
        """Subscribe an email with duplicate handling"""
        # Check if email already exists
        existing = cls.objects.filter(email=email).first()
        
        if existing:
            if existing.is_active:
                return existing, False  # Already subscribed
            else:
                # Reactivate existing subscription
                existing.is_active = True
                existing.unsubscribed_at = None
                existing.subscribed_at = timezone.now()
                existing.source = source
                existing.ip_address = ip_address
                existing.user_agent = user_agent
                existing.save()
                return existing, True  # Resubscribed
        else:
            # Create new subscription
            subscription = cls.objects.create(
                email=email,
                source=source,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return subscription, True  # Newly subscribed




# Signal to create free subscription for new users
@receiver(post_save, sender=User)
def create_user_subscription(sender, instance, created, **kwargs):
    """Create a free subscription for new users"""
    if created and not hasattr(instance, 'subscription'):
        Subscription.objects.create(
            user=instance,
            tier=SubscriptionTier.FREE,
            max_interval_days=3
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