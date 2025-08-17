from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from accounts.models import SubscriptionTier

User = get_user_model()


class PaymentPlan(models.Model):
    """Stripe 결제 플랜 정보"""
    name = models.CharField(max_length=100, help_text="플랜 이름")
    tier = models.CharField(
        max_length=20, 
        choices=SubscriptionTier.choices,
        help_text="구독 티어"
    )
    
    # Stripe 관련 필드
    stripe_price_id_monthly = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Stripe 월간 가격 ID"
    )
    stripe_price_id_yearly = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Stripe 연간 가격 ID"
    )
    
    # 가격 정보
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="월간 가격")
    yearly_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="연간 가격")
    
    # 플랜 상세
    description = models.TextField(blank=True, help_text="플랜 설명")
    features = models.JSONField(default=list, help_text="플랜 기능 목록")
    
    # 메타데이터
    is_active = models.BooleanField(default=True, help_text="활성 상태")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['tier']
        
    def __str__(self):
        return f"{self.name} ({self.get_tier_display()})"
    
    @property
    def yearly_discount_percentage(self):
        """연간 결제 할인율 계산"""
        if self.monthly_price > 0:
            monthly_yearly_total = self.monthly_price * 12
            discount = (monthly_yearly_total - self.yearly_price) / monthly_yearly_total * 100
            return round(discount, 1)
        return 0


class Payment(models.Model):
    """결제 기록"""
    class Status(models.TextChoices):
        PENDING = 'pending', '대기중'
        SUCCEEDED = 'succeeded', '성공'
        FAILED = 'failed', '실패'
        CANCELED = 'canceled', '취소'
        REFUNDED = 'refunded', '환불'
    
    class BillingCycle(models.TextChoices):
        MONTHLY = 'monthly', '월간'
        YEARLY = 'yearly', '연간'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(PaymentPlan, on_delete=models.CASCADE)
    
    # 결제 정보
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="결제 금액")
    currency = models.CharField(max_length=3, default='KRW', help_text="통화")
    billing_cycle = models.CharField(max_length=20, choices=BillingCycle.choices)
    
    # Stripe 관련
    stripe_payment_intent_id = models.CharField(max_length=200, unique=True)
    stripe_subscription_id = models.CharField(max_length=200, blank=True, null=True)
    
    # 상태 및 메타데이터
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    failure_reason = models.TextField(blank=True, help_text="실패 사유")
    
    # 일시
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} - {self.get_status_display()}"


class Subscription(models.Model):
    """사용자 구독 정보 (기존 accounts 모델 확장)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription_payment')
    plan = models.ForeignKey(PaymentPlan, on_delete=models.CASCADE)
    
    # Stripe 구독 정보
    stripe_subscription_id = models.CharField(max_length=200, unique=True)
    stripe_customer_id = models.CharField(max_length=200)
    
    # 구독 상태
    is_active = models.BooleanField(default=True)
    billing_cycle = models.CharField(
        max_length=20, 
        choices=Payment.BillingCycle.choices,
        default=Payment.BillingCycle.MONTHLY
    )
    
    # 일시 정보
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    trial_end = models.DateTimeField(blank=True, null=True)
    canceled_at = models.DateTimeField(blank=True, null=True)
    
    # 메타데이터
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"
    
    def is_expired(self):
        """구독 만료 여부 확인"""
        return timezone.now() > self.current_period_end
    
    def days_until_renewal(self):
        """갱신까지 남은 일수"""
        if self.is_expired():
            return 0
        return (self.current_period_end - timezone.now()).days


class WebhookEvent(models.Model):
    """Stripe 웹훅 이벤트 로그"""
    stripe_event_id = models.CharField(max_length=200, unique=True)
    event_type = models.CharField(max_length=100)
    processed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.event_type} - {self.stripe_event_id}"