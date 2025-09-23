from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Subscription, SubscriptionTier, PaymentHistory

User = get_user_model()


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer that uses email instead of username"""
    email = serializers.EmailField()
    password = serializers.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the username field and add email field
        self.fields.pop('username', None)
        self.fields['email'] = serializers.EmailField()

    def validate(self, attrs):
        # Use email for authentication
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,  # Django's authenticate uses 'username' parameter but we pass email
                password=password
            )

            if not user:
                raise serializers.ValidationError('이메일 또는 비밀번호가 올바르지 않습니다.')

            if not user.is_active:
                raise serializers.ValidationError('비활성화된 계정입니다.')

            # 환경변수로 이메일 인증 강제 여부 제어
            if getattr(settings, 'ENFORCE_EMAIL_VERIFICATION', False) and not user.is_email_verified:
                raise serializers.ValidationError({
                    'email_verification_required': True,
                    'email': user.email,
                    'message': '이메일 인증을 완료해주세요.'
                })

            # Set the user for token generation
            self.user = user
            refresh = self.get_token(user)
            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        else:
            raise serializers.ValidationError('이메일과 비밀번호를 입력해주세요.')

    @classmethod
    def get_token(cls, user):
        return super().get_token(user)


class UserSerializer(serializers.ModelSerializer):
    """User serializer"""
    subscription = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'is_email_verified', 'is_staff', 'is_superuser', 'weekly_goal', 'date_joined', 'subscription')
        read_only_fields = ('id', 'date_joined', 'is_email_verified', 'is_staff', 'is_superuser', 'subscription')
    
    def get_subscription(self, obj):
        """Get subscription data"""
        if hasattr(obj, 'subscription'):
            return {
                'id': obj.subscription.id,
                'tier': obj.subscription.tier,
                'tier_display': obj.subscription.get_tier_display(),
                'max_interval_days': obj.subscription.max_interval_days,
                'start_date': obj.subscription.start_date.isoformat() if obj.subscription.start_date else None,
                'end_date': obj.subscription.end_date.isoformat() if obj.subscription.end_date else None,
                'is_active': obj.subscription.is_active,
                'days_remaining': obj.subscription.days_remaining(),
                'is_expired': obj.subscription.is_expired(),
            }
        return None


class ProfileSerializer(serializers.ModelSerializer):
    """Profile serializer for user profile updates"""
    
    class Meta:
        model = User
        fields = ('email', 'username', 'is_email_verified', 'weekly_goal')
        read_only_fields = ('email', 'is_email_verified')
    
    def validate_username(self, value):
        """Validate username"""
        if value:  # Only validate if username is provided
            # Check if username is already taken by another user
            user = self.instance
            if User.objects.filter(username=value).exclude(id=user.id).exists():
                raise serializers.ValidationError("이미 사용 중인 사용자명입니다.")
        return value
    
    def validate_weekly_goal(self, value):
        """Validate weekly goal"""
        if value is not None:
            if value < 1:
                raise serializers.ValidationError("주간 목표는 최소 1회 이상이어야 합니다.")
            if value > 1000:
                raise serializers.ValidationError("주간 목표는 최대 1000회까지 설정 가능합니다.")
        return value


class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer with email-only authentication"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm')
    
    def validate_email(self, value):
        """Validate email"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 사용 중인 이메일 주소입니다.")
        return value
    
    def validate_password(self, value):
        """Validate password strength"""
        if len(value) < 8:
            raise serializers.ValidationError("비밀번호는 최소 8글자 이상이어야 합니다.")
        
        # Check for at least one letter and one number
        has_letter = any(c.isalpha() for c in value)
        has_number = any(c.isdigit() for c in value)
        
        if not has_letter:
            raise serializers.ValidationError("비밀번호에는 최소 하나의 문자가 포함되어야 합니다.")
        if not has_number:
            raise serializers.ValidationError("비밀번호에는 최소 하나의 숫자가 포함되어야 합니다.")
        
        return value
    
    def validate(self, attrs):
        """Validate form data"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': "비밀번호가 일치하지 않습니다."
            })
        return attrs
    
    def create(self, validated_data):
        """Create new user"""
        try:
            validated_data.pop('password_confirm')
            user = User.objects.create_user(**validated_data)
            return user
        except Exception as e:
            raise serializers.ValidationError({
                'non_field_errors': f"계정 생성 중 오류가 발생했습니다: {str(e)}"
            })


class PasswordChangeSerializer(serializers.Serializer):
    """Password change serializer"""
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not authenticate(username=user.email, password=value):
            raise serializers.ValidationError("현재 비밀번호가 올바르지 않습니다.")
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("새 비밀번호가 일치하지 않습니다.")
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class AccountDeleteSerializer(serializers.Serializer):
    """Account deletion serializer"""
    password = serializers.CharField(required=True)
    confirmation = serializers.CharField(required=True)
    
    def validate_password(self, value):
        user = self.context['request'].user
        if not authenticate(username=user.email, password=value):
            raise serializers.ValidationError("비밀번호가 올바르지 않습니다.")
        return value
    
    def validate_confirmation(self, value):
        if value != 'DELETE':
            raise serializers.ValidationError("계정 삭제를 확인하려면 'DELETE'를 입력해주세요.")
        return value
    
    def save(self):
        user = self.context['request'].user
        user.delete()
        return user


class SubscriptionSerializer(serializers.ModelSerializer):
    """Subscription serializer"""
    tier_display = serializers.CharField(source='get_tier_display', read_only=True)
    days_remaining = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'tier', 'tier_display', 'max_interval_days',
            'start_date', 'end_date', 'is_active',
            'days_remaining', 'is_expired', 'auto_renewal',
            'next_billing_date', 'payment_method'
        ]
        read_only_fields = ['id', 'start_date']
    
    def get_days_remaining(self, obj):
        """Get days remaining in subscription"""
        return obj.days_remaining()
    
    def get_is_expired(self, obj):
        """Check if subscription is expired"""
        return obj.is_expired()


class SubscriptionTierSerializer(serializers.Serializer):
    """Serializer for subscription tier information"""
    name = serializers.CharField()
    display_name = serializers.CharField()
    max_days = serializers.IntegerField()
    price = serializers.IntegerField()
    features = serializers.ListField(child=serializers.CharField())


class SubscriptionUpgradeSerializer(serializers.Serializer):
    """Serializer for subscription upgrade request"""
    tier = serializers.ChoiceField(choices=SubscriptionTier.choices)
    
    def validate_tier(self, value):
        """Validate tier selection"""
        user = self.context['request'].user
        
        if not user.is_email_verified:
            raise serializers.ValidationError('이메일 인증이 필요합니다.')
        
        if hasattr(user, 'subscription') and user.subscription.tier == SubscriptionTier.PRO:
            if value == SubscriptionTier.PRO:
                raise serializers.ValidationError('이미 최고 구독 등급입니다.')
        
        return value


class PaymentHistorySerializer(serializers.ModelSerializer):
    """Serializer for payment history records"""
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    tier_display = serializers.CharField(read_only=True)
    from_tier_display = serializers.SerializerMethodField()
    to_tier_display = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentHistory
        fields = [
            'id',
            'payment_type',
            'payment_type_display',
            'from_tier',
            'from_tier_display',
            'to_tier',
            'to_tier_display',
            'tier_display',
            'amount',
            'description',
            'created_at'
        ]
        read_only_fields = fields
    
    def get_from_tier_display(self, obj):
        """Get display text for from_tier"""
        if obj.from_tier:
            return dict(SubscriptionTier.choices).get(obj.from_tier, obj.from_tier)
        return None
    
    def get_to_tier_display(self, obj):
        """Get display text for to_tier"""
        return dict(SubscriptionTier.choices).get(obj.to_tier, obj.to_tier)