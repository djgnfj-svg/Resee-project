from rest_framework import serializers

from .models import Payment, PaymentPlan, Subscription


class PaymentPlanSerializer(serializers.ModelSerializer):
    """결제 플랜 시리얼라이저"""
    yearly_discount_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = PaymentPlan
        fields = [
            'id', 'name', 'tier', 'monthly_price', 'yearly_price',
            'yearly_discount_percentage', 'description', 'features', 'is_active'
        ]
        read_only_fields = ['id']


class PaymentSerializer(serializers.ModelSerializer):
    """결제 기록 시리얼라이저"""
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'user_email', 'plan_name', 'amount', 'currency',
            'billing_cycle', 'status', 'failure_reason', 'created_at', 'paid_at'
        ]
        read_only_fields = ['id', 'user_email', 'plan_name', 'created_at', 'paid_at']


class SubscriptionSerializer(serializers.ModelSerializer):
    """구독 정보 시리얼라이저"""
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_tier = serializers.CharField(source='plan.tier', read_only=True)
    days_until_renewal = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'plan_name', 'plan_tier', 'is_active', 'billing_cycle',
            'current_period_start', 'current_period_end', 'trial_end',
            'canceled_at', 'days_until_renewal', 'is_expired', 'created_at'
        ]
        read_only_fields = [
            'id', 'plan_name', 'plan_tier', 'current_period_start',
            'current_period_end', 'trial_end', 'canceled_at', 'created_at'
        ]


class CreatePaymentIntentSerializer(serializers.Serializer):
    """결제 의도 생성 요청 시리얼라이저"""
    plan_id = serializers.IntegerField()
    billing_cycle = serializers.ChoiceField(
        choices=Payment.BillingCycle.choices,
        default=Payment.BillingCycle.MONTHLY
    )
    
    def validate_plan_id(self, value):
        try:
            plan = PaymentPlan.objects.get(id=value, is_active=True)
            return value
        except PaymentPlan.DoesNotExist:
            raise serializers.ValidationError("유효하지 않은 플랜입니다.")


class CreateSubscriptionSerializer(serializers.Serializer):
    """구독 생성 요청 시리얼라이저"""
    plan_id = serializers.IntegerField()
    billing_cycle = serializers.ChoiceField(
        choices=Payment.BillingCycle.choices,
        default=Payment.BillingCycle.MONTHLY
    )
    payment_method_id = serializers.CharField(max_length=200)
    
    def validate_plan_id(self, value):
        try:
            plan = PaymentPlan.objects.get(id=value, is_active=True)
            return value
        except PaymentPlan.DoesNotExist:
            raise serializers.ValidationError("유효하지 않은 플랜입니다.")


class UpdateSubscriptionSerializer(serializers.Serializer):
    """구독 변경 요청 시리얼라이저"""
    plan_id = serializers.IntegerField()
    billing_cycle = serializers.ChoiceField(
        choices=Payment.BillingCycle.choices,
        default=Payment.BillingCycle.MONTHLY
    )
    
    def validate_plan_id(self, value):
        try:
            plan = PaymentPlan.objects.get(id=value, is_active=True)
            return value
        except PaymentPlan.DoesNotExist:
            raise serializers.ValidationError("유효하지 않은 플랜입니다.")