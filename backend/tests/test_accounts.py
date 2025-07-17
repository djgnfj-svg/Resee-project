"""
Tests for accounts app
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .base import BaseTestCase, BaseAPITestCase
from accounts.models import User
from accounts.serializers import (
    UserSerializer, ProfileSerializer, UserRegistrationSerializer,
    PasswordChangeSerializer, AccountDeleteSerializer
)

User = get_user_model()


class UserModelTestCase(BaseTestCase):
    """Test cases for User model"""
    
    def test_create_user(self):
        """Test creating a regular user"""
        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        self.assertEqual(user.username, 'testuser2')
        self.assertEqual(user.email, 'test2@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.timezone, 'Asia/Seoul')  # Default timezone
        self.assertTrue(user.notification_enabled)  # Default enabled
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertEqual(admin_user.username, 'admin')
        self.assertEqual(admin_user.email, 'admin@example.com')
        self.assertTrue(admin_user.check_password('adminpass123'))
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
    
    def test_user_string_representation(self):
        """Test user string representation"""
        user = self.create_user(username='testuser3', email='test3@example.com')
        self.assertEqual(str(user), 'testuser3')
    
    def test_user_email_unique(self):
        """Test that email must be unique"""
        self.create_user(email='test4@example.com', username='user4')
        with self.assertRaises(Exception):
            self.create_user(email='test4@example.com', username='different')
    
    def test_user_timezone_validation(self):
        """Test timezone field validation"""
        user = self.create_user(username='user5', email='test5@example.com', timezone='America/New_York')
        self.assertEqual(user.timezone, 'America/New_York')
    
    def test_user_notification_settings(self):
        """Test notification settings"""
        user = self.create_user(username='user6', email='test6@example.com', notification_enabled=False)
        self.assertFalse(user.notification_enabled)


class UserSerializerTestCase(BaseTestCase):
    """Test cases for User serializers"""
    
    def test_user_serializer(self):
        """Test UserSerializer"""
        user = self.create_user()
        serializer = UserSerializer(user)
        data = serializer.data
        
        self.assertEqual(data['username'], user.username)
        self.assertEqual(data['email'], user.email)
        self.assertEqual(data['timezone'], user.timezone)
        self.assertEqual(data['notification_enabled'], user.notification_enabled)
        self.assertIn('date_joined', data)
        self.assertNotIn('password', data)
    
    def test_profile_serializer(self):
        """Test ProfileSerializer"""
        user = self.create_user()
        data = {
            'username': 'updateduser',
            'email': 'updated@example.com',
            'first_name': 'Updated',
            'last_name': 'User',
            'timezone': 'America/New_York',
            'notification_enabled': False,
        }
        serializer = ProfileSerializer(user, data=data)
        self.assertTrue(serializer.is_valid())
        
        updated_user = serializer.save()
        self.assertEqual(updated_user.username, 'updateduser')
        self.assertEqual(updated_user.email, 'updated@example.com')
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.timezone, 'America/New_York')
        self.assertFalse(updated_user.notification_enabled)
    
    def test_user_registration_serializer_valid(self):
        """Test UserRegistrationSerializer with valid data"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'timezone': 'Asia/Seoul',
            'notification_enabled': True,
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertTrue(user.check_password('newpass123'))
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.timezone, 'Asia/Seoul')
    
    def test_user_registration_serializer_password_mismatch(self):
        """Test UserRegistrationSerializer with mismatched passwords"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'differentpass',
            'timezone': 'Asia/Seoul',
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
    
    def test_password_change_serializer_valid(self):
        """Test PasswordChangeSerializer with valid data"""
        user = self.create_user()
        request = type('Request', (), {'user': user})()
        
        data = {
            'current_password': 'testpass123',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123',
        }
        serializer = PasswordChangeSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
        
        serializer.save()
        user.refresh_from_db()
        self.assertTrue(user.check_password('newpass123'))
        self.assertFalse(user.check_password('testpass123'))
    
    def test_password_change_serializer_wrong_current_password(self):
        """Test PasswordChangeSerializer with wrong current password"""
        user = self.create_user()
        request = type('Request', (), {'user': user})()
        
        data = {
            'current_password': 'wrongpass',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123',
        }
        serializer = PasswordChangeSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('current_password', serializer.errors)
    
    def test_account_delete_serializer_valid(self):
        """Test AccountDeleteSerializer with valid data"""
        user = self.create_user()
        request = type('Request', (), {'user': user})()
        
        data = {
            'password': 'testpass123',
            'confirmation': 'DELETE',
        }
        serializer = AccountDeleteSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
    
    def test_account_delete_serializer_wrong_password(self):
        """Test AccountDeleteSerializer with wrong password"""
        user = self.create_user()
        request = type('Request', (), {'user': user})()
        
        data = {
            'password': 'wrongpass',
            'confirmation': 'DELETE',
        }
        serializer = AccountDeleteSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
    
    def test_account_delete_serializer_wrong_confirmation(self):
        """Test AccountDeleteSerializer with wrong confirmation"""
        user = self.create_user()
        request = type('Request', (), {'user': user})()
        
        data = {
            'password': 'testpass123',
            'confirmation': 'WRONG',
        }
        serializer = AccountDeleteSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('confirmation', serializer.errors)


class AccountsAPITestCase(BaseAPITestCase):
    """Test cases for accounts API endpoints"""
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        url = reverse('accounts:users-register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'timezone': 'Asia/Seoul',
            'notification_enabled': True,
        }
        
        # Remove authentication for registration
        self.client.credentials()
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check user was created
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.first_name, 'New')
        self.assertTrue(user.check_password('newpass123'))
    
    def test_user_registration_invalid_data(self):
        """Test user registration with invalid data"""
        url = reverse('accounts:users-register')
        data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password': 'short',
            'password_confirm': 'different',
        }
        
        # Remove authentication for registration
        self.client.credentials()
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)
    
    def test_get_profile(self):
        """Test getting user profile"""
        url = reverse('accounts:profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['timezone'], self.user.timezone)
    
    def test_update_profile(self):
        """Test updating user profile"""
        url = reverse('accounts:profile')
        data = {
            'username': 'updateduser',
            'email': 'updated@example.com',
            'first_name': 'Updated',
            'last_name': 'User',
            'timezone': 'America/New_York',
            'notification_enabled': False,
        }
        
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check user was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updateduser')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.timezone, 'America/New_York')
        self.assertFalse(self.user.notification_enabled)
    
    def test_change_password(self):
        """Test password change endpoint"""
        url = reverse('accounts:password-change')
        data = {
            'current_password': 'testpass123',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123',
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Check password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))
        self.assertFalse(self.user.check_password('testpass123'))
    
    def test_change_password_wrong_current(self):
        """Test password change with wrong current password"""
        url = reverse('accounts:password-change')
        data = {
            'current_password': 'wrongpass',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123',
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('current_password', response.data)
    
    def test_change_password_mismatch(self):
        """Test password change with password mismatch"""
        url = reverse('accounts:password-change')
        data = {
            'current_password': 'testpass123',
            'new_password': 'newpassword123',
            'new_password_confirm': 'differentpass',
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_delete_account(self):
        """Test account deletion endpoint"""
        url = reverse('accounts:account-delete')
        data = {
            'password': 'testpass123',
            'confirmation': 'DELETE',
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Check user was deleted
        self.assertFalse(User.objects.filter(id=self.user.id).exists())
    
    def test_delete_account_wrong_password(self):
        """Test account deletion with wrong password"""
        url = reverse('accounts:account-delete')
        data = {
            'password': 'wrongpass',
            'confirmation': 'DELETE',
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
    
    def test_delete_account_wrong_confirmation(self):
        """Test account deletion with wrong confirmation"""
        url = reverse('accounts:account-delete')
        data = {
            'password': 'testpass123',
            'confirmation': 'WRONG',
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirmation', response.data)
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access protected endpoints"""
        # Remove authentication
        self.client.credentials()
        
        # Test profile endpoint
        url = reverse('accounts:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test password change endpoint
        url = reverse('accounts:password-change')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test account deletion endpoint
        url = reverse('accounts:account-delete')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class JWTAuthenticationTestCase(BaseAPITestCase):
    """Test cases for JWT authentication"""
    
    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'testpass123',
        }
        
        # Remove authentication
        self.client.credentials()
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword',
        }
        
        # Remove authentication
        self.client.credentials()
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_token_refresh(self):
        """Test JWT token refresh"""
        # Get initial tokens
        refresh = RefreshToken.for_user(self.user)
        
        url = reverse('token_refresh')
        data = {
            'refresh': str(refresh),
        }
        
        # Remove authentication
        self.client.credentials()
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_token_verify(self):
        """Test JWT token verification"""
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token
        
        url = reverse('token_verify')
        data = {
            'token': str(access_token),
        }
        
        # Remove authentication
        self.client.credentials()
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)