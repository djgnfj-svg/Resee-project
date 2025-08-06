import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.crypto import get_random_string


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
    
    # 생성일자, 업데이트일자
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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
        if hasattr(self, 'subscription') and self.subscription.is_active and not self.subscription.is_expired():
            return self.subscription.max_interval_days
        return 3  # Default FREE tier
    
    def has_active_subscription(self):
        """Check if user has an active subscription"""
        if not hasattr(self, 'subscription'):
            return False
        return self.subscription.is_active and not self.subscription.is_expired()
    
    def can_upgrade_subscription(self):
        """Check if user can upgrade subscription"""
        from django.conf import settings
        if getattr(settings, 'ENFORCE_EMAIL_VERIFICATION', True) and not self.is_email_verified:
            return False
        
        if hasattr(self, 'subscription') and self.subscription.tier == SubscriptionTier.PRO:
            return False
        
        return True
    
    def can_use_ai_features(self):
        """Check if user can use AI features based on subscription"""
        from django.conf import settings
        if getattr(settings, 'ENFORCE_EMAIL_VERIFICATION', True) and not self.is_email_verified:
            return False
            
        if not hasattr(self, 'subscription'):
            return False
            
        return self.subscription.is_active and not self.subscription.is_expired()
    
    def get_ai_question_limit(self):
        """Get AI question generation limit per day based on subscription tier"""
        if not hasattr(self, 'subscription') or not self.subscription.is_active or self.subscription.is_expired():
            return 0
        
        tier_limits = {
            SubscriptionTier.FREE: 0,         # No AI features for free users
            SubscriptionTier.BASIC: 30,       # 30 questions per day
            SubscriptionTier.PRO: 200,        # 200 questions per day (unlimited-like)
        }
        
        return tier_limits.get(self.subscription.tier, 0)
    
    def get_ai_features_list(self):
        """Get list of AI features available for user's subscription tier"""
        if not self.can_use_ai_features():
            return []
            
        tier_features = {
            SubscriptionTier.FREE: [],
            SubscriptionTier.BASIC: [
                'multiple_choice',
                'ai_chat',
                'explanation_evaluation'  # 서술형 평가 추가
            ],
            SubscriptionTier.PRO: [
                'multiple_choice',
                'fill_blank',
                'blur_processing',
                'ai_chat',
                'explanation_evaluation'
            ]
        }
        
        return tier_features.get(self.subscription.tier, [])


class SubscriptionTier(models.TextChoices):
    """Subscription tier choices with Ebbinghaus-optimized intervals"""
    FREE = 'free', 'Free (3일)'
    BASIC = 'basic', 'Basic (90일)'
    PRO = 'pro', 'Pro (180일)'


class Subscription(models.Model):
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
    is_active = models.BooleanField(
        default=True,
        help_text='Whether the subscription is active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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


class AIUsageTracking(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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
        from review.models import ReviewSchedule
        from review.utils import get_review_intervals
        from django.utils import timezone
        from datetime import timedelta
        
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