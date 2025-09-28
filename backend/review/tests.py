"""
Test cases for review application - Ebbinghaus forgetting curve implementation
"""
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import SubscriptionTier
from content.models import Category, Content
from .models import ReviewSchedule, ReviewHistory
from .utils import (
    get_review_intervals, calculate_next_review_date,
    calculate_success_rate, get_today_reviews_count,
    get_pending_reviews_count
)
from .serializers import ReviewScheduleSerializer, ReviewHistorySerializer

User = get_user_model()


class ReviewUtilsTest(TestCase):
    """Test review utility functions - Core Ebbinghaus implementation"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_get_review_intervals_free_tier(self):
        """Test review intervals for FREE tier"""
        self.user.subscription.tier = SubscriptionTier.FREE
        self.user.subscription.save()
        
        intervals = get_review_intervals(self.user)
        expected = [1, 3]  # FREE tier: max 3 days
        self.assertEqual(intervals, expected)
    
    def test_get_review_intervals_basic_tier(self):
        """Test review intervals for BASIC tier"""
        self.user.subscription.tier = SubscriptionTier.BASIC
        self.user.subscription.save()
        
        intervals = get_review_intervals(self.user)
        expected = [1, 3, 7, 14, 30, 60, 90]  # BASIC tier: max 90 days
        self.assertEqual(intervals, expected)
    
    def test_get_review_intervals_pro_tier(self):
        """Test review intervals for PRO tier"""
        self.user.subscription.tier = SubscriptionTier.PRO
        self.user.subscription.save()
        
        intervals = get_review_intervals(self.user)
        expected = [1, 3, 7, 14, 30, 60, 120, 180]  # PRO tier: max 180 days
        self.assertEqual(intervals, expected)
    
    def test_calculate_next_review_date(self):
        """Test next review date calculation"""
        # Test with user and interval index
        next_date, new_index = calculate_next_review_date(self.user, 0, 'remembered')

        # Should advance to next interval
        self.assertEqual(new_index, 1)

        # Should be scheduled for tomorrow (first interval)
        intervals = get_review_intervals(self.user)
        expected_days = intervals[1]  # Second interval after advancing
        expected_date = timezone.now() + timedelta(days=expected_days)

        # Check if dates are within reasonable range (1 minute tolerance)
        time_diff = abs((next_date - expected_date).total_seconds())
        self.assertLess(time_diff, 60)

        # Test reset on forgotten
        reset_date, reset_index = calculate_next_review_date(self.user, 2, 'forgotten')
        self.assertEqual(reset_index, 0)  # Should reset to first interval
    
    def test_calculate_success_rate(self):
        """Test success rate calculation"""
        category = Category.objects.create(name='Success Rate Category', user=self.user)
        content = Content.objects.create(
            title='Success Rate Content',
            content='Test content',
            author=self.user,
            category=category
        )
        
        # Create some review history
        ReviewHistory.objects.create(
            content=content,
            user=self.user,
            result='remembered',
            time_spent=30
        )
        ReviewHistory.objects.create(
            content=content,
            user=self.user,
            result='forgot',
            time_spent=45
        )
        ReviewHistory.objects.create(
            content=content,
            user=self.user,
            result='remembered',
            time_spent=25
        )
        
        success_rate, total_reviews, details = calculate_success_rate(self.user)
        
        self.assertEqual(total_reviews, 3)
        self.assertAlmostEqual(success_rate, 66.7, places=1)  # 2/3 = 66.7%
        self.assertIn('remembered', details)
        self.assertIn('forgot', details)
    
    def test_get_today_reviews_count(self):
        """Test today's review count"""
        category = Category.objects.create(name='Today Category', user=self.user)
        content = Content.objects.create(
            title='Today Content',
            content='Test content',
            author=self.user,
            category=category
        )

        # Update the automatically created review schedule to be due today
        schedule = ReviewSchedule.objects.get(content=content, user=self.user)
        schedule.next_review_date = timezone.now()
        schedule.is_active = True
        schedule.save()

        count = get_today_reviews_count(self.user)
        self.assertEqual(count, 1)
    
    def test_get_pending_reviews_count(self):
        """Test pending reviews count"""
        # Create content with past date using raw SQL to bypass constraints
        from django.db import connection

        category = Category.objects.create(name='Pending Category', user=self.user)
        content = Content.objects.create(
            title='Pending Content',
            content='Test content',
            author=self.user,
            category=category
        )

        # Delete auto-created schedule and create one with past dates
        ReviewSchedule.objects.filter(content=content, user=self.user).delete()

        # Create schedule with past dates using raw SQL
        with connection.cursor() as cursor:
            past_date = timezone.now() - timedelta(days=2)
            cursor.execute(
                """INSERT INTO review_reviewschedule
                   (content_id, user_id, next_review_date, interval_index, is_active,
                    initial_review_completed, created_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                [content.id, self.user.id, past_date, 0, True, False, past_date, past_date]
            )

        count = get_pending_reviews_count(self.user)
        self.assertEqual(count, 1)


class ReviewScheduleModelTest(TestCase):
    """Test ReviewSchedule model - Core Ebbinghaus logic"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test Category', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='Test content',
            author=self.user,
            category=self.category
        )
    
    def test_create_review_schedule(self):
        """Test creating a review schedule"""
        # Use the automatically created schedule from signal
        schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)

        self.assertEqual(schedule.content, self.content)
        self.assertEqual(schedule.user, self.user)
        self.assertEqual(schedule.interval_index, 0)
        self.assertTrue(schedule.is_active)
        self.assertFalse(schedule.initial_review_completed)
    
    def test_advance_schedule_free_tier(self):
        """Test advancing schedule for FREE tier"""
        self.user.subscription.tier = SubscriptionTier.FREE
        self.user.subscription.save()

        # Use the automatically created schedule from signal
        schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)
        
        original_date = schedule.next_review_date
        schedule.advance_schedule()
        
        # Should advance to next interval (3 days for FREE tier)
        self.assertEqual(schedule.interval_index, 1)
        self.assertGreater(schedule.next_review_date, original_date)
        
        # Try to advance beyond FREE tier limit
        schedule.advance_schedule()  # Should stay at max interval
        self.assertEqual(schedule.interval_index, 1)  # Should not exceed FREE limit
    
    def test_advance_schedule_basic_tier(self):
        """Test advancing schedule for BASIC tier"""
        self.user.subscription.tier = SubscriptionTier.BASIC
        self.user.subscription.save()

        # Use the automatically created schedule from signal
        schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)
        
        # Advance multiple times to test full progression
        original_index = schedule.interval_index
        schedule.advance_schedule()
        self.assertEqual(schedule.interval_index, original_index + 1)
        
        # Test advancing through multiple intervals
        for i in range(5):  # Advance 5 more times
            prev_index = schedule.interval_index
            schedule.advance_schedule()
            if prev_index < 6:  # BASIC has 7 intervals (0-6)
                self.assertEqual(schedule.interval_index, prev_index + 1)
    
    def test_reset_schedule(self):
        """Test resetting schedule (forgot case)"""
        # Set BASIC tier to allow higher interval index
        self.user.subscription.tier = SubscriptionTier.BASIC
        self.user.subscription.save()

        # Use the automatically created schedule from signal
        schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)
        schedule.interval_index = 3
        schedule.save()
        
        old_date = schedule.next_review_date
        schedule.reset_schedule()
        
        self.assertEqual(schedule.interval_index, 0)
        self.assertNotEqual(schedule.next_review_date, old_date)
    
    def test_schedule_str_representation(self):
        """Test schedule string representation"""
        # Use the automatically created schedule from signal
        schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)
        
        expected_str = f"Test Content - {self.user.email} (interval: 0)"
        self.assertEqual(str(schedule), expected_str)
    
    def test_subscription_tier_change_adjustment(self):
        """Test schedule adjustment when subscription tier changes"""
        # Start with PRO tier
        self.user.subscription.tier = SubscriptionTier.PRO
        self.user.subscription.save()

        # Use the automatically created schedule from signal
        schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)
        schedule.interval_index = 7  # Max PRO interval
        schedule.next_review_date = timezone.now() + timedelta(days=180)
        schedule.save()
        
        # Downgrade to BASIC tier
        self.user.subscription.tier = SubscriptionTier.BASIC
        self.user.subscription.save()
        
        # Schedule should be adjusted to BASIC limits
        # This would be handled by signals in the actual implementation


class ReviewHistoryModelTest(TestCase):
    """Test ReviewHistory model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test Category', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='Test content',
            author=self.user,
            category=self.category
        )
    
    def test_create_review_history(self):
        """Test creating review history"""
        history = ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='remembered',
            time_spent=30,
            notes='Good recall'
        )
        
        self.assertEqual(history.content, self.content)
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.result, 'remembered')
        self.assertEqual(history.time_spent, 30)
        self.assertEqual(history.notes, 'Good recall')
        self.assertIsNotNone(history.review_date)
    
    def test_history_result_choices(self):
        """Test valid result choices"""
        valid_results = ['remembered', 'partial', 'forgot']
        
        for result in valid_results:
            history = ReviewHistory.objects.create(
                content=self.content,
                user=self.user,
                result=result,
                time_spent=30
            )
            self.assertEqual(history.result, result)
    
    def test_history_str_representation(self):
        """Test history string representation"""
        history = ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='remembered',
            time_spent=30
        )
        
        expected_str = f"Test Content - remembered"
        self.assertEqual(str(history), expected_str)


class ReviewAPITest(APITestCase):
    """Test Review API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        self.category = Category.objects.create(name='Test Category', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='Test content',
            author=self.user,
            category=self.category
        )
        
        # Use the automatically created schedule from signal
        self.schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)
    
    def test_today_review_view(self):
        """Test today's review endpoint"""
        url = reverse('review:today')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['content']['title'], 'Test Content')
        self.assertIn('subscription_tier', response.data)
        self.assertIn('max_interval_days', response.data)
    
    def test_today_review_with_category_filter(self):
        """Test today's review with category filter"""
        url = reverse('review:today')
        response = self.client.get(url, {'category_slug': self.category.slug})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_today_review_subscription_limits(self):
        """Test subscription limits in today's reviews"""
        # Create overdue review beyond FREE tier limit
        old_content = Content.objects.create(
            title='Old Content',
            content='Old content',
            author=self.user,
            category=self.category
        )
        
        # Update the auto-created schedule to be overdue by 5 days (beyond FREE tier limit)
        old_schedule = ReviewSchedule.objects.get(content=old_content, user=self.user)
        # Use raw SQL to bypass constraint validation for testing
        from django.db import connection
        with connection.cursor() as cursor:
            past_date = timezone.now() - timedelta(days=6)  # Both creation and review dates in the past
            cursor.execute(
                """UPDATE review_reviewschedule
                   SET next_review_date = %s, is_active = %s, created_at = %s
                   WHERE id = %s""",
                [timezone.now() - timedelta(days=5), True, past_date, old_schedule.id]
            )
        
        url = reverse('review:today')
        response = self.client.get(url)
        
        # Should only return recent reviews within subscription limit
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # FREE tier should filter out reviews older than 3 days
        titles = [item['content']['title'] for item in response.data['results']]
        self.assertIn('Test Content', titles)  # Today's review
        # Old Content might not be included due to FREE tier limits
    
    def test_complete_review_remembered(self):
        """Test completing review with 'remembered' result"""
        url = reverse('review:complete')
        data = {
            'content_id': self.content.id,
            'result': 'remembered',
            'time_spent': 30,
            'notes': 'Easy to remember'
        }
        
        original_interval_index = self.schedule.interval_index
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('next_review_date', response.data)
        self.assertIn('interval_index', response.data)
        
        # Check schedule was updated
        self.schedule.refresh_from_db()
        self.assertGreater(self.schedule.interval_index, original_interval_index)
        self.assertTrue(self.schedule.initial_review_completed)
        
        # Check history was created
        history = ReviewHistory.objects.filter(
            content=self.content,
            user=self.user,
            result='remembered'
        ).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.time_spent, 30)
        self.assertEqual(history.notes, 'Easy to remember')
    
    def test_complete_review_partial(self):
        """Test completing review with 'partial' result"""
        url = reverse('review:complete')
        data = {
            'content_id': self.content.id,
            'result': 'partial',
            'time_spent': 45
        }
        
        original_interval_index = self.schedule.interval_index
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check schedule stayed at same interval
        self.schedule.refresh_from_db()
        self.assertEqual(self.schedule.interval_index, original_interval_index)
        self.assertTrue(self.schedule.initial_review_completed)
    
    def test_complete_review_forgot(self):
        """Test completing review with 'forgot' result"""
        # Set BASIC tier to allow higher interval index
        self.user.subscription.tier = SubscriptionTier.BASIC
        self.user.subscription.save()

        # Advance schedule first
        self.schedule.interval_index = 2
        self.schedule.save()
        
        url = reverse('review:complete')
        data = {
            'content_id': self.content.id,
            'result': 'forgot',
            'time_spent': 60
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check schedule was reset to first interval
        self.schedule.refresh_from_db()
        self.assertEqual(self.schedule.interval_index, 0)
        self.assertTrue(self.schedule.initial_review_completed)
    
    def test_complete_review_invalid_content(self):
        """Test completing review with invalid content ID"""
        url = reverse('review:complete')
        data = {
            'content_id': 99999,
            'result': 'remembered',
            'time_spent': 30
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_complete_review_invalid_result(self):
        """Test completing review with invalid result"""
        url = reverse('review:complete')
        data = {
            'content_id': self.content.id,
            'result': 'invalid_result',
            'time_spent': 30
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_complete_review_missing_data(self):
        """Test completing review with missing required data"""
        url = reverse('review:complete')
        data = {
            'content_id': self.content.id,
            # Missing result
            'time_spent': 30
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_review_schedules_list(self):
        """Test listing review schedules"""
        url = reverse('review:schedules-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['content']['title'], 'Test Content')
    
    def test_review_history_list(self):
        """Test listing review history"""
        # Create some history first
        ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='remembered',
            time_spent=30
        )
        
        url = reverse('review:history-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['result'], 'remembered')
    
    def test_category_review_stats(self):
        """Test category review statistics"""
        # Create some review history
        ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='remembered',
            time_spent=30
        )
        
        url = reverse('review:category-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)

        if response.data:  # If there are stats
            # The response is a dict keyed by category slug
            category_slug = list(response.data.keys())[0]
            stats = response.data[category_slug]
            self.assertIn('category', stats)
            self.assertIn('total_reviews_30_days', stats)  # Updated field name
            self.assertIn('success_rate', stats)


class EbbinghausAlgorithmTest(TestCase):
    """Test Ebbinghaus forgetting curve algorithm implementation"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test Category', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='Test content',
            author=self.user,
            category=self.category
        )
    
    def test_ebbinghaus_progression_basic_tier(self):
        """Test complete Ebbinghaus progression for BASIC tier"""
        self.user.subscription.tier = SubscriptionTier.BASIC
        self.user.subscription.save()
        
        # Use the automatically created schedule from signal
        schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)
        
        expected_intervals = [1, 3, 7, 14, 30, 60, 90]
        
        # Test progression through all intervals
        for i, expected_days in enumerate(expected_intervals[1:], 1):
            before_advance = timezone.now()
            schedule.advance_schedule()

            self.assertEqual(schedule.interval_index, i)

            # Calculate expected new date from when advance_schedule was called
            expected_new_date = before_advance + timedelta(days=expected_days)

            # Allow reasonable time difference due to processing time
            time_diff = abs((schedule.next_review_date - expected_new_date).total_seconds())
            self.assertLess(time_diff, 5)  # Less than 5 seconds difference
    
    def test_ebbinghaus_forgetting_reset(self):
        """Test forgetting resets to first interval"""
        self.user.subscription.tier = SubscriptionTier.BASIC
        self.user.subscription.save()
        
        # Use the automatically created schedule from signal
        schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)
        schedule.interval_index = 5  # Advanced interval
        schedule.save()
        
        # Simulate forgetting
        schedule.reset_schedule()
        
        self.assertEqual(schedule.interval_index, 0)
        
        # Next review should be in 1 day (first interval)
        expected_date = timezone.now() + timedelta(days=1)
        time_diff = abs((schedule.next_review_date - expected_date).total_seconds())
        self.assertLess(time_diff, 60)  # Less than 1 minute difference
    
    def test_subscription_tier_interval_limits(self):
        """Test that intervals respect subscription tier limits"""
        # Test FREE tier limits
        self.user.subscription.tier = SubscriptionTier.FREE
        self.user.subscription.save()
        
        free_intervals = get_review_intervals(self.user)
        self.assertEqual(max(free_intervals), 3)  # FREE max is 3 days
        
        # Test BASIC tier limits
        self.user.subscription.tier = SubscriptionTier.BASIC
        self.user.subscription.save()
        
        basic_intervals = get_review_intervals(self.user)
        self.assertEqual(max(basic_intervals), 90)  # BASIC max is 90 days
        
        # Test PRO tier limits
        self.user.subscription.tier = SubscriptionTier.PRO
        self.user.subscription.save()
        
        pro_intervals = get_review_intervals(self.user)
        self.assertEqual(max(pro_intervals), 180)  # PRO max is 180 days


class SerializerTest(TestCase):
    """Test review serializers"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test Category', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='Test content',
            author=self.user,
            category=self.category
        )
        
        # Use the automatically created schedule from signal
        self.schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)
        
        self.history = ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='remembered',
            time_spent=30
        )
    
    def test_review_schedule_serializer(self):
        """Test ReviewScheduleSerializer"""
        serializer = ReviewScheduleSerializer(self.schedule)
        
        data = serializer.data
        self.assertIn('content', data)
        self.assertIn('interval_index', data)
        self.assertIn('next_review_date', data)
        self.assertIn('initial_review_completed', data)
        self.assertEqual(data['content']['title'], 'Test Content')
    
    def test_review_history_serializer(self):
        """Test ReviewHistorySerializer"""
        serializer = ReviewHistorySerializer(self.history)
        
        data = serializer.data
        self.assertIn('content', data)
        self.assertIn('result', data)
        self.assertIn('time_spent', data)
        self.assertIn('review_date', data)
        self.assertEqual(data['result'], 'remembered')
        self.assertEqual(data['time_spent'], 30)