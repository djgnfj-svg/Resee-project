"""
Tests for enhanced analytics functionality
"""

from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .base import BaseTestCase, BaseAPITestCase, TestDataMixin

User = get_user_model()


class EnhancedAnalyticsAPITestCase(BaseAPITestCase, TestDataMixin):
    """Test cases for Enhanced Analytics API endpoints"""
    
    def setUp(self):
        """Set up test data for enhanced analytics"""
        super().setUp()
        
        # Create test content
        self.content1 = self.create_content(title='Python Basics')
        self.content2 = self.create_content(title='Django Models')
        
        # Create review history for testing
        today = timezone.now()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        
        # Recent reviews (last 30 days)
        self.create_review_history(
            content=self.content1,
            result='remembered',
            time_spent=120,
            review_date=today
        )
        self.create_review_history(
            content=self.content2,
            result='partial',
            time_spent=180,
            review_date=yesterday
        )
        self.create_review_history(
            content=self.content1,
            result='forgot',
            time_spent=150,
            review_date=week_ago
        )
    
    def test_enhanced_dashboard_endpoint(self):
        """Test enhanced dashboard endpoint structure"""
        url = reverse('analytics:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check required fields
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
        
        # Check data types
        self.assertIsInstance(response.data['streak_days'], int)
        self.assertGreaterEqual(response.data['streak_days'], 0)
    
    def test_enhanced_review_stats_endpoint(self):
        """Test enhanced review stats endpoint structure"""
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check main structure
        required_fields = [
            'result_distribution',
            'daily_reviews',
            'weekly_performance',
            'trends'
        ]
        
        for field in required_fields:
            self.assertIn(field, response.data)
    
    def test_result_distribution_structure(self):
        """Test result distribution data structure"""
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        result_dist = response.data['result_distribution']
        
        # Check structure
        self.assertIn('all_time', result_dist)
        self.assertIn('recent_30_days', result_dist)
        self.assertIn('all_time_total', result_dist)
        self.assertIn('recent_total', result_dist)
        
        # Check recent 30 days data
        recent_data = result_dist['recent_30_days']
        self.assertIsInstance(recent_data, list)
        
        # Check each result type has required fields
        for item in recent_data:
            self.assertIn('result', item)
            self.assertIn('name', item)
            self.assertIn('count', item)
            self.assertIn('percentage', item)
    
    def test_daily_reviews_structure(self):
        """Test daily reviews data structure"""
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        daily_reviews = response.data['daily_reviews']
        self.assertIsInstance(daily_reviews, list)
        self.assertEqual(len(daily_reviews), 30)  # 30 days
        
        # Check structure of each day
        for day in daily_reviews:
            self.assertIn('date', day)
            self.assertIn('count', day)
            self.assertIn('success_rate', day)
            self.assertIn('remembered', day)
            self.assertIn('partial', day)
            self.assertIn('forgot', day)
    
    def test_weekly_performance_structure(self):
        """Test weekly performance data structure"""
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        weekly_performance = response.data['weekly_performance']
        self.assertIsInstance(weekly_performance, list)
        self.assertEqual(len(weekly_performance), 4)  # 4 weeks
        
        # Check structure of each week
        for week in weekly_performance:
            required_fields = [
                'week_start', 'week_end', 'week_label',
                'total_reviews', 'success_rate', 'consistency',
                'days_active', 'remembered', 'partial', 'forgot'
            ]
            for field in required_fields:
                self.assertIn(field, week)
            
            # Check data types
            self.assertIsInstance(week['success_rate'], (int, float))
            self.assertIsInstance(week['consistency'], (int, float))
            self.assertIsInstance(week['days_active'], int)
            self.assertGreaterEqual(week['days_active'], 0)
            self.assertLessEqual(week['days_active'], 7)
    
    def test_trends_structure(self):
        """Test trends data structure"""
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        trends = response.data['trends']
        
        required_fields = [
            'review_count_change',
            'success_rate_change',
            'current_period_total',
            'previous_period_total',
            'current_success_rate',
            'previous_success_rate'
        ]
        
        for field in required_fields:
            self.assertIn(field, trends)
            self.assertIsInstance(trends[field], (int, float))
    
    def test_streak_calculation(self):
        """Test streak calculation logic"""
        # Create consecutive daily reviews
        today = timezone.now().date()
        
        for i in range(3):
            review_date = today - timedelta(days=i)
            content = self.create_content(title=f'Streak Content {i}')
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
        streak_days = response.data['streak_days']
        
        # Should have at least 3 day streak
        self.assertGreaterEqual(streak_days, 3)
    
    def test_percentage_calculations(self):
        """Test percentage calculations in result distribution"""
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        result_dist = response.data['result_distribution']
        recent_data = result_dist['recent_30_days']
        
        # Check that percentages add up to 100 (or close to it due to rounding)
        total_percentage = sum(item['percentage'] for item in recent_data)
        
        if result_dist['recent_total'] > 0:
            self.assertAlmostEqual(total_percentage, 100.0, delta=0.1)
        else:
            self.assertEqual(total_percentage, 0.0)
    
    def test_empty_data_handling(self):
        """Test handling of empty data sets"""
        # Create user with no review history
        empty_user = self.create_user(username='empty', email='empty@example.com')
        self.authenticate_user(empty_user)
        
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that empty data is handled gracefully
        result_dist = response.data['result_distribution']
        self.assertEqual(result_dist['recent_total'], 0)
        self.assertEqual(result_dist['all_time_total'], 0)
        
        daily_reviews = response.data['daily_reviews']
        self.assertEqual(len(daily_reviews), 30)
        
        # All days should have 0 counts
        for day in daily_reviews:
            self.assertEqual(day['count'], 0)
            self.assertEqual(day['success_rate'], 0)
    
    def test_user_data_isolation(self):
        """Test that analytics data is properly isolated by user"""
        # Create another user with different data
        other_user = self.create_user(username='other', email='other@example.com')
        other_content = self.create_content(
            title='Other User Content',
            author=other_user
        )
        self.create_review_history(
            user=other_user,
            content=other_content,
            result='remembered'
        )
        
        # Check current user's data
        url = reverse('analytics:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should not include other user's data
        total_content = response.data['total_content']
        self.assertGreater(total_content, 0)  # Should have some content
        
        # Verify isolation by checking totals don't include other user
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        result_dist = response.data['result_distribution']
        recent_total = result_dist['recent_total']
        
        # Should only count current user's reviews
        self.assertEqual(recent_total, 3)  # Our test reviews, not other user's
    
    def test_api_response_performance(self):
        """Test API response performance with reasonable dataset"""
        # Create moderate dataset
        for i in range(10):
            content = self.create_content(title=f'Performance Test {i}')
            for j in range(3):
                result = ['remembered', 'partial', 'forgot'][j]
                self.create_review_history(
                    content=content,
                    result=result,
                    review_date=timezone.now() - timedelta(days=j)
                )
        
        # Test both endpoints
        endpoints = [
            reverse('analytics:dashboard'),
            reverse('analytics:review-stats')
        ]
        
        for url in endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Response should be reasonably structured
            self.assertIsInstance(response.data, dict)
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access analytics"""
        self.client.credentials()
        
        endpoints = [
            reverse('analytics:dashboard'),
            reverse('analytics:review-stats')
        ]
        
        for url in endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)