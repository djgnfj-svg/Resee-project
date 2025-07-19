from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

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

            # Set the user for token generation
            self.user = user
            return {}
        else:
            raise serializers.ValidationError('이메일과 비밀번호를 입력해주세요.')

    @classmethod
    def get_token(cls, user):
        return super().get_token(user)


class UserSerializer(serializers.ModelSerializer):
    """User serializer"""
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 
                 'timezone', 'notification_enabled', 'date_joined')
        read_only_fields = ('id', 'date_joined')


class ProfileSerializer(serializers.ModelSerializer):
    """Profile serializer for user profile updates"""
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 
                 'timezone', 'notification_enabled')


class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer with email-only authentication"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm',
                 'first_name', 'last_name', 'timezone', 'notification_enabled')
    
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
            raise serializers.ValidationError("Current password is incorrect")
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
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
            raise serializers.ValidationError("Password is incorrect")
        return value
    
    def validate_confirmation(self, value):
        if value != 'DELETE':
            raise serializers.ValidationError("Please type 'DELETE' to confirm account deletion")
        return value
    
    def save(self):
        user = self.context['request'].user
        user.delete()
        return user