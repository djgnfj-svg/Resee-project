"""
Test cases for accounts application
"""
import json
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Subscription, SubscriptionTier, AIUsageTracking
from .serializers import (
    UserSerializer, UserRegistrationSerializer, ProfileSerializer,
    PasswordChangeSerializer, EmailTokenObtainPairSerializer
)
from .google_auth import GoogleAuthService, GoogleOAuthError

User = get_user_model()


class UserModelTest(TestCase):
    """Test User model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_user(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
        self.assertFalse(self.user.is_email_verified)
        self.assertTrue(hasattr(self.user, 'subscription'))
    
    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_email_verified)
    
    def test_user_str_representation(self):
        self.assertEqual(str(self.user), 'test@example.com')
    
    def test_get_ai_question_limit(self):
        # Test FREE tier limit
        self.assertEqual(self.user.get_ai_question_limit(), 0)
        
        # Test BASIC tier limit
        self.user.subscription.tier = SubscriptionTier.BASIC
        self.user.subscription.save()
        self.assertEqual(self.user.get_ai_question_limit(), 30)
        
        # Test PRO tier limit
        self.user.subscription.tier = SubscriptionTier.PRO
        self.user.subscription.save()
        self.assertEqual(self.user.get_ai_question_limit(), 200)
    
    def test_get_max_review_interval(self):
        # Test FREE tier interval
        self.assertEqual(self.user.get_max_review_interval(), 3)
        
        # Test BASIC tier interval
        self.user.subscription.tier = SubscriptionTier.BASIC
        self.user.subscription.save()
        self.assertEqual(self.user.get_max_review_interval(), 90)
        
        # Test PRO tier interval
        self.user.subscription.tier = SubscriptionTier.PRO
        self.user.subscription.save()
        self.assertEqual(self.user.get_max_review_interval(), 180)
    
    def test_can_upgrade_subscription(self):
        self.user.is_email_verified = True
        self.user.save()
        self.assertTrue(self.user.can_upgrade_subscription())
        
        self.user.is_email_verified = False
        self.user.save()
        self.assertFalse(self.user.can_upgrade_subscription())
    
    def test_can_use_ai_features(self):
        # FREE tier cannot use AI
        self.assertFalse(self.user.can_use_ai_features())
        
        # BASIC tier can use AI if email verified
        self.user.subscription.tier = SubscriptionTier.BASIC
        self.user.subscription.save()
        self.user.is_email_verified = True
        self.user.save()
        self.assertTrue(self.user.can_use_ai_features())
    
    def test_get_ai_features_list(self):
        # FREE tier has no AI features
        self.assertEqual(self.user.get_ai_features_list(), [])
        
        # BASIC tier features
        self.user.subscription.tier = SubscriptionTier.BASIC
        self.user.subscription.save()
        self.user.is_email_verified = True
        self.user.save()
        features = self.user.get_ai_features_list()
        self.assertIn('multiple_choice', features)
        self.assertIn('ai_chat', features)
        self.assertIn('explanation_evaluation', features)
        
        # PRO tier features
        self.user.subscription.tier = SubscriptionTier.PRO
        self.user.subscription.save()
        features = self.user.get_ai_features_list()
        self.assertIn('multiple_choice', features)
        self.assertIn('fill_blank', features)
        self.assertIn('blur_processing', features)


class SubscriptionModelTest(TestCase):
    """Test Subscription model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_subscription_auto_creation(self):
        """Test that subscription is automatically created for new users"""
        self.assertTrue(hasattr(self.user, 'subscription'))
        self.assertEqual(self.user.subscription.tier, SubscriptionTier.FREE)
        self.assertEqual(self.user.subscription.max_interval_days, 3)
    
    def test_subscription_tier_update(self):
        """Test subscription tier update updates max_interval_days"""
        subscription = self.user.subscription
        
        # Upgrade to BASIC
        subscription.tier = SubscriptionTier.BASIC
        subscription.save()
        subscription.refresh_from_db()
        self.assertEqual(subscription.max_interval_days, 90)
        
        # Upgrade to PRO
        subscription.tier = SubscriptionTier.PRO
        subscription.save()
        subscription.refresh_from_db()
        self.assertEqual(subscription.max_interval_days, 180)
    
    def test_subscription_is_expired(self):
        subscription = self.user.subscription
        
        # No end date - not expired
        self.assertFalse(subscription.is_expired())
        
        # Future end date - not expired
        subscription.end_date = timezone.now() + timedelta(days=30)
        subscription.save()
        self.assertFalse(subscription.is_expired())
        
        # Past end date - expired
        subscription.end_date = timezone.now() - timedelta(days=1)
        subscription.save()
        self.assertTrue(subscription.is_expired())
    
    def test_days_remaining(self):
        subscription = self.user.subscription
        
        # No end date
        self.assertIsNone(subscription.days_remaining())
        
        # Future end date
        subscription.end_date = timezone.now() + timedelta(days=30)
        subscription.save()
        remaining = subscription.days_remaining()
        self.assertGreaterEqual(remaining, 29)
        self.assertLessEqual(remaining, 30)


class AIUsageTrackingTest(TestCase):
    """Test AIUsageTracking model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_get_or_create_for_today(self):
        # First call should create new record
        usage = AIUsageTracking.get_or_create_for_today(self.user)
        self.assertEqual(usage.user, self.user)
        self.assertEqual(usage.questions_generated, 0)
        
        # Second call should return existing record
        usage2 = AIUsageTracking.get_or_create_for_today(self.user)
        self.assertEqual(usage.id, usage2.id)
    
    def test_can_generate_questions(self):
        usage = AIUsageTracking.get_or_create_for_today(self.user)
        
        # User with FREE tier cannot generate questions
        self.assertFalse(usage.can_generate_questions(1))
        
        # User with BASIC tier can generate questions
        self.user.subscription.tier = SubscriptionTier.BASIC
        self.user.subscription.save()
        self.assertTrue(usage.can_generate_questions(1))
        self.assertTrue(usage.can_generate_questions(30))
        self.assertFalse(usage.can_generate_questions(31))
        
        # After using some quota
        usage.questions_generated = 25
        usage.save()
        self.assertTrue(usage.can_generate_questions(5))
        self.assertFalse(usage.can_generate_questions(6))


class AuthenticationAPITest(APITestCase):
    """Test Authentication API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
    
    def test_user_registration(self):
        """Test user registration"""
        url = reverse('accounts:users-register')
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
        
        # Check response data
        self.assertIn('user', response.data['data'])
        self.assertIn('requires_email_verification', response.data['data'])
    
    def test_user_registration_password_mismatch(self):
        """Test registration with password mismatch"""
        url = reverse('accounts:users-register')
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'differentpass',
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email"""
        url = reverse('accounts:users-register')
        data = {
            'email': 'test@example.com',  # Already exists
            'password': 'newpass123',
            'password_confirm': 'newpass123',
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_login(self):
        """Test user login with email"""
        url = reverse('token_obtain_pair')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        url = reverse('token_obtain_pair')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpass'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    @override_settings(ENFORCE_EMAIL_VERIFICATION=True)
    def test_user_login_unverified_email(self):
        """Test login with unverified email"""
        self.user.is_email_verified = False
        self.user.save()
        
        url = reverse('token_obtain_pair')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_token_refresh(self):
        """Test JWT token refresh"""
        refresh = RefreshToken.for_user(self.user)
        
        url = reverse('token_refresh')
        data = {'refresh': str(refresh)}
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_profile_view_get(self):
        """Test get user profile"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('accounts:profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertIn('subscription', response.data)
    
    def test_profile_view_update(self):
        """Test update user profile"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('accounts:profile')
        data = {
            'username': 'newusername',
            'weekly_goal': 10
        }
        
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newusername')
        self.assertEqual(self.user.weekly_goal, 10)
    
    def test_password_change(self):
        """Test password change"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('accounts:password-change')
        data = {
            'current_password': 'testpass123',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))
    
    def test_password_change_wrong_current_password(self):
        """Test password change with wrong current password"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('accounts:password-change')
        data = {
            'current_password': 'wrongpass',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GoogleOAuthTest(TestCase):
    """Test Google OAuth functionality"""
    
    @patch('accounts.google_auth.id_token.verify_oauth2_token')
    def test_verify_google_token_success(self, mock_verify):
        """Test successful Google token verification"""
        mock_verify.return_value = {
            'iss': 'accounts.google.com',
            'email': 'test@gmail.com',
            'given_name': 'Test',
            'family_name': 'User',
            'name': 'Test User'
        }
        
        with override_settings(SOCIALACCOUNT_PROVIDERS={'google': {'APP': {'client_id': 'test-client-id'}}}):
            result = GoogleAuthService.verify_google_token('fake-token')
            
            self.assertEqual(result['email'], 'test@gmail.com')
            self.assertEqual(result['given_name'], 'Test')
    
    @patch('accounts.google_auth.id_token.verify_oauth2_token')
    def test_verify_google_token_invalid_issuer(self, mock_verify):
        """Test Google token verification with invalid issuer"""
        mock_verify.return_value = {
            'iss': 'evil.com',
            'email': 'test@gmail.com'
        }
        
        with override_settings(SOCIALACCOUNT_PROVIDERS={'google': {'APP': {'client_id': 'test-client-id'}}}):
            with self.assertRaises(GoogleOAuthError):
                GoogleAuthService.verify_google_token('fake-token')
    
    def test_get_or_create_user_existing(self):
        """Test getting existing user with Google OAuth"""
        existing_user = User.objects.create_user(
            email='test@gmail.com',
            password='password'
        )
        existing_user.is_email_verified = False
        existing_user.save()
        
        google_info = {
            'email': 'test@gmail.com',
            'given_name': 'Test',
            'family_name': 'User'
        }
        
        user, created = GoogleAuthService.get_or_create_user(google_info)
        
        self.assertFalse(created)
        self.assertEqual(user, existing_user)
        self.assertTrue(user.is_email_verified)  # Should be verified after Google OAuth
    
    def test_get_or_create_user_new(self):
        """Test creating new user with Google OAuth"""
        google_info = {
            'email': 'newuser@gmail.com',
            'given_name': 'New',
            'family_name': 'User'
        }
        
        user, created = GoogleAuthService.get_or_create_user(google_info)
        
        self.assertTrue(created)
        self.assertEqual(user.email, 'newuser@gmail.com')
        self.assertTrue(user.is_email_verified)
        self.assertFalse(user.has_usable_password())


class SubscriptionAPITest(APITestCase):
    """Test Subscription API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_subscription_detail(self):
        """Test get subscription details"""
        url = reverse('accounts:subscription-detail')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tier'], SubscriptionTier.FREE)
        self.assertEqual(response.data['max_interval_days'], 3)
    
    def test_subscription_tiers(self):
        """Test get subscription tiers"""
        url = reverse('accounts:subscription-tiers')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # FREE, BASIC, PRO
        
        # Check tier structure
        free_tier = next(tier for tier in response.data if tier['name'] == 'free')
        self.assertEqual(free_tier['max_days'], 3)
        self.assertEqual(free_tier['price'], 0)
    
    def test_subscription_upgrade_success(self):
        """Test successful subscription upgrade"""
        url = reverse('accounts:subscription-upgrade')
        data = {'tier': SubscriptionTier.BASIC}
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription.tier, SubscriptionTier.BASIC)
        self.assertEqual(self.user.subscription.max_interval_days, 90)
    
    @override_settings(ENFORCE_EMAIL_VERIFICATION=True)
    def test_subscription_upgrade_unverified_email(self):
        """Test subscription upgrade with unverified email"""
        self.user.is_email_verified = False
        self.user.save()
        
        url = reverse('accounts:subscription-upgrade')
        data = {'tier': SubscriptionTier.BASIC}
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SerializerTest(TestCase):
    """Test serializers"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_serializer(self):
        """Test UserSerializer"""
        serializer = UserSerializer(self.user)
        
        self.assertEqual(serializer.data['email'], 'test@example.com')
        self.assertIn('subscription', serializer.data)
        self.assertFalse(serializer.data['is_email_verified'])
    
    def test_user_registration_serializer_valid(self):
        """Test UserRegistrationSerializer with valid data"""
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertTrue(user.check_password('newpass123'))
    
    def test_user_registration_serializer_password_mismatch(self):
        """Test UserRegistrationSerializer with password mismatch"""
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'differentpass'
        }
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password_confirm', serializer.errors)
    
    def test_password_change_serializer(self):
        """Test PasswordChangeSerializer"""
        data = {
            'current_password': 'testpass123',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        
        serializer = PasswordChangeSerializer(
            data=data,
            context={'request': type('Request', (), {'user': self.user})()}
        )
        
        self.assertTrue(serializer.is_valid())
    
    def test_email_token_serializer_valid(self):
        """Test EmailTokenObtainPairSerializer with valid credentials"""
        self.user.is_email_verified = True
        self.user.save()
        
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        serializer = EmailTokenObtainPairSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertIn('access', serializer.validated_data)
        self.assertIn('refresh', serializer.validated_data)