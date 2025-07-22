"""
Test cases for subscription-related utilities
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from accounts.models import Subscription, SubscriptionTier
from review.utils import get_review_intervals

User = get_user_model()


class SubscriptionUtilsTest(TestCase):
    """Test subscription-related utility functions"""
    
    def setUp(self):
        """Create test users with different subscriptions"""
        self.free_user = User.objects.create_user(
            email='free@example.com',
            password='testpass123'
        )
        
        self.basic_user = User.objects.create_user(
            email='basic@example.com',
            password='testpass123'
        )
        self.basic_user.subscription.tier = SubscriptionTier.BASIC
        self.basic_user.subscription.save()
        
        self.premium_user = User.objects.create_user(
            email='premium@example.com',
            password='testpass123'
        )
        self.premium_user.subscription.tier = SubscriptionTier.PREMIUM
        self.premium_user.subscription.save()
        
        self.pro_user = User.objects.create_user(
            email='pro@example.com',
            password='testpass123'
        )
        self.pro_user.subscription.tier = SubscriptionTier.PRO
        self.pro_user.subscription.save()
    
    def test_get_review_intervals_for_free_user(self):
        """Test review intervals for free tier user"""
        intervals = get_review_intervals(self.free_user)
        expected_intervals = [1, 3, 7]
        self.assertEqual(intervals, expected_intervals)
    
    def test_get_review_intervals_for_basic_user(self):
        """Test review intervals for basic tier user"""
        intervals = get_review_intervals(self.basic_user)
        expected_intervals = [1, 3, 7, 14, 21, 30]
        self.assertEqual(intervals, expected_intervals)
    
    def test_get_review_intervals_for_premium_user(self):
        """Test review intervals for premium tier user"""
        intervals = get_review_intervals(self.premium_user)
        expected_intervals = [1, 3, 7, 14, 21, 30, 45, 60]
        self.assertEqual(intervals, expected_intervals)
    
    def test_get_review_intervals_for_pro_user(self):
        """Test review intervals for pro tier user"""
        intervals = get_review_intervals(self.pro_user)
        expected_intervals = [1, 3, 7, 14, 21, 30, 45, 60, 75, 90]
        self.assertEqual(intervals, expected_intervals)
    
    def test_get_review_intervals_for_expired_subscription(self):
        """Test review intervals for user with expired subscription"""
        # Set subscription as expired
        self.premium_user.subscription.end_date = timezone.now() - timedelta(days=1)
        self.premium_user.subscription.save()
        
        intervals = get_review_intervals(self.premium_user)
        expected_intervals = [1, 3, 7]  # Should fall back to free tier
        self.assertEqual(intervals, expected_intervals)
    
    def test_get_review_intervals_for_inactive_subscription(self):
        """Test review intervals for user with inactive subscription"""
        # Set subscription as inactive
        self.basic_user.subscription.is_active = False
        self.basic_user.subscription.save()
        
        intervals = get_review_intervals(self.basic_user)
        expected_intervals = [1, 3, 7]  # Should fall back to free tier
        self.assertEqual(intervals, expected_intervals)
    
    def test_get_review_intervals_for_user_without_subscription(self):
        """Test review intervals for user without subscription"""
        # Delete subscription
        self.free_user.subscription.delete()
        
        intervals = get_review_intervals(self.free_user)
        expected_intervals = [1, 3, 7]  # Should use free tier default
        self.assertEqual(intervals, expected_intervals)


class ReviewScheduleSubscriptionTest(TestCase):
    """Test ReviewSchedule model with subscription-based intervals"""
    
    def setUp(self):
        """Create test user and content"""
        from content.models import Content, Category
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
        
        self.content = Content.objects.create(
            title='Test Content',
            content='Test content body',
            author=self.user,
            category=self.category
        )
    
    def test_review_schedule_respects_subscription_limits(self):
        """Test that review schedules respect subscription tier limits"""
        from review.models import ReviewSchedule
        
        schedule = ReviewSchedule.objects.create(
            content=self.content,
            user=self.user,
            next_review_date=timezone.now(),
            interval_index=0
        )
        
        # Free user should only advance through limited intervals
        for i in range(5):  # Try to advance 5 times
            schedule.advance_schedule()
        
        # Check that interval_index doesn't exceed free tier limits
        intervals = get_review_intervals(self.user)
        self.assertLessEqual(schedule.interval_index, len(intervals) - 1)
    
    def test_review_schedule_with_upgraded_subscription(self):
        """Test review schedule behavior when subscription is upgraded"""
        from review.models import ReviewSchedule
        
        schedule = ReviewSchedule.objects.create(
            content=self.content,
            user=self.user,
            next_review_date=timezone.now(),
            interval_index=2  # At max for free tier
        )
        
        # Advance to the end of free tier
        schedule.advance_schedule()
        old_interval_index = schedule.interval_index
        
        # Upgrade to premium
        self.user.subscription.tier = SubscriptionTier.PREMIUM
        self.user.subscription.save()
        
        # Now should be able to advance further
        schedule.advance_schedule()
        self.assertGreater(schedule.interval_index, old_interval_index)
    
    def test_review_schedule_with_downgraded_subscription(self):
        """Test review schedule behavior when subscription is downgraded"""
        from review.models import ReviewSchedule
        
        # Start with premium user
        self.user.subscription.tier = SubscriptionTier.PREMIUM
        self.user.subscription.save()
        
        schedule = ReviewSchedule.objects.create(
            content=self.content,
            user=self.user,
            next_review_date=timezone.now(),
            interval_index=5  # Beyond free tier limit
        )
        
        # Downgrade to free
        self.user.subscription.tier = SubscriptionTier.FREE
        self.user.subscription.save()
        
        # Schedule should still work but not advance beyond free tier limits
        current_index = schedule.interval_index
        schedule.advance_schedule()
        
        # Should stay at current interval since it's already beyond free tier
        intervals = get_review_intervals(self.user)
        self.assertEqual(schedule.interval_index, min(current_index + 1, len(intervals) - 1))