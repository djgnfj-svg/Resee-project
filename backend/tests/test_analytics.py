"""
Tests for analytics app
"""

from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .base import BaseTestCase, BaseAPITestCase, TestDataMixin
from analytics.views import DashboardView, ReviewStatsView

User = get_user_model()


class AnalyticsAPITestCase(BaseAPITestCase, TestDataMixin):
    """Test cases for Analytics API endpoints"""
    
    def setUp(self):
        """Set up test data for analytics"""
        super().setUp()
        
        # Create additional test data for analytics
        self.category1 = self.create_category(name='Python')
        self.category2 = self.create_category(name='Django')
        
        self.content1 = self.create_content(title='Python Basics', category=self.category1)
        self.content2 = self.create_content(title='Django Models', category=self.category2)
        self.content3 = self.create_content(title='Python Advanced', category=self.category1)
        
        # Create review schedules
        self.schedule1 = self.create_review_schedule(content=self.content1, interval_index=1)
        self.schedule2 = self.create_review_schedule(content=self.content2, interval_index=2)
        self.schedule3 = self.create_review_schedule(content=self.content3, interval_index=0)
        
        # Create review history
        self.history1 = self.create_review_history(
            content=self.content1,
            result='remembered',
            time_spent=120,
            review_date=timezone.now() - timedelta(days=1)
        )
        self.history2 = self.create_review_history(
            content=self.content2,
            result='forgot',
            time_spent=180,
            review_date=timezone.now() - timedelta(days=2)
        )
        self.history3 = self.create_review_history(
            content=self.content3,
            result='partial',
            time_spent=150,
            review_date=timezone.now() - timedelta(days=3)
        )
        self.history4 = self.create_review_history(
            content=self.content1,
            result='remembered',
            time_spent=90,
            review_date=timezone.now() - timedelta(days=4)
        )
    
    def test_dashboard_overview(self):
        """Test dashboard overview endpoint"""
        url = reverse('analytics:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check required fields in response
        required_fields = [
            'today_reviews',
            'pending_reviews',
            'total_content',
            'success_rate',
            'total_reviews_30_days',
            'streak_days'
        ]
        
        for field in required_fields:
            self.assertIn(field, response.data)
        
        # Check types
        self.assertIsInstance(response.data['today_reviews'], int)
        self.assertIsInstance(response.data['pending_reviews'], int)
        self.assertIsInstance(response.data['total_content'], int)
        self.assertIsInstance(response.data['success_rate'], (int, float))
        self.assertIsInstance(response.data['total_reviews_30_days'], int)
        self.assertIsInstance(response.data['streak_days'], int)
    
    def test_dashboard_recent_activity(self):
        """Test recent activity in dashboard"""
        url = reverse('analytics:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        recent_activity = response.data['recent_activity']
        self.assertTrue(len(recent_activity) >= 4)
        
        # Check activity structure
        for activity in recent_activity:
            self.assertIn('content_title', activity)
            self.assertIn('result', activity)
            self.assertIn('review_date', activity)
            self.assertIn('time_spent', activity)
        
        # Check ordering (newest first)
        dates = [activity['review_date'] for activity in recent_activity]
        self.assertEqual(dates, sorted(dates, reverse=True))
    
    def test_dashboard_streak_calculation(self):
        """Test streak calculation in dashboard"""
        # Create review history for consecutive days
        today = timezone.now().date()
        
        for i in range(5):
            review_date = today - timedelta(days=i)
            content = self.create_content(title=f'Content {i}')
            self.create_review_history(
                content=content,
                result='remembered',
                review_date=timezone.make_aware(
                    timezone.datetime.combine(review_date, timezone.datetime.min.time())
                )
            )
        
        url = reverse('analytics:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have a streak of at least 5 days
        self.assertGreaterEqual(response.data['streak_days'], 5)
    
    def test_dashboard_reviews_today(self):
        """Test reviews today count in dashboard"""
        # Create review history for today
        today_history = self.create_review_history(
            content=self.create_content(title='Today Content'),
            result='remembered',
            review_date=timezone.now()
        )
        
        url = reverse('analytics:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['reviews_today'], 1)
    
    def test_review_stats_overall(self):
        """Test review statistics endpoint overall stats"""
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check required fields
        required_fields = [
            'result_distribution',
            'daily_reviews',
            'weekly_performance',
            'trends'
        ]
        
        for field in required_fields:
            self.assertIn(field, response.data)
        
        # Check structure
        self.assertIsInstance(response.data['result_distribution'], dict)
        self.assertIsInstance(response.data['daily_reviews'], list)
        self.assertIsInstance(response.data['weekly_performance'], list)
        self.assertIsInstance(response.data['trends'], dict)
        
        # Check result distribution structure
        result_dist = response.data['result_distribution']
        self.assertIn('all_time', result_dist)
        self.assertIn('recent_30_days', result_dist)
        self.assertIn('all_time_total', result_dist)
        self.assertIn('recent_total', result_dist)
    
    def test_review_stats_success_rate(self):
        """Test success rate calculation in trends"""
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check trends include success rate
        trends = response.data['trends']
        self.assertIn('current_success_rate', trends)
        self.assertIn('previous_success_rate', trends)
        self.assertIn('success_rate_change', trends)
        
        self.assertIsInstance(trends['current_success_rate'], (int, float))
        self.assertIsInstance(trends['previous_success_rate'], (int, float))
        self.assertIsInstance(trends['success_rate_change'], (int, float))
    
    def test_review_stats_average_time(self):
        """Test average time spent calculation"""
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # With current test data: 120 + 180 + 150 + 90 = 540, average = 135
        expected_average = 135.0
        self.assertEqual(response.data['average_time_spent'], expected_average)
    
    def test_review_stats_distribution(self):
        """Test review result distribution"""
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        distribution = response.data['review_distribution']
        self.assertIn('remembered', distribution)
        self.assertIn('forgot', distribution)
        self.assertIn('partial', distribution)
        
        # Check counts
        self.assertEqual(distribution['remembered'], 2)
        self.assertEqual(distribution['forgot'], 1)
        self.assertEqual(distribution['partial'], 1)
    
    def test_review_stats_daily_stats(self):
        """Test daily statistics"""
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        daily_stats = response.data['daily_stats']
        self.assertIsInstance(daily_stats, list)
        
        # Check structure of daily stats
        for day_stat in daily_stats:
            self.assertIn('date', day_stat)
            self.assertIn('reviews_count', day_stat)
            self.assertIn('success_rate', day_stat)
            self.assertIn('average_time', day_stat)
    
    def test_review_stats_category_performance(self):
        """Test category performance statistics"""
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        category_performance = response.data['category_performance']
        self.assertIsInstance(category_performance, list)
        
        # Check structure of category performance
        for category_stat in category_performance:
            self.assertIn('category_name', category_stat)
            self.assertIn('total_reviews', category_stat)
            self.assertIn('success_rate', category_stat)
            self.assertIn('average_time', category_stat)
        
        # Should have at least 2 categories
        self.assertGreaterEqual(len(category_performance), 2)
    
    def test_review_stats_date_filtering(self):
        """Test review statistics with date filtering"""
        # Create review history for specific dates
        specific_date = timezone.now() - timedelta(days=10)
        old_content = self.create_content(title='Old Content')
        old_history = self.create_review_history(
            content=old_content,
            result='remembered',
            review_date=specific_date
        )
        
        url = reverse('analytics:review-stats')
        
        # Filter by date range
        from_date = (timezone.now() - timedelta(days=5)).date()
        to_date = timezone.now().date()
        
        response = self.client.get(url, {
            'from_date': from_date.isoformat(),
            'to_date': to_date.isoformat()
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only include reviews from the last 5 days
        self.assertEqual(response.data['total_reviews'], 4)  # Excludes old_history
    
    def test_review_stats_category_filtering(self):
        """Test review statistics with category filtering"""
        url = reverse('analytics:review-stats')
        
        # Filter by specific category
        response = self.client.get(url, {'category': self.category1.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only include reviews from Python category
        self.assertEqual(response.data['total_reviews'], 2)  # content1 has 2 reviews
        
        # Check category performance only shows filtered category
        category_performance = response.data['category_performance']
        self.assertEqual(len(category_performance), 1)
        self.assertEqual(category_performance[0]['category_name'], 'Python')
    
    def test_review_stats_empty_data(self):
        """Test review statistics with no data"""
        # Create user with no review history
        empty_user = self.create_user(username='empty', email='empty@example.com')
        self.authenticate_user(empty_user)
        
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check zero values
        self.assertEqual(response.data['total_reviews'], 0)
        self.assertEqual(response.data['success_rate'], 0)
        self.assertEqual(response.data['average_time_spent'], 0)
        self.assertEqual(response.data['review_distribution'], {
            'remembered': 0,
            'forgot': 0,
            'partial': 0
        })
        self.assertEqual(response.data['daily_stats'], [])
        self.assertEqual(response.data['category_performance'], [])
    
    def test_analytics_user_isolation(self):
        """Test that analytics data is isolated per user"""
        # Create another user with review history
        other_user = self.create_user(username='other', email='other@example.com')
        other_category = self.create_category(name='Other Category', user=other_user)
        other_content = self.create_content(
            title='Other Content',
            author=other_user,
            category=other_category
        )
        self.create_review_history(
            user=other_user,
            content=other_content,
            result='remembered'
        )
        
        # Check current user's analytics
        url = reverse('analytics:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only see current user's data
        self.assertEqual(response.data['total_contents'], 4)  # Not including other_content
        self.assertEqual(response.data['total_reviews'], 4)   # Not including other_user's review
    
    def test_analytics_performance_with_large_dataset(self):
        """Test analytics performance with larger dataset"""
        # Create a larger dataset
        contents = []
        for i in range(20):
            content = self.create_content(title=f'Performance Content {i}')
            contents.append(content)
            
            # Create multiple review histories per content
            for j in range(5):
                result = ['remembered', 'forgot', 'partial'][j % 3]
                self.create_review_history(
                    content=content,
                    result=result,
                    time_spent=120 + j * 10,
                    review_date=timezone.now() - timedelta(days=j)
                )
        
        # Test dashboard performance
        url = reverse('analytics:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['total_contents'], 20)
        self.assertGreaterEqual(response.data['total_reviews'], 100)
        
        # Test review stats performance
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['total_reviews'], 100)
    
    def test_unauthenticated_access(self):
        """Test unauthenticated access to analytics endpoints"""
        self.client.credentials()
        
        endpoints = [
            'analytics:dashboard',
            'analytics:review-stats',
        ]
        
        for endpoint_name in endpoints:
            url = reverse(endpoint_name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AnalyticsViewTestCase(BaseTestCase):
    """Test cases for Analytics view classes"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        # Create additional test data
        self.content2 = self.create_content(title='Content 2')
        self.content3 = self.create_content(title='Content 3')
        
        # Create review histories
        self.history1 = self.create_review_history(
            content=self.content,
            result='remembered',
            time_spent=120
        )
        self.history2 = self.create_review_history(
            content=self.content2,
            result='forgot',
            time_spent=180
        )
        self.history3 = self.create_review_history(
            content=self.content3,
            result='partial',
            time_spent=150
        )
    
    def test_dashboard_view_data_aggregation(self):
        """Test dashboard view data aggregation logic"""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/analytics/dashboard/')
        request.user = self.user
        
        view = DashboardView()
        view.request = request
        
        # Test individual methods
        total_contents = view.get_total_contents()
        total_reviews = view.get_total_reviews()
        reviews_today = view.get_reviews_today()
        
        self.assertEqual(total_contents, 4)  # 3 + 1 from base setup
        self.assertEqual(total_reviews, 3)
        self.assertIsInstance(reviews_today, int)
    
    def test_review_stats_view_calculations(self):
        """Test review stats view calculation logic"""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/analytics/review-stats/')
        request.user = self.user
        
        view = ReviewStatsView()
        view.request = request
        
        # Test individual methods
        success_rate = view.calculate_success_rate()
        avg_time = view.calculate_average_time()
        distribution = view.get_review_distribution()
        
        # With 1 remembered, 1 forgot, 1 partial: success rate = 33.33%
        self.assertAlmostEqual(success_rate, 33.33, places=2)
        
        # Average time: (120 + 180 + 150) / 3 = 150
        self.assertEqual(avg_time, 150.0)
        
        # Distribution
        self.assertEqual(distribution['remembered'], 1)
        self.assertEqual(distribution['forgot'], 1)
        self.assertEqual(distribution['partial'], 1)
    
    def test_analytics_edge_cases(self):
        """Test analytics edge cases"""
        from django.test import RequestFactory
        
        # Test with user who has no review history
        empty_user = self.create_user(username='empty', email='empty@example.com')
        
        factory = RequestFactory()
        request = factory.get('/analytics/dashboard/')
        request.user = empty_user
        
        view = DashboardView()
        view.request = request
        
        # Should handle zero data gracefully
        total_reviews = view.get_total_reviews()
        reviews_today = view.get_reviews_today()
        streak_days = view.get_streak_days()
        
        self.assertEqual(total_reviews, 0)
        self.assertEqual(reviews_today, 0)
        self.assertEqual(streak_days, 0)
    
    def test_analytics_date_boundaries(self):
        """Test analytics with date boundary conditions"""
        # Create review at exact midnight
        midnight = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        midnight_content = self.create_content(title='Midnight Content')
        midnight_history = self.create_review_history(
            content=midnight_content,
            result='remembered',
            review_date=midnight
        )
        
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/analytics/review-stats/')
        request.user = self.user
        
        view = ReviewStatsView()
        view.request = request
        
        # Should properly handle date boundaries
        daily_stats = view.get_daily_stats()
        self.assertIsInstance(daily_stats, list)
        
        # Check that midnight review is included
        today_stats = [stat for stat in daily_stats if stat['date'] == midnight.date()]
        self.assertTrue(len(today_stats) > 0)