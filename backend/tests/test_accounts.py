"""
Tests for accounts app
"""
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class TestUserModel:
    """Test User model"""
    
    @pytest.mark.django_db
    def test_create_user(self):
        """Test creating a regular user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.is_active
        assert not user.is_staff
        assert not user.is_superuser
        assert user.check_password('testpass123')
    
    @pytest.mark.django_db
    def test_create_superuser(self):
        """Test creating a superuser"""
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        assert admin_user.username == 'admin'
        assert admin_user.email == 'admin@example.com'
        assert admin_user.is_active
        assert admin_user.is_staff
        assert admin_user.is_superuser
    
    @pytest.mark.django_db
    def test_user_str_representation(self):
        """Test user string representation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        assert str(user) == 'testuser'
    
    @pytest.mark.django_db
    def test_email_unique(self):
        """Test that email must be unique"""
        User.objects.create_user(
            username='user1',
            email='test@example.com',
            password='testpass123'
        )
        
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='user2',
                email='test@example.com',
                password='testpass123'
            )
    
    @pytest.mark.django_db
    def test_user_timezone_default(self):
        """Test user timezone default value"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        assert user.timezone == 'Asia/Seoul'
    
    @pytest.mark.django_db
    def test_user_notification_enabled_default(self):
        """Test user notification enabled default value"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        assert user.notification_enabled is True