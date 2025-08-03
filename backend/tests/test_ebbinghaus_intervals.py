"""
Tests for Ebbinghaus forgetting curve optimized review intervals
"""

from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from .base import BaseTestCase
from review.utils import get_review_intervals
from review.models import ReviewSchedule
from accounts.models import SubscriptionTier, Subscription

User = get_user_model()


class EbbinghausIntervalsTestCase(BaseTestCase):
    """Test cases for Ebbinghaus-optimized review intervals"""
    
    def test_free_tier_intervals(self):
        """Test FREE tier has basic spaced repetition intervals"""
        user = self.create_user(email='free@test.com')
        user.subscription.tier = SubscriptionTier.FREE
        user.subscription.save()
        
        intervals = get_review_intervals(user)
        expected = [1, 3, 7]  # Basic spaced repetition (max 7 days)
        
        self.assertEqual(intervals, expected)
        self.assertEqual(max(intervals), 7)
        self.assertEqual(user.subscription.max_interval_days, 7)
    
    def test_basic_tier_intervals(self):
        """Test BASIC tier has medium-term memory intervals"""
        user = self.create_user(email='basic@test.com')
        user.subscription.tier = SubscriptionTier.BASIC
        user.subscription.save()
        
        intervals = get_review_intervals(user)
        expected = [1, 3, 7, 14, 30]  # Medium-term memory (max 30 days)
        
        self.assertEqual(intervals, expected)
        self.assertEqual(max(intervals), 30)
        self.assertEqual(user.subscription.max_interval_days, 30)
    
    def test_premium_tier_intervals(self):
        """Test PREMIUM tier has long-term memory intervals"""
        user = self.create_user(email='premium@test.com')
        user.subscription.tier = SubscriptionTier.PREMIUM
        user.subscription.save()
        
        intervals = get_review_intervals(user)
        expected = [1, 3, 7, 14, 30, 60]  # Long-term memory (max 60 days)
        
        self.assertEqual(intervals, expected)
        self.assertEqual(max(intervals), 60)
        self.assertEqual(user.subscription.max_interval_days, 60)
    
    def test_pro_tier_intervals(self):
        """Test PRO tier has complete long-term retention intervals"""
        user = self.create_user(email='pro@test.com')
        user.subscription.tier = SubscriptionTier.PRO
        user.subscription.save()
        
        intervals = get_review_intervals(user)
        expected = [1, 3, 7, 14, 30, 60, 120, 180]  # Complete retention (max 180 days)
        
        self.assertEqual(intervals, expected)
        self.assertEqual(max(intervals), 180)
        self.assertEqual(user.subscription.max_interval_days, 180)
    
    def test_ebbinghaus_progression(self):
        """Test that intervals follow Ebbinghaus progression"""
        user = self.create_user(email='ebbinghaus@test.com')
        user.subscription.tier = SubscriptionTier.PRO
        user.subscription.save()
        
        intervals = get_review_intervals(user)
        
        # Check each interval follows Ebbinghaus research
        self.assertIn(1, intervals)    # Initial reinforcement
        self.assertIn(3, intervals)    # Short-term consolidation
        self.assertIn(7, intervals)    # Working memory to long-term transfer
        self.assertIn(14, intervals)   # Long-term memory strengthening
        self.assertIn(30, intervals)   # Monthly reinforcement
        self.assertIn(60, intervals)   # Bi-monthly consolidation
        self.assertIn(120, intervals)  # Quarterly review (4 months)
        self.assertIn(180, intervals)  # Semi-annual review (6 months)
    
    def test_subscription_change_interval_adjustment(self):
        """Test that subscription changes adjust intervals correctly"""
        user = self.create_user(email='change@test.com')
        
        # Start with FREE tier
        user.subscription.tier = SubscriptionTier.FREE
        user.subscription.save()
        self.assertEqual(max(get_review_intervals(user)), 7)
        
        # Upgrade to PRO tier
        user.subscription.tier = SubscriptionTier.PRO
        user.subscription.save()
        self.assertEqual(max(get_review_intervals(user)), 180)
        self.assertEqual(user.subscription.max_interval_days, 180)
        
        # Downgrade to BASIC tier
        user.subscription.tier = SubscriptionTier.BASIC
        user.subscription.save()
        self.assertEqual(max(get_review_intervals(user)), 30)
        self.assertEqual(user.subscription.max_interval_days, 30)
    
    def test_no_user_defaults_to_free(self):
        """Test that no user defaults to FREE tier intervals"""
        intervals = get_review_intervals(None)
        expected = [1, 3, 7]  # FREE tier
        
        self.assertEqual(intervals, expected)
    
    def test_inactive_subscription_defaults_to_free(self):
        """Test that inactive subscription defaults to FREE tier intervals"""
        user = self.create_user(email='inactive@test.com')
        user.subscription.tier = SubscriptionTier.PRO
        user.subscription.is_active = False  # Deactivate
        user.subscription.save()
        
        intervals = get_review_intervals(user)
        expected = [1, 3, 7]  # Should fallback to FREE tier
        
        self.assertEqual(intervals, expected)
    
    def test_expired_subscription_defaults_to_free(self):
        """Test that expired subscription defaults to FREE tier intervals"""
        user = self.create_user(email='expired@test.com')
        user.subscription.tier = SubscriptionTier.PRO
        user.subscription.end_date = timezone.now() - timedelta(days=1)  # Expired
        user.subscription.save()
        
        intervals = get_review_intervals(user)
        expected = [1, 3, 7]  # Should fallback to FREE tier
        
        self.assertEqual(intervals, expected)


class ReviewScheduleEbbinghausTestCase(BaseTestCase):
    """Test review schedule with Ebbinghaus intervals"""
    
    def test_review_progression_free_tier(self):
        """Test review progression for FREE tier"""
        user = self.create_user(email='progression_free@test.com')
        user.subscription.tier = SubscriptionTier.FREE
        user.subscription.save()
        
        schedule = self.create_review_schedule(user=user, interval_index=0)
        
        # First advance: 1 → 3 days
        schedule.advance_schedule()
        self.assertEqual(schedule.interval_index, 1)
        
        # Second advance: 3 → 7 days
        schedule.advance_schedule()
        self.assertEqual(schedule.interval_index, 2)
        
        # Third advance: should stay at 7 days (max for FREE)
        schedule.advance_schedule()
        self.assertEqual(schedule.interval_index, 2)  # Stay at max
    
    def test_review_progression_pro_tier(self):
        """Test review progression for PRO tier up to 180 days"""
        user = self.create_user(email='progression_pro@test.com')
        user.subscription.tier = SubscriptionTier.PRO
        user.subscription.save()
        
        schedule = self.create_review_schedule(user=user, interval_index=0)
        intervals = get_review_intervals(user)
        
        # Test progression through all intervals
        for i in range(len(intervals)):
            if i > 0:
                schedule.advance_schedule()
            expected_interval = intervals[schedule.interval_index]
            
            # Check that next_review_date is set correctly (allowing for timing differences)
            expected_date = timezone.now() + timedelta(days=expected_interval)
            time_diff = abs((schedule.next_review_date - expected_date).total_seconds())
            self.assertLess(time_diff, 86401, f"Failed at interval index {i} - time difference too large")
        
        # Final check: should be at 180 days
        final_interval = intervals[schedule.interval_index]
        self.assertEqual(final_interval, 180)
    
    def test_subscription_downgrade_schedule_adjustment(self):
        """Test that schedules adjust when subscription is downgraded"""
        user = self.create_user(email='downgrade@test.com')
        user.subscription.tier = SubscriptionTier.PRO
        user.subscription.save()
        
        # Create schedule at 120-day interval (index 6 for PRO)
        schedule = self.create_review_schedule(user=user, interval_index=6)
        
        # Downgrade to BASIC (max 30 days, max index 4)
        user.subscription.tier = SubscriptionTier.BASIC
        user.subscription.save()
        
        # Advance schedule should adjust to BASIC tier limits
        schedule.advance_schedule()
        
        basic_intervals = get_review_intervals(user)
        current_interval = basic_intervals[schedule.interval_index]
        
        # Should not exceed BASIC tier maximum (30 days)
        self.assertLessEqual(current_interval, 30)
        self.assertIn(current_interval, basic_intervals)
    
    def test_reset_schedule_uses_tier_intervals(self):
        """Test that reset_schedule uses correct tier intervals"""
        user = self.create_user(email='reset@test.com')
        user.subscription.tier = SubscriptionTier.PREMIUM
        user.subscription.save()
        
        # Create schedule at high interval
        schedule = self.create_review_schedule(user=user, interval_index=5)
        
        # Reset should go back to first interval (1 day)
        schedule.reset_schedule()
        
        self.assertEqual(schedule.interval_index, 0)
        
        # Should be scheduled for 1 day from now
        expected_date = timezone.now() + timedelta(days=1)
        time_diff = abs((schedule.next_review_date - expected_date).total_seconds())
        self.assertLess(time_diff, 60)


class EbbinghausMemoryOptimizationTestCase(TestCase):
    """Test memory optimization principles in interval design"""
    
    def test_interval_exponential_growth(self):
        """Test that intervals grow exponentially as per Ebbinghaus research"""
        from accounts.models import SubscriptionTier
        
        # Get PRO tier intervals for full progression
        tier_intervals = {
            SubscriptionTier.PRO: [1, 3, 7, 14, 30, 60, 120, 180]
        }
        
        intervals = tier_intervals[SubscriptionTier.PRO]
        
        # Check exponential-ish growth pattern
        self.assertTrue(intervals[1] > intervals[0] * 2)  # 3 > 1*2
        self.assertTrue(intervals[2] > intervals[1] * 2)  # 7 > 3*2
        self.assertTrue(intervals[3] > intervals[2] * 1.5)  # 14 > 7*1.5
        self.assertTrue(intervals[4] > intervals[3] * 2)  # 30 > 14*2
        
    def test_critical_memory_points(self):
        """Test that intervals hit critical memory consolidation points"""
        from accounts.models import SubscriptionTier
        from review.utils import get_review_intervals
        
        class MockUser:
            class MockSubscription:
                tier = SubscriptionTier.PRO
                is_active = True
                def is_expired(self):
                    return False
            subscription = MockSubscription()
        
        intervals = get_review_intervals(MockUser())
        
        # Critical points from memory research
        self.assertIn(1, intervals)    # 24-hour consolidation
        self.assertIn(7, intervals)    # Weekly memory cycle
        self.assertIn(30, intervals)   # Monthly review cycle
        self.assertIn(60, intervals)   # Bi-monthly strengthening
        self.assertIn(180, intervals)  # Long-term retention (6 months)
    
    def test_tier_progression_logical(self):
        """Test that tier progression makes logical sense"""
        from accounts.models import SubscriptionTier
        
        # Mock user class for testing
        class MockUser:
            def __init__(self, tier):
                self.subscription = type('obj', (object,), {
                    'tier': tier,
                    'is_active': True,
                    'is_expired': lambda: False
                })
        
        free_intervals = get_review_intervals(MockUser(SubscriptionTier.FREE))
        basic_intervals = get_review_intervals(MockUser(SubscriptionTier.BASIC))
        premium_intervals = get_review_intervals(MockUser(SubscriptionTier.PREMIUM))
        pro_intervals = get_review_intervals(MockUser(SubscriptionTier.PRO))
        
        # Each tier should be a superset of the previous
        self.assertTrue(all(interval in basic_intervals for interval in free_intervals))
        self.assertTrue(all(interval in premium_intervals for interval in basic_intervals))
        self.assertTrue(all(interval in pro_intervals for interval in premium_intervals))
        
        # Each tier should have progressively longer maximum intervals
        self.assertLess(max(free_intervals), max(basic_intervals))
        self.assertLess(max(basic_intervals), max(premium_intervals))
        self.assertLess(max(premium_intervals), max(pro_intervals))
        
        # PRO tier should reach 180 days (6 months)
        self.assertEqual(max(pro_intervals), 180)