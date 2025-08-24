"""
Test cases for analytics application
"""
from datetime import datetime, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import SubscriptionTier
from content.models import Category, Content
from review.models import ReviewHistory, ReviewSchedule

User = get_user_model()


class AnalyticsUtilityTest(TestCase):
    """Test analytics utility functions and calculations"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        # Create test content and category
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
        
        self.schedule = ReviewSchedule.objects.create(
            user=self.user,
            content=self.content,
            interval_index=1,
            next_review_date=timezone.now().date()
        )
    
    def test_streak_calculation_empty(self):
        """Test streak calculation with no review history"""
        from analytics.views import DashboardView
        
        view = DashboardView()
        streak = view._calculate_review_streak(self.user)
        
        self.assertEqual(streak, 0)
    
    def test_streak_calculation_single_day(self):
        """Test streak calculation with single day review"""
        from analytics.views import DashboardView
        
        # Create review for today
        ReviewHistory.objects.create(
            user=self.user,
            content=self.content,
            result='remembered',
            review_date=timezone.now()
        )
        
        view = DashboardView()
        streak = view._calculate_review_streak(self.user)
        
        self.assertEqual(streak, 1)
    
    def test_streak_calculation_multiple_consecutive_days(self):
        """Test streak calculation with multiple consecutive days"""
        from analytics.views import DashboardView
        
        # Create reviews for 3 consecutive days
        for i in range(3):
            review_date = timezone.now() - timedelta(days=i)
            ReviewHistory.objects.create(
                user=self.user,
                content=self.content,
                result='remembered',
                review_date=review_date
            )
        
        view = DashboardView()
        streak = view._calculate_review_streak(self.user)
        
        self.assertEqual(streak, 3)
    
    def test_streak_calculation_with_gap(self):
        """Test streak calculation with gap in review history"""
        from analytics.views import DashboardView
        
        # Create reviews with a gap
        today = timezone.now()
        
        # Review today
        ReviewHistory.objects.create(
            user=self.user,
            content=self.content,
            result='remembered',
            review_date=today
        )
        
        # Skip yesterday, review day before yesterday
        review_date = today - timedelta(days=2)
        ReviewHistory.objects.create(
            user=self.user,
            content=self.content,
            result='remembered',
            review_date=review_date
        )
        
        view = DashboardView()
        streak = view._calculate_review_streak(self.user)
        
        # Should only count today due to gap
        self.assertEqual(streak, 1)


class DashboardViewTest(APITestCase):
    """Test DashboardView API endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create test data
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
        
        self.schedule = ReviewSchedule.objects.create(
            user=self.user,
            content=self.content,
            interval_index=1,
            next_review_date=timezone.now().date()
        )
    
    def test_dashboard_view_get_success(self):
        """Test successful dashboard data retrieval"""
        url = reverse('analytics:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        data = response.data
        required_fields = [
            'today_reviews', 'pending_reviews', 'total_content',
            'success_rate', 'total_reviews_30_days', 'streak_days'
        ]
        
        for field in required_fields:
            self.assertIn(field, data)
        
        # Check basic values
        self.assertEqual(data['total_content'], 1)
        self.assertIsInstance(data['today_reviews'], int)
        self.assertIsInstance(data['pending_reviews'], int)
        self.assertIsInstance(data['success_rate'], (int, float))
        self.assertIsInstance(data['total_reviews_30_days'], int)
        self.assertIsInstance(data['streak_days'], int)
    
    def test_dashboard_view_with_review_data(self):
        """Test dashboard view with actual review history"""
        # Create review history
        for i in range(5):
            ReviewHistory.objects.create(
                user=self.user,
                content=self.content,
                result='remembered' if i < 3 else 'forgot',
                review_date=timezone.now() - timedelta(days=i)
            )
        
        url = reverse('analytics:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        
        # Should have some review data now
        self.assertEqual(data['total_reviews_30_days'], 5)
        self.assertGreaterEqual(data['success_rate'], 0)
        self.assertLessEqual(data['success_rate'], 100)
    
    def test_dashboard_view_unauthenticated(self):
        """Test dashboard view without authentication"""
        self.client.credentials()  # Clear authentication
        
        url = reverse('analytics:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ReviewStatsViewTest(APITestCase):
    """Test ReviewStatsView API endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create test data
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
        
        # Create varied review history
        for i in range(10):
            result = ['remembered', 'partial', 'forgot'][i % 3]
            review_date = timezone.now() - timedelta(days=i)
            
            ReviewHistory.objects.create(
                user=self.user,
                content=self.content,
                result=result,
                review_date=review_date
            )
    
    def test_review_stats_view_success(self):
        """Test successful review statistics retrieval"""
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        data = response.data
        required_fields = [
            'result_distribution', 'daily_reviews', 'weekly_performance', 'trends'
        ]
        
        for field in required_fields:
            self.assertIn(field, data)
    
    def test_result_distribution_structure(self):
        """Test result distribution data structure"""
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        data = response.data
        result_distribution = data['result_distribution']
        
        # Check all_time and recent_30_days sections
        self.assertIn('all_time', result_distribution)
        self.assertIn('recent_30_days', result_distribution)
        self.assertIn('all_time_total', result_distribution)
        self.assertIn('recent_total', result_distribution)
        
        # Check result types
        result_types = ['remembered', 'partial', 'forgot']
        for result_data in result_distribution['all_time']:
            self.assertIn(result_data['result'], result_types)
            self.assertIn('count', result_data)
            self.assertIn('percentage', result_data)
            self.assertIn('name', result_data)
    
    def test_daily_reviews_structure(self):
        """Test daily reviews data structure"""
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        data = response.data
        daily_reviews = data['daily_reviews']
        
        # Should have 30 days of data
        self.assertEqual(len(daily_reviews), 30)
        
        # Check structure of first day data
        day_data = daily_reviews[0]
        required_fields = ['date', 'count', 'success_rate', 'remembered', 'partial', 'forgot']
        
        for field in required_fields:
            self.assertIn(field, day_data)
        
        # Check data types
        self.assertIsInstance(day_data['count'], int)
        self.assertIsInstance(day_data['success_rate'], (int, float))
    
    def test_weekly_performance_structure(self):
        """Test weekly performance data structure"""
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        data = response.data
        weekly_performance = data['weekly_performance']
        
        # Should have 4 weeks of data
        self.assertEqual(len(weekly_performance), 4)
        
        # Check structure of first week data
        week_data = weekly_performance[0]
        required_fields = [
            'week_start', 'week_end', 'week_label', 'total_reviews',
            'success_rate', 'consistency', 'days_active', 
            'remembered', 'partial', 'forgot'
        ]
        
        for field in required_fields:
            self.assertIn(field, week_data)
    
    def test_trends_structure(self):
        """Test trends data structure"""
        url = reverse('analytics:review-stats')
        response = self.client.get(url)
        
        data = response.data
        trends = data['trends']
        
        required_fields = [
            'review_count_change', 'success_rate_change',
            'current_period_total', 'previous_period_total',
            'current_success_rate', 'previous_success_rate'
        ]
        
        for field in required_fields:
            self.assertIn(field, trends)


class AdvancedAnalyticsViewTest(APITestCase):
    """Test AdvancedAnalyticsView API endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.weekly_goal = 50
        self.user.save()
        
        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create multiple categories and content
        for i in range(3):
            category = Category.objects.create(
                name=f'Category {i}',
                user=self.user
            )
            
            for j in range(2):
                content = Content.objects.create(
                    title=f'Content {i}-{j}',
                    content=f'Content body {i}-{j}',
                    author=self.user,
                    category=category
                )
                
                # Create review history with varied results and times
                for k in range(5):
                    result = ['remembered', 'partial', 'forgot'][k % 3]
                    hours_offset = k * 6  # Different hours of the day
                    review_date = timezone.now() - timedelta(days=k, hours=hours_offset % 24)
                    
                    ReviewHistory.objects.create(
                        user=self.user,
                        content=content,
                        result=result,
                        review_date=review_date
                    )
    
    def test_advanced_analytics_view_success(self):
        """Test successful advanced analytics retrieval"""
        url = reverse('analytics:advanced-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        data = response.data
        required_sections = [
            'learning_insights', 'category_performance', 'study_patterns',
            'achievement_stats', 'performance_metrics', 'recommendations'
        ]
        
        for section in required_sections:
            self.assertIn(section, data)
    
    def test_learning_insights_structure(self):
        """Test learning insights data structure"""
        url = reverse('analytics:advanced-analytics')
        response = self.client.get(url)
        
        insights = response.data['learning_insights']
        required_fields = [
            'total_content', 'total_reviews', 'recent_30d_reviews',
            'recent_7d_reviews', 'recent_success_rate', 'week_success_rate',
            'average_interval_days', 'streak_days'
        ]
        
        for field in required_fields:
            self.assertIn(field, insights)
        
        # Check basic values match expected data
        self.assertEqual(insights['total_content'], 6)  # 3 categories * 2 content each
        self.assertGreater(insights['total_reviews'], 0)
    
    def test_category_performance_structure(self):
        """Test category performance data structure"""
        url = reverse('analytics:advanced-analytics')
        response = self.client.get(url)
        
        category_performance = response.data['category_performance']
        
        # Should have 3 categories
        self.assertEqual(len(category_performance), 3)
        
        # Check structure of first category
        category_data = category_performance[0]
        required_fields = [
            'id', 'name', 'slug', 'content_count', 'total_reviews',
            'success_rate', 'recent_success_rate', 'difficulty_level', 'mastery_level'
        ]
        
        for field in required_fields:
            self.assertIn(field, category_data)
        
        # Check that categories are sorted by success rate
        if len(category_performance) > 1:
            for i in range(len(category_performance) - 1):
                self.assertGreaterEqual(
                    category_performance[i]['success_rate'],
                    category_performance[i + 1]['success_rate']
                )
    
    def test_study_patterns_structure(self):
        """Test study patterns data structure"""
        url = reverse('analytics:advanced-analytics')
        response = self.client.get(url)
        
        study_patterns = response.data['study_patterns']
        required_fields = [
            'hourly_pattern', 'daily_pattern', 'recommended_hour',
            'recommended_day', 'total_study_sessions'
        ]
        
        for field in required_fields:
            self.assertIn(field, study_patterns)
        
        # Check hourly pattern structure
        hourly_pattern = study_patterns['hourly_pattern']
        self.assertEqual(len(hourly_pattern), 24)  # 24 hours
        
        for hour_data in hourly_pattern:
            self.assertIn('hour', hour_data)
            self.assertIn('count', hour_data)
        
        # Check daily pattern structure
        daily_pattern = study_patterns['daily_pattern']
        self.assertEqual(len(daily_pattern), 7)  # 7 days
        
        for day_data in daily_pattern:
            self.assertIn('day', day_data)
            self.assertIn('count', day_data)
    
    def test_achievement_stats_structure(self):
        """Test achievement statistics structure"""
        url = reverse('analytics:advanced-analytics')
        response = self.client.get(url)
        
        achievement_stats = response.data['achievement_stats']
        required_fields = [
            'current_streak', 'max_streak', 'perfect_sessions',
            'mastered_categories', 'monthly_progress',
            'monthly_target', 'monthly_completed'
        ]
        
        for field in required_fields:
            self.assertIn(field, achievement_stats)
        
        # Check data types and ranges
        self.assertIsInstance(achievement_stats['current_streak'], int)
        self.assertIsInstance(achievement_stats['max_streak'], int)
        self.assertGreaterEqual(achievement_stats['monthly_progress'], 0)
        self.assertLessEqual(achievement_stats['monthly_progress'], 100)
    
    def test_performance_metrics_structure(self):
        """Test performance metrics structure"""
        url = reverse('analytics:advanced-analytics')
        response = self.client.get(url)
        
        performance_metrics = response.data['performance_metrics']
        required_fields = [
            'currentStreak', 'longestStreak', 'totalReviews',
            'averageRetention', 'studyEfficiency', 'weeklyGoal', 'weeklyProgress'
        ]
        
        for field in required_fields:
            self.assertIn(field, performance_metrics)
        
        # Check that weekly goal matches user setting
        self.assertEqual(performance_metrics['weeklyGoal'], self.user.weekly_goal)
    
    def test_recommendations_structure(self):
        """Test recommendations structure"""
        url = reverse('analytics:advanced-analytics')
        response = self.client.get(url)
        
        recommendations = response.data['recommendations']
        self.assertIsInstance(recommendations, list)
        
        # Check structure of recommendations if they exist
        if recommendations:
            recommendation = recommendations[0]
            required_fields = ['type', 'title', 'message', 'action']
            
            for field in required_fields:
                self.assertIn(field, recommendation)


class LearningCalendarViewTest(APITestCase):
    """Test LearningCalendarView API endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create test content
        category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
        
        self.content = Content.objects.create(
            title='Test Content',
            content='Test content body',
            author=self.user,
            category=category
        )
        
        # Create review history spanning multiple days with different intensities
        base_date = timezone.now() - timedelta(days=30)
        
        for i in range(30):
            review_date = base_date + timedelta(days=i)
            
            # Create different intensities (review counts) for different days
            if i % 7 == 0:  # Weekly high activity
                review_count = 25  # High intensity (4)
            elif i % 3 == 0:  # Every 3 days medium activity
                review_count = 15  # Medium-high intensity (3)
            elif i % 2 == 0:  # Every other day low activity
                review_count = 5   # Low intensity (1)
            else:
                continue  # No reviews on these days
            
            for j in range(review_count):
                result = ['remembered', 'partial', 'forgot'][j % 3]
                ReviewHistory.objects.create(
                    user=self.user,
                    content=self.content,
                    result=result,
                    review_date=review_date
                )
    
    def test_learning_calendar_view_success(self):
        """Test successful learning calendar retrieval"""
        url = reverse('analytics:learning-calendar')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        data = response.data
        required_fields = ['calendar_data', 'monthly_summary', 'total_active_days', 'best_day']
        
        for field in required_fields:
            self.assertIn(field, data)
    
    def test_calendar_data_structure(self):
        """Test calendar data structure and content"""
        url = reverse('analytics:learning-calendar')
        response = self.client.get(url)
        
        calendar_data = response.data['calendar_data']
        
        # Should have 365 days of data
        self.assertEqual(len(calendar_data), 365)
        
        # Check structure of day data
        day_data = calendar_data[0]
        required_fields = [
            'date', 'count', 'success_rate', 'intensity',
            'remembered', 'partial', 'forgot'
        ]
        
        for field in required_fields:
            self.assertIn(field, day_data)
        
        # Check data types and ranges
        self.assertIsInstance(day_data['count'], int)
        self.assertIsInstance(day_data['success_rate'], (int, float))
        self.assertIsInstance(day_data['intensity'], int)
        self.assertGreaterEqual(day_data['intensity'], 0)
        self.assertLessEqual(day_data['intensity'], 4)
    
    def test_intensity_calculation(self):
        """Test intensity level calculations"""
        url = reverse('analytics:learning-calendar')
        response = self.client.get(url)
        
        calendar_data = response.data['calendar_data']
        
        # Find days with different review counts
        intensity_examples = {}
        for day_data in calendar_data:
            count = day_data['count']
            intensity = day_data['intensity']
            
            if count == 0:
                self.assertEqual(intensity, 0)
            elif 1 <= count <= 9:
                self.assertEqual(intensity, 1)
            elif 10 <= count <= 14:
                self.assertEqual(intensity, 2)
            elif 15 <= count <= 19:
                self.assertEqual(intensity, 3)
            elif count >= 20:
                self.assertEqual(intensity, 4)
    
    def test_monthly_summary_structure(self):
        """Test monthly summary structure"""
        url = reverse('analytics:learning-calendar')
        response = self.client.get(url)
        
        monthly_summary = response.data['monthly_summary']
        
        # Should have up to 12 months of data
        self.assertLessEqual(len(monthly_summary), 12)
        
        if monthly_summary:
            month_data = monthly_summary[0]
            required_fields = ['month', 'total_reviews', 'active_days', 'success_rate']
            
            for field in required_fields:
                self.assertIn(field, month_data)
            
            # Check data validity
            self.assertGreaterEqual(month_data['total_reviews'], 0)
            self.assertGreaterEqual(month_data['active_days'], 0)
            self.assertGreaterEqual(month_data['success_rate'], 0)
            self.assertLessEqual(month_data['success_rate'], 100)
    
    def test_total_active_days_calculation(self):
        """Test total active days calculation"""
        url = reverse('analytics:learning-calendar')
        response = self.client.get(url)
        
        data = response.data
        total_active_days = data['total_active_days']
        calendar_data = data['calendar_data']
        
        # Count active days from calendar data
        expected_active_days = len([d for d in calendar_data if d['count'] > 0])
        
        self.assertEqual(total_active_days, expected_active_days)
        self.assertGreater(total_active_days, 0)  # Should have some active days from setup
    
    def test_best_day_calculation(self):
        """Test best day calculation"""
        url = reverse('analytics:learning-calendar')
        response = self.client.get(url)
        
        data = response.data
        best_day = data['best_day']
        calendar_data = data['calendar_data']
        
        if best_day:
            # Best day should have the maximum count
            max_count = max(d['count'] for d in calendar_data)
            self.assertEqual(best_day['count'], max_count)
            
            # Should have all required fields
            required_fields = [
                'date', 'count', 'success_rate', 'intensity',
                'remembered', 'partial', 'forgot'
            ]
            
            for field in required_fields:
                self.assertIn(field, best_day)


class AnalyticsAccessControlTest(APITestCase):
    """Test access control for analytics endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        # Create another user for access control testing
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        self.other_user.is_email_verified = True
        self.other_user.save()
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied"""
        endpoints = [
            'analytics:dashboard',
            'analytics:review-stats',
            'analytics:advanced-analytics',
            'analytics:learning-calendar'
        ]
        
        for endpoint_name in endpoints:
            url = reverse(endpoint_name)
            response = self.client.get(url)
            
            self.assertEqual(
                response.status_code, 
                status.HTTP_401_UNAUTHORIZED,
                f"Endpoint {endpoint_name} should require authentication"
            )
    
    def test_authenticated_access_allowed(self):
        """Test that authenticated users can access their analytics"""
        # Authenticate as first user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        endpoints = [
            'analytics:dashboard',
            'analytics:review-stats',
            'analytics:advanced-analytics',
            'analytics:learning-calendar'
        ]
        
        for endpoint_name in endpoints:
            url = reverse(endpoint_name)
            response = self.client.get(url)
            
            self.assertEqual(
                response.status_code, 
                status.HTTP_200_OK,
                f"Authenticated user should access {endpoint_name}"
            )
    
    def test_user_data_isolation(self):
        """Test that users only see their own analytics data"""
        # Create content for each user
        category1 = Category.objects.create(name='User1 Category', user=self.user)
        category2 = Category.objects.create(name='User2 Category', user=self.other_user)
        
        content1 = Content.objects.create(
            title='User1 Content',
            content='Content body',
            author=self.user,
            category=category1
        )
        
        content2 = Content.objects.create(
            title='User2 Content',
            content='Content body',
            author=self.other_user,
            category=category2
        )
        
        # Create review history for both users
        ReviewHistory.objects.create(
            user=self.user,
            content=content1,
            result='remembered',
            review_date=timezone.now()
        )
        
        ReviewHistory.objects.create(
            user=self.other_user,
            content=content2,
            result='remembered',
            review_date=timezone.now()
        )
        
        # Test user 1 sees only their data
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('analytics:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_content'], 1)  # Only user1's content
        
        # Test user 2 sees only their data
        refresh = RefreshToken.for_user(self.other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_content'], 1)  # Only user2's content


class AnalyticsEdgeCasesTest(APITestCase):
    """Test edge cases and error conditions for analytics"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_analytics_with_no_data(self):
        """Test analytics endpoints with no user data"""
        endpoints = [
            'analytics:dashboard',
            'analytics:review-stats',
            'analytics:advanced-analytics',
            'analytics:learning-calendar'
        ]
        
        for endpoint_name in endpoints:
            url = reverse(endpoint_name)
            response = self.client.get(url)
            
            # Should still return 200 with default/empty values
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                f"Endpoint {endpoint_name} should handle empty data gracefully"
            )
            
            # Check that response contains expected structure
            data = response.data
            self.assertIsInstance(data, dict)
    
    def test_division_by_zero_protection(self):
        """Test protection against division by zero in calculations"""
        # Create content without any review history
        category = Category.objects.create(name='Test Category', user=self.user)
        Content.objects.create(
            title='Test Content',
            content='Content body',
            author=self.user,
            category=category
        )
        
        url = reverse('analytics:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Success rate should be 0, not cause division by zero error
        self.assertEqual(response.data['success_rate'], 0.0)
        self.assertEqual(response.data['total_reviews_30_days'], 0)
    
    def test_invalid_date_handling(self):
        """Test handling of edge cases in date calculations"""
        # Create content and review
        category = Category.objects.create(name='Test Category', user=self.user)
        content = Content.objects.create(
            title='Test Content',
            content='Content body',
            author=self.user,
            category=category
        )
        
        # Create a review with future date (edge case)
        future_date = timezone.now() + timedelta(days=1)
        ReviewHistory.objects.create(
            user=self.user,
            content=content,
            result='remembered',
            review_date=future_date
        )
        
        # Should still work without errors
        url = reverse('analytics:learning-calendar')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AnalyticsPerformanceTest(APITestCase):
    """Test performance aspects of analytics endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create large dataset for performance testing
        categories = []
        contents = []
        
        # Create multiple categories and content items
        for i in range(5):
            category = Category.objects.create(
                name=f'Category {i}',
                user=self.user
            )
            categories.append(category)
            
            for j in range(10):
                content = Content.objects.create(
                    title=f'Content {i}-{j}',
                    content=f'Content body {i}-{j}',
                    author=self.user,
                    category=category
                )
                contents.append(content)
        
        # Create large review history (365 days * multiple reviews per day)
        base_date = timezone.now() - timedelta(days=365)
        
        for day in range(365):
            review_date = base_date + timedelta(days=day)
            content_count = len(contents)
            
            # Create 5-10 reviews per day
            for review_num in range(5 + (day % 6)):
                content_index = (day + review_num) % content_count
                result = ['remembered', 'partial', 'forgot'][review_num % 3]
                
                ReviewHistory.objects.create(
                    user=self.user,
                    content=contents[content_index],
                    result=result,
                    review_date=review_date
                )
    
    def test_dashboard_performance_with_large_dataset(self):
        """Test dashboard performance with large dataset"""
        url = reverse('analytics:dashboard')
        
        start_time = timezone.now()
        response = self.client.get(url)
        end_time = timezone.now()
        
        # Should complete within reasonable time (5 seconds for large dataset)
        response_time = (end_time - start_time).total_seconds()
        self.assertLess(response_time, 5.0)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify data integrity
        data = response.data
        self.assertEqual(data['total_content'], 50)  # 5 categories * 10 content each
        self.assertGreater(data['total_reviews_30_days'], 0)
    
    def test_calendar_view_performance_with_large_dataset(self):
        """Test calendar view performance with large dataset"""
        url = reverse('analytics:learning-calendar')
        
        start_time = timezone.now()
        response = self.client.get(url)
        end_time = timezone.now()
        
        # Should complete within reasonable time
        response_time = (end_time - start_time).total_seconds()
        self.assertLess(response_time, 10.0)  # More lenient for calendar data processing
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response structure and data
        data = response.data
        self.assertEqual(len(data['calendar_data']), 365)
        self.assertGreater(data['total_active_days'], 0)
    
    def test_advanced_analytics_performance_with_large_dataset(self):
        """Test advanced analytics performance with large dataset"""
        url = reverse('analytics:advanced-analytics')
        
        start_time = timezone.now()
        response = self.client.get(url)
        end_time = timezone.now()
        
        # Should complete within reasonable time
        response_time = (end_time - start_time).total_seconds()
        self.assertLess(response_time, 15.0)  # Most complex endpoint, more lenient
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify comprehensive data
        data = response.data
        self.assertEqual(len(data['category_performance']), 5)  # 5 categories
        self.assertGreater(data['learning_insights']['total_reviews'], 1000)  # Should have many reviews