"""
Test cases for subscription models
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from accounts.models import Subscription, SubscriptionTier

User = get_user_model()


class SubscriptionModelTest(TestCase):
    """Test Subscription model functionality"""
    
    def setUp(self):
        """Create test user"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_subscription_defaults_to_free(self):
        """Test that new subscription defaults to FREE tier"""
        # Delete auto-created subscription first
        if hasattr(self.user, 'subscription'):
            self.user.subscription.delete()
            
        subscription = Subscription.objects.create(user=self.user)
        
        self.assertEqual(subscription.tier, SubscriptionTier.FREE)
        self.assertEqual(subscription.max_interval_days, 7)
        self.assertTrue(subscription.is_active)
        self.assertIsNotNone(subscription.start_date)
        self.assertIsNone(subscription.end_date)
    
    def test_subscription_tier_choices(self):
        """Test all subscription tier choices"""
        tiers = [
            (SubscriptionTier.FREE, 7),
            (SubscriptionTier.BASIC, 30),
            (SubscriptionTier.PREMIUM, 60),
            (SubscriptionTier.PRO, 90),
        ]
        
        for tier, expected_days in tiers:
            test_user = User.objects.create_user(
                email=f'{tier}@example.com',
                password='testpass123'
            )
            # Update the auto-created subscription
            subscription = test_user.subscription
            subscription.tier = tier
            subscription.save()
            
            self.assertEqual(subscription.tier, tier)
            self.assertEqual(subscription.max_interval_days, expected_days)
    
    def test_subscription_unique_per_user(self):
        """Test that each user can have only one subscription"""
        # User already has subscription from signal
        self.assertTrue(hasattr(self.user, 'subscription'))
        
        with self.assertRaises(Exception):
            Subscription.objects.create(user=self.user)
    
    def test_subscription_str_representation(self):
        """Test string representation of subscription"""
        # Update existing subscription
        subscription = self.user.subscription
        subscription.tier = SubscriptionTier.PREMIUM
        subscription.save()
        
        expected = f"{self.user.email} - {SubscriptionTier.PREMIUM.label}"
        self.assertEqual(str(subscription), expected)
    
    def test_subscription_is_expired(self):
        """Test subscription expiration check"""
        # Use existing subscription
        subscription = self.user.subscription
        self.assertFalse(subscription.is_expired())
        
        # Active subscription with future end date
        subscription.end_date = timezone.now() + timedelta(days=30)
        subscription.save()
        self.assertFalse(subscription.is_expired())
        
        # Expired subscription
        subscription.end_date = timezone.now() - timedelta(days=1)
        subscription.save()
        self.assertTrue(subscription.is_expired())
    
    def test_subscription_days_remaining(self):
        """Test days remaining calculation"""
        subscription = self.user.subscription
        
        # No end date means unlimited
        self.assertIsNone(subscription.days_remaining())
        
        # Future end date
        subscription.end_date = timezone.now() + timedelta(days=15)
        subscription.save()
        # Days remaining should be 14 or 15 depending on time of day
        self.assertIn(subscription.days_remaining(), [14, 15])
        
        # Past end date
        subscription.end_date = timezone.now() - timedelta(days=5)
        subscription.save()
        self.assertEqual(subscription.days_remaining(), 0)


class UserSubscriptionMethodsTest(TestCase):
    """Test User model subscription-related methods"""
    
    def setUp(self):
        """Create test user"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_get_max_review_interval_no_subscription(self):
        """Test max review interval when user has no subscription"""
        # Delete the auto-created subscription
        if hasattr(self.user, 'subscription'):
            self.user.subscription.delete()
        
        # Should return FREE tier default
        self.assertEqual(self.user.get_max_review_interval(), 7)
    
    def test_get_max_review_interval_with_subscription(self):
        """Test max review interval with different subscription tiers"""
        tiers_and_intervals = [
            (SubscriptionTier.FREE, 7),
            (SubscriptionTier.BASIC, 30),
            (SubscriptionTier.PREMIUM, 60),
            (SubscriptionTier.PRO, 90),
        ]
        
        subscription = self.user.subscription
        for tier, expected_interval in tiers_and_intervals:
            subscription.tier = tier
            subscription.save()
            self.assertEqual(self.user.get_max_review_interval(), expected_interval)
    
    def test_get_max_review_interval_expired_subscription(self):
        """Test max review interval with expired subscription"""
        subscription = self.user.subscription
        subscription.tier = SubscriptionTier.PREMIUM
        subscription.max_interval_days = 60
        subscription.end_date = timezone.now() - timedelta(days=1)
        subscription.save()
        
        # Should fall back to FREE tier
        self.assertEqual(self.user.get_max_review_interval(), 7)
    
    def test_has_active_subscription(self):
        """Test checking if user has active subscription"""
        # User has auto-created free subscription
        self.assertTrue(self.user.has_active_subscription())
        
        # Free tier is still considered active
        subscription = self.user.subscription
        self.assertEqual(subscription.tier, SubscriptionTier.FREE)
        self.assertTrue(self.user.has_active_subscription())
        
        # Paid tier
        subscription.tier = SubscriptionTier.PREMIUM
        subscription.save()
        self.assertTrue(self.user.has_active_subscription())
        
        # Expired subscription
        subscription.end_date = timezone.now() - timedelta(days=1)
        subscription.save()
        self.assertFalse(self.user.has_active_subscription())
    
    def test_can_upgrade_subscription(self):
        """Test if user can upgrade subscription"""
        # User without email verification cannot upgrade
        self.assertFalse(self.user.can_upgrade_subscription())
        
        # Verify email
        self.user.is_email_verified = True
        self.user.save()
        
        # Now user can upgrade
        self.assertTrue(self.user.can_upgrade_subscription())
        
        # User with PRO subscription cannot upgrade further
        subscription = self.user.subscription
        subscription.tier = SubscriptionTier.PRO
        subscription.save()
        self.assertFalse(self.user.can_upgrade_subscription())


@pytest.mark.django_db
class TestSubscriptionSignals:
    """Test subscription-related signals"""
    
    def test_create_free_subscription_on_user_creation(self):
        """Test that free subscription is created when user is created"""
        user = User.objects.create_user(
            email='newsub@example.com',
            password='testpass123'
        )
        
        # Check subscription was created
        assert hasattr(user, 'subscription')
        assert user.subscription.tier == SubscriptionTier.FREE
        assert user.subscription.max_interval_days == 7
        assert user.subscription.is_active is True
    
    def test_update_review_schedules_on_subscription_change(self):
        """Test that review schedules are updated when subscription changes"""
        # This test will be implemented after review schedule updates are added
        pass