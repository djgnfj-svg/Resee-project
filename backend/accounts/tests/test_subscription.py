"""
Tests for subscription services and utilities.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Subscription, SubscriptionTier
from accounts.subscription import tier_utils

User = get_user_model()


class TierUtilsTest(TestCase):
    """Test tier utility functions."""

    def test_get_max_interval_free(self):
        """Test get_max_interval for FREE tier."""
        max_interval = tier_utils.get_max_interval(SubscriptionTier.FREE)
        self.assertEqual(max_interval, 3)

    def test_get_max_interval_basic(self):
        """Test get_max_interval for BASIC tier."""
        max_interval = tier_utils.get_max_interval(SubscriptionTier.BASIC)
        self.assertEqual(max_interval, 90)

    def test_get_max_interval_pro(self):
        """Test get_max_interval for PRO tier."""
        max_interval = tier_utils.get_max_interval(SubscriptionTier.PRO)
        self.assertEqual(max_interval, 180)

    def test_get_tier_level(self):
        """Test get_tier_level function."""
        self.assertEqual(tier_utils.get_tier_level(SubscriptionTier.FREE), 0)
        self.assertEqual(tier_utils.get_tier_level(SubscriptionTier.BASIC), 1)
        self.assertEqual(tier_utils.get_tier_level(SubscriptionTier.PRO), 2)

    def test_is_upgrade(self):
        """Test is_upgrade function."""
        self.assertTrue(tier_utils.is_upgrade(SubscriptionTier.FREE, SubscriptionTier.BASIC))
        self.assertTrue(tier_utils.is_upgrade(SubscriptionTier.BASIC, SubscriptionTier.PRO))
        self.assertFalse(tier_utils.is_upgrade(SubscriptionTier.BASIC, SubscriptionTier.FREE))
        self.assertFalse(tier_utils.is_upgrade(SubscriptionTier.BASIC, SubscriptionTier.BASIC))

    def test_is_downgrade(self):
        """Test is_downgrade function."""
        self.assertTrue(tier_utils.is_downgrade(SubscriptionTier.BASIC, SubscriptionTier.FREE))
        self.assertTrue(tier_utils.is_downgrade(SubscriptionTier.PRO, SubscriptionTier.BASIC))
        self.assertFalse(tier_utils.is_downgrade(SubscriptionTier.FREE, SubscriptionTier.BASIC))
        self.assertFalse(tier_utils.is_downgrade(SubscriptionTier.BASIC, SubscriptionTier.BASIC))

    def test_can_change_tier(self):
        """Test can_change_tier function."""
        self.assertTrue(tier_utils.can_change_tier(SubscriptionTier.FREE, SubscriptionTier.BASIC))
        self.assertFalse(tier_utils.can_change_tier(SubscriptionTier.BASIC, SubscriptionTier.BASIC))

    def test_get_monthly_price(self):
        """Test get_monthly_price function."""
        price = tier_utils.get_monthly_price(SubscriptionTier.FREE)
        self.assertIsInstance(price, Decimal)

    def test_calculate_price(self):
        """Test calculate_price function."""
        price = tier_utils.calculate_price(SubscriptionTier.BASIC)
        self.assertIsInstance(price, Decimal)

    def test_get_content_limit(self):
        """Test get_content_limit function."""
        limit = tier_utils.get_content_limit(SubscriptionTier.FREE)
        self.assertIsInstance(limit, int)

    def test_get_category_limit(self):
        """Test get_category_limit function."""
        limit = tier_utils.get_category_limit(SubscriptionTier.FREE)
        self.assertIsInstance(limit, int)

    def test_get_features(self):
        """Test get_features function."""
        features = tier_utils.get_features(SubscriptionTier.FREE)
        self.assertIsInstance(features, list)

    def test_get_tier_info(self):
        """Test get_tier_info function."""
        info = tier_utils.get_tier_info(SubscriptionTier.BASIC)
        self.assertIsInstance(info, dict)
        self.assertIn('tier', info)
        self.assertIn('max_interval_days', info)

    def test_get_all_tiers_info(self):
        """Test get_all_tiers_info function."""
        all_tiers = tier_utils.get_all_tiers_info()
        self.assertIsInstance(all_tiers, list)
        self.assertEqual(len(all_tiers), 3)

    def test_calculate_prorated_refund(self):
        """Test calculate_prorated_refund function."""
        refund = tier_utils.calculate_prorated_refund(
            current_price=Decimal('100.00'),
            days_remaining=15,
            total_days=30
        )
        self.assertIsInstance(refund, Decimal)
        self.assertEqual(refund, Decimal('50.00'))


class SubscriptionViewsTest(TestCase):
    """Test subscription views."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.client.force_authenticate(user=self.user)

    def test_subscription_detail(self):
        """Test getting subscription details."""
        response = self.client.get('/api/accounts/subscription/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tier', response.data)

    def test_subscription_tiers(self):
        """Test getting available tiers."""
        response = self.client.get('/api/accounts/subscription/tiers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tiers', response.data)
        self.assertIn('billing_cycle', response.data)
        self.assertEqual(response.data['billing_cycle'], 'monthly')
        self.assertIsInstance(response.data['tiers'], list)
        self.assertEqual(len(response.data['tiers']), 3)  # FREE, BASIC, PRO

    def test_subscription_detail_unauthenticated(self):
        """Test subscription detail without authentication."""
        self.client.logout()
        response = self.client.get('/api/accounts/subscription/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
