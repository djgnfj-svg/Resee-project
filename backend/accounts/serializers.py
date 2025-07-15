from rest_framework import serializers
from django.contrib.auth import get_user_model

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