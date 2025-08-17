"""
Test cases for subscription API endpoints
"""
import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Subscription, SubscriptionTier

User = get_user_model()


class SubscriptionAPITest(TestCase):
    """Test subscription API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test users
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        self.unverified_user = User.objects.create_user(
            email='unverified@example.com',
            password='testpass123'
        )
        
        # Get JWT tokens
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        unverified_refresh = RefreshToken.for_user(self.unverified_user)
        self.unverified_access_token = str(unverified_refresh.access_token)
    
    def test_get_subscription_info_authenticated(self):
        """Test getting subscription info for authenticated user"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        response = self.client.get('/api/accounts/subscription/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['tier'], 'free')
        self.assertEqual(data['max_interval_days'], 7)
        self.assertTrue(data['is_active'])
        self.assertIsNone(data['end_date'])
    
    def test_get_subscription_info_unauthenticated(self):
        """Test getting subscription info without authentication"""
        response = self.client.get('/api/accounts/subscription/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_subscription_tiers(self):
        """Test getting available subscription tiers"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        response = self.client.get('/api/accounts/subscription/tiers/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check that all tiers are present
        tier_names = [tier['name'] for tier in data]
        self.assertIn('free', tier_names)
        self.assertIn('basic', tier_names)
        self.assertIn('premium', tier_names)
        self.assertIn('pro', tier_names)
        
        # Check tier details
        free_tier = next(tier for tier in data if tier['name'] == 'free')
        self.assertEqual(free_tier['max_days'], 7)
        self.assertEqual(free_tier['price'], 0)
        
        pro_tier = next(tier for tier in data if tier['name'] == 'pro')
        self.assertEqual(pro_tier['max_days'], 90)
    
    def test_upgrade_subscription_with_verified_email(self):
        """Test upgrading subscription with verified email"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        response = self.client.post(
            '/api/accounts/subscription/upgrade/',
            data={'tier': 'premium'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['tier'], 'premium')
        self.assertEqual(data['max_interval_days'], 60)
        
        # Verify in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscription.tier, SubscriptionTier.PREMIUM)
    
    def test_upgrade_subscription_without_verified_email(self):
        """Test upgrading subscription without verified email"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.unverified_access_token}')
        
        response = self.client.post(
            '/api/accounts/subscription/upgrade/',
            data={'tier': 'premium'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        data = response.json()
        self.assertIn('email_verified', data)
        self.assertFalse(data['email_verified'])
    
    def test_upgrade_to_invalid_tier(self):
        """Test upgrading to invalid tier"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        response = self.client.post(
            '/api/accounts/subscription/upgrade/',
            data={'tier': 'invalid_tier'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_upgrade_from_pro_tier(self):
        """Test that PRO users cannot upgrade further"""
        # Set user to PRO tier
        self.user.subscription.tier = SubscriptionTier.PRO
        self.user.subscription.save()
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        response = self.client.post(
            '/api/accounts/subscription/upgrade/',
            data={'tier': 'pro'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        # Check for error in either 'error' field or nested in 'tier' field
        error_msg = data.get('error', '') or str(data.get('tier', [''])[0])
        self.assertIn('already at highest', error_msg.lower())
    
    def test_downgrade_subscription(self):
        """Test downgrading subscription"""
        # Set user to PREMIUM tier
        self.user.subscription.tier = SubscriptionTier.PREMIUM
        self.user.subscription.save()
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        response = self.client.post(
            '/api/accounts/subscription/upgrade/',
            data={'tier': 'basic'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['tier'], 'basic')
        self.assertEqual(data['max_interval_days'], 30)
    
    def test_subscription_serialization(self):
        """Test subscription serialization includes all required fields"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Set a specific end date
        end_date = timezone.now() + timedelta(days=30)
        self.user.subscription.end_date = end_date
        self.user.subscription.save()
        
        response = self.client.get('/api/accounts/subscription/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check all required fields are present
        required_fields = [
            'id', 'tier', 'max_interval_days', 'start_date',
            'end_date', 'is_active', 'days_remaining', 'is_expired'
        ]
        for field in required_fields:
            self.assertIn(field, data)
        
        # Check calculated fields
        self.assertFalse(data['is_expired'])
        self.assertIsNotNone(data['days_remaining'])


class SubscriptionIntegrationTest(TestCase):
    """Test subscription integration with other features"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Create test content
        from content.models import Category, Content
        
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
        
        self.content = Content.objects.create(
            title='Test Content',
            content='Test body',
            author=self.user,
            category=self.category
        )
    
    def test_review_intervals_update_with_subscription(self):
        """Test that review intervals update when subscription changes"""
        from review.models import ReviewSchedule

        # Create review schedule
        schedule = ReviewSchedule.objects.create(
            content=self.content,
            user=self.user,
            next_review_date=timezone.now(),
            interval_index=2  # At max for free tier
        )
        
        # Get current review info
        response = self.client.get(f'/api/review/schedules/{schedule.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Upgrade subscription
        response = self.client.post(
            '/api/accounts/subscription/upgrade/',
            data={'tier': 'premium'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user can now advance beyond free tier limits
        from review.utils import get_review_intervals

        # Refresh user from DB to get updated subscription
        self.user.refresh_from_db()
        intervals = get_review_intervals(self.user)
        self.assertEqual(len(intervals), 8)  # Premium tier has 8 intervals