from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """User serializer"""
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'timezone', 'notification_enabled', 'date_joined')
        read_only_fields = ('id', 'date_joined')


class ProfileSerializer(serializers.ModelSerializer):
    """Profile serializer for user profile updates"""
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 
                 'timezone', 'notification_enabled')


class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm',
                 'first_name', 'last_name', 'timezone', 'notification_enabled')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class PasswordChangeSerializer(serializers.Serializer):
    """Password change serializer"""
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not authenticate(username=user.username, password=value):
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
        if not authenticate(username=user.username, password=value):
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