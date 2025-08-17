"""
Tests for accounts app
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from accounts.serializers import (AccountDeleteSerializer,
                                  PasswordChangeSerializer, ProfileSerializer,
                                  UserRegistrationSerializer, UserSerializer)

from .base import BaseAPITestCase, BaseTestCase

User = get_user_model()


class UserModelTestCase(BaseTestCase):
    """Test cases for User model"""
    
    def test_create_user(self):
        """Test creating a regular user"""
        user = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test2@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_email_verified)  # Default not verified
        self.assertEqual(user.weekly_goal, 7)  # Default weekly goal
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertEqual(admin_user.email, 'admin@example.com')
        self.assertTrue(admin_user.check_password('adminpass123'))
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_email_verified)  # Superuser is auto-verified
    
    def test_user_string_representation(self):
        """Test user string representation"""
        user = self.create_user(email='test3@example.com')
        self.assertEqual(str(user), 'test3@example.com')
    
    def test_user_email_unique(self):
        """Test that email must be unique"""
        self.create_user(email='test4@example.com')
        with self.assertRaises(Exception):
            self.create_user(email='test4@example.com')
    
    def test_user_weekly_goal_default(self):
        """Test weekly goal default value"""
        user = self.create_user(email='test5@example.com')
        self.assertEqual(user.weekly_goal, 7)
    
    def test_user_email_verification(self):
        """Test email verification functionality"""
        user = self.create_user(email='test6@example.com')
        self.assertFalse(user.is_email_verified)
        
        # Generate verification token
        token = user.generate_email_verification_token()
        self.assertIsNotNone(token)
        self.assertIsNotNone(user.email_verification_token)
        
        # Verify email with token
        self.assertTrue(user.verify_email(token))
        self.assertTrue(user.is_email_verified)
        self.assertIsNone(user.email_verification_token)


class UserSerializerTestCase(BaseTestCase):
    """Test cases for User serializers"""
    
    def test_user_serializer(self):
        """Test UserSerializer"""
        user = self.create_user()
        serializer = UserSerializer(user)
        data = serializer.data
        
        self.assertEqual(data['email'], user.email)
        self.assertEqual(data['is_email_verified'], user.is_email_verified)
        self.assertEqual(data['weekly_goal'], user.weekly_goal)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertNotIn('password', data)
    
    def test_profile_serializer(self):
        """Test ProfileSerializer"""
        user = self.create_user()
        data = {
            'username': 'updateduser',
            'weekly_goal': 14,
        }
        serializer = ProfileSerializer(user, data=data)
        self.assertTrue(serializer.is_valid())
        
        updated_user = serializer.save()
        self.assertEqual(updated_user.username, 'updateduser')
        self.assertEqual(updated_user.weekly_goal, 14)
        # Email should remain unchanged (read-only)
        self.assertEqual(updated_user.email, user.email)
    
    def test_user_registration_serializer_valid(self):
        """Test UserRegistrationSerializer with valid data"""
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertTrue(user.check_password('newpass123'))
        self.assertFalse(user.is_email_verified)  # Default not verified
        self.assertEqual(user.weekly_goal, 7)  # Default weekly goal
    
    def test_user_registration_serializer_password_mismatch(self):
        """Test UserRegistrationSerializer with mismatched passwords"""
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'differentpass',
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password_confirm', serializer.errors)
    
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
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
        }
        
        # Remove authentication for registration
        self.client.credentials()
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check user was created
        user = User.objects.get(email='newuser@example.com')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertFalse(user.is_email_verified)  # Email not auto-verified in test environment
        self.assertEqual(user.weekly_goal, 7)  # Default value
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
        self.assertIn('field_errors', response.data)
        self.assertIn('email', response.data['field_errors'])
        self.assertIn('password', response.data['field_errors'])
    
    def test_get_profile(self):
        """Test getting user profile"""
        url = reverse('accounts:profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['is_email_verified'], self.user.is_email_verified)
        self.assertEqual(response.data['weekly_goal'], self.user.weekly_goal)
    
    def test_update_profile(self):
        """Test updating user profile"""
        url = reverse('accounts:profile')
        data = {
            'username': 'updateduser',
            'weekly_goal': 14,
        }
        
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check user was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updateduser')
        self.assertEqual(self.user.weekly_goal, 14)
        # Email should remain unchanged (read-only in ProfileSerializer)
        self.assertNotEqual(self.user.email, 'updated@example.com')
    
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
        # Verify user email first
        self.user.is_email_verified = True
        self.user.save()
        
        url = reverse('token_obtain_pair')
        data = {
            'email': self.user.email,
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
            'email': self.user.email,
            'password': 'wrongpassword',
        }
        
        # Remove authentication
        self.client.credentials()
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
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