"""
Test cases for business_intelligence application
"""
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Subscription, SubscriptionTier
from content.models import Category, Content
from review.models import ReviewHistory, ReviewSchedule
from .models import (ContentEffectiveness, LearningPattern,
                     SubscriptionAnalytics, SystemUsageMetrics)

User = get_user_model()


class BusinessIntelligenceModelTest(TestCase):
    """Test Business Intelligence models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        # Create test content
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
    
    def test_learning_pattern_model_creation(self):
        """Test LearningPattern model creation and properties"""
        today = timezone.now().date()
        
        pattern = LearningPattern.objects.create(
            user=self.user,
            date=today,
            contents_created=5,
            reviews_completed=15,
            ai_questions_generated=8,
            session_duration_minutes=120,
            success_rate=85.5,
            average_review_time_seconds=45,
            peak_activity_hour=14,
            login_count=3,
            consecutive_days=7
        )
        
        self.assertEqual(pattern.user, self.user)
        self.assertEqual(pattern.date, today)
        self.assertEqual(pattern.contents_created, 5)
        self.assertEqual(pattern.reviews_completed, 15)
        self.assertEqual(pattern.ai_questions_generated, 8)
        self.assertEqual(pattern.session_duration_minutes, 120)
        self.assertEqual(pattern.success_rate, 85.5)
        self.assertEqual(pattern.average_review_time_seconds, 45)
        self.assertEqual(pattern.peak_activity_hour, 14)
        self.assertEqual(pattern.login_count, 3)
        self.assertEqual(pattern.consecutive_days, 7)
        
        # Check string representation
        expected_str = f"{self.user.email} - {today}"
        self.assertEqual(str(pattern), expected_str)
    
    def test_learning_pattern_unique_constraint(self):
        """Test unique constraint on user and date"""
        today = timezone.now().date()
        
        # Create first pattern
        LearningPattern.objects.create(
            user=self.user,
            date=today,
            contents_created=1
        )
        
        # Attempt to create duplicate should raise IntegrityError
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            LearningPattern.objects.create(
                user=self.user,
                date=today,
                contents_created=2
            )
    
    def test_content_effectiveness_model_creation(self):
        """Test ContentEffectiveness model creation"""
        effectiveness = ContentEffectiveness.objects.create(
            content=self.content,
            total_reviews=20,
            successful_reviews=15,
            average_difficulty_rating=3.5,
            average_review_time_seconds=60,
            time_to_master_days=14,
            ai_questions_generated=5,
            ai_questions_success_rate=80.0,
            last_reviewed=timezone.now(),
            abandonment_risk_score=25.5
        )
        
        self.assertEqual(effectiveness.content, self.content)
        self.assertEqual(effectiveness.total_reviews, 20)
        self.assertEqual(effectiveness.successful_reviews, 15)
        self.assertEqual(effectiveness.average_difficulty_rating, 3.5)
        self.assertEqual(effectiveness.average_review_time_seconds, 60)
        self.assertEqual(effectiveness.time_to_master_days, 14)
        self.assertEqual(effectiveness.ai_questions_generated, 5)
        self.assertEqual(effectiveness.ai_questions_success_rate, 80.0)
        self.assertEqual(effectiveness.abandonment_risk_score, 25.5)
        
        # Test success_rate property
        expected_success_rate = (15 / 20) * 100  # 75.0
        self.assertEqual(effectiveness.success_rate, 75.0)
        
        # Check string representation
        expected_str = f"Effectiveness: {self.content.title}"
        self.assertEqual(str(effectiveness), expected_str)
    
    def test_content_effectiveness_success_rate_no_reviews(self):
        """Test success rate calculation with no reviews"""
        effectiveness = ContentEffectiveness.objects.create(
            content=self.content,
            total_reviews=0,
            successful_reviews=0
        )
        
        # Should return 0.0 when no reviews
        self.assertEqual(effectiveness.success_rate, 0.0)
    
    def test_subscription_analytics_model_creation(self):
        """Test SubscriptionAnalytics model creation"""
        start_date = timezone.now()
        
        analytics = SubscriptionAnalytics.objects.create(
            user=self.user,
            subscription_tier='BASIC',
            tier_start_date=start_date,
            is_active=True,
            total_content_created=25,
            total_reviews_completed=150,
            total_ai_questions_used=45,
            total_session_time_hours=35.5,
            days_active=20,
            average_daily_reviews=7.5,
            feature_adoption_score=75.0,
            upgrade_probability=65.0,
            churn_risk_score=20.0
        )
        
        self.assertEqual(analytics.user, self.user)
        self.assertEqual(analytics.subscription_tier, 'BASIC')
        self.assertEqual(analytics.tier_start_date, start_date)
        self.assertTrue(analytics.is_active)
        self.assertEqual(analytics.total_content_created, 25)
        self.assertEqual(analytics.total_reviews_completed, 150)
        self.assertEqual(analytics.total_ai_questions_used, 45)
        self.assertEqual(analytics.total_session_time_hours, 35.5)
        self.assertEqual(analytics.days_active, 20)
        self.assertEqual(analytics.average_daily_reviews, 7.5)
        self.assertEqual(analytics.feature_adoption_score, 75.0)
        self.assertEqual(analytics.upgrade_probability, 65.0)
        self.assertEqual(analytics.churn_risk_score, 20.0)
        
        # Check string representation
        expected_str = f"{self.user.email} - BASIC ({start_date.date()})"
        self.assertEqual(str(analytics), expected_str)
    
    def test_system_usage_metrics_model_creation(self):
        """Test SystemUsageMetrics model creation"""
        today = timezone.now().date()
        
        metrics = SystemUsageMetrics.objects.create(
            date=today,
            total_users=1500,
            active_users_daily=250,
            new_users=15,
            churned_users=5,
            free_users=800,
            basic_users=500,
            pro_users=200,
            subscription_revenue_usd=Decimal('15000.00'),
            total_content_created=450,
            total_reviews_completed=2500,
            average_success_rate=78.5,
            ai_questions_generated=1200,
            ai_cost_usd=Decimal('125.50'),
            ai_tokens_used=50000,
            average_api_response_time_ms=180,
            error_rate_percentage=1.2,
            uptime_percentage=99.8
        )
        
        self.assertEqual(metrics.date, today)
        self.assertEqual(metrics.total_users, 1500)
        self.assertEqual(metrics.active_users_daily, 250)
        self.assertEqual(metrics.new_users, 15)
        self.assertEqual(metrics.churned_users, 5)
        self.assertEqual(metrics.free_users, 800)
        self.assertEqual(metrics.basic_users, 500)
        self.assertEqual(metrics.pro_users, 200)
        self.assertEqual(metrics.subscription_revenue_usd, Decimal('15000.00'))
        self.assertEqual(metrics.total_content_created, 450)
        self.assertEqual(metrics.total_reviews_completed, 2500)
        self.assertEqual(metrics.average_success_rate, 78.5)
        self.assertEqual(metrics.ai_questions_generated, 1200)
        self.assertEqual(metrics.ai_cost_usd, Decimal('125.50'))
        self.assertEqual(metrics.ai_tokens_used, 50000)
        self.assertEqual(metrics.average_api_response_time_ms, 180)
        self.assertEqual(metrics.error_rate_percentage, 1.2)
        self.assertEqual(metrics.uptime_percentage, 99.8)
        
        # Check string representation
        expected_str = f"System Metrics - {today}"
        self.assertEqual(str(metrics), expected_str)
    
    def test_system_usage_metrics_unique_date(self):
        """Test unique constraint on date"""
        today = timezone.now().date()
        
        # Create first metrics record
        SystemUsageMetrics.objects.create(
            date=today,
            total_users=100
        )
        
        # Attempt to create duplicate should raise IntegrityError
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            SystemUsageMetrics.objects.create(
                date=today,
                total_users=200
            )


class BusinessIntelligenceViewTest(APITestCase):
    """Test Business Intelligence API views"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create regular user
        self.user = User.objects.create_user(
            email='user@example.com',
            password='userpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        self.admin_user.is_email_verified = True
        self.admin_user.save()
        
        # Create subscription for user
        self.subscription = Subscription.objects.create(
            user=self.user,
            tier=SubscriptionTier.BASIC,
            amount_paid=Decimal('9.99'),
            is_active=True
        )
        
        # Create test data
        self._create_test_data()
    
    def _create_test_data(self):
        """Create test data for Business Intelligence"""
        # Create content
        category = Category.objects.create(name='Test Category', user=self.user)
        content = Content.objects.create(
            title='Test Content',
            content='Content body',
            author=self.user,
            category=category
        )
        
        # Create learning patterns
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            LearningPattern.objects.create(
                user=self.user,
                date=date,
                contents_created=2 + i % 3,
                reviews_completed=10 + i * 2,
                ai_questions_generated=3 + i % 4,
                session_duration_minutes=60 + i * 10,
                success_rate=75.0 + (i * 2),
                average_review_time_seconds=45 + i,
                peak_activity_hour=9 + (i % 6),
                login_count=1 + i % 3,
                consecutive_days=i + 1
            )
        
        # Create content effectiveness
        ContentEffectiveness.objects.create(
            content=content,
            total_reviews=25,
            successful_reviews=20,
            average_difficulty_rating=3.0,
            average_review_time_seconds=50,
            time_to_master_days=10,
            ai_questions_generated=8,
            ai_questions_success_rate=85.0,
            last_reviewed=timezone.now(),
            abandonment_risk_score=15.0
        )
        
        # Create subscription analytics
        SubscriptionAnalytics.objects.create(
            user=self.user,
            subscription_tier='BASIC',
            tier_start_date=timezone.now() - timedelta(days=30),
            is_active=True,
            total_content_created=20,
            total_reviews_completed=200,
            total_ai_questions_used=50,
            total_session_time_hours=40.0,
            days_active=25,
            average_daily_reviews=8.0,
            feature_adoption_score=80.0,
            upgrade_probability=60.0,
            churn_risk_score=25.0
        )
        
        # Create review history for realistic data
        for i in range(10):
            ReviewHistory.objects.create(
                user=self.user,
                content=content,
                result=['remembered', 'partial', 'forgot'][i % 3],
                review_date=timezone.now() - timedelta(days=i),
                time_spent=45 + i
            )
    
    def _authenticate_user(self):
        """Authenticate as regular user"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def _authenticate_admin(self):
        """Authenticate as admin user"""
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')


class LearningInsightsViewTest(BusinessIntelligenceViewTest):
    """Test LearningInsightsView"""
    
    @patch('business_intelligence.views.LearningAnalyticsEngine')
    def test_learning_insights_success(self, mock_engine_class):
        """Test successful learning insights retrieval"""
        # Mock the analytics engine
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.get_learning_insights.return_value = {
            'total_study_days': 30,
            'current_streak': 7,
            'longest_streak': 14,
            'average_daily_reviews': 8.5,
            'overall_success_rate': 82.3,
            'most_productive_hour': 14,
            'total_study_time_hours': 45.5,
            'learning_consistency_score': 78.0
        }
        
        self._authenticate_user()
        
        url = reverse('business_intelligence:learning-insights')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the mock was called correctly
        mock_engine_class.assert_called_once_with(self.user)
        mock_engine.get_learning_insights.assert_called_once_with(30)  # default days
        
        # Check response structure
        data = response.data
        expected_fields = [
            'total_study_days', 'current_streak', 'longest_streak',
            'average_daily_reviews', 'overall_success_rate',
            'most_productive_hour', 'total_study_time_hours',
            'learning_consistency_score'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
    
    @patch('business_intelligence.views.LearningAnalyticsEngine')
    def test_learning_insights_custom_days(self, mock_engine_class):
        """Test learning insights with custom days parameter"""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.get_learning_insights.return_value = {}
        
        self._authenticate_user()
        
        url = reverse('business_intelligence:learning-insights')
        response = self.client.get(url, {'days': 60})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_engine.get_learning_insights.assert_called_once_with(60)
    
    def test_learning_insights_unauthenticated(self):
        """Test learning insights requires authentication"""
        url = reverse('business_intelligence:learning-insights')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ContentAnalyticsViewTest(BusinessIntelligenceViewTest):
    """Test ContentAnalyticsView"""
    
    @patch('business_intelligence.views.LearningAnalyticsEngine')
    def test_content_analytics_success(self, mock_engine_class):
        """Test successful content analytics retrieval"""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.get_content_analytics.return_value = {
            'total_content': 15,
            'mastered_content': 8,
            'struggling_content': 3,
            'average_mastery_time_days': 12.5,
            'most_effective_content_type': 'Flashcard',
            'least_effective_content_type': 'Long Text',
            'category_performance': [
                {'name': 'Math', 'success_rate': 85.0},
                {'name': 'History', 'success_rate': 72.0}
            ],
            'difficulty_distribution': {
                'easy': 5,
                'medium': 7,
                'hard': 3
            }
        }
        
        self._authenticate_user()
        
        url = reverse('business_intelligence:content-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the mock was called correctly
        mock_engine_class.assert_called_once_with(self.user)
        mock_engine.get_content_analytics.assert_called_once()
        
        # Check response structure
        data = response.data
        expected_fields = [
            'total_content', 'mastered_content', 'struggling_content',
            'average_mastery_time_days', 'most_effective_content_type',
            'least_effective_content_type', 'category_performance',
            'difficulty_distribution'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)


class PerformanceTrendViewTest(BusinessIntelligenceViewTest):
    """Test PerformanceTrendView"""
    
    @patch('business_intelligence.views.LearningAnalyticsEngine')
    def test_performance_trend_success(self, mock_engine_class):
        """Test successful performance trend retrieval"""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.get_performance_trends.return_value = [
            {
                'date': '2023-10-01',
                'success_rate': 85.0,
                'reviews_completed': 12,
                'study_time_minutes': 90,
                'difficulty_trend': 3.2,
                'engagement_score': 78.5
            },
            {
                'date': '2023-10-02',
                'success_rate': 88.0,
                'reviews_completed': 15,
                'study_time_minutes': 105,
                'difficulty_trend': 3.0,
                'engagement_score': 82.0
            }
        ]
        
        self._authenticate_user()
        
        url = reverse('business_intelligence:performance-trends')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the mock was called correctly
        mock_engine_class.assert_called_once_with(self.user)
        mock_engine.get_performance_trends.assert_called_once_with(30)  # default days
        
        # Check response is a list
        data = response.data
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        
        # Check structure of first trend data
        if data:
            trend = data[0]
            expected_fields = [
                'date', 'success_rate', 'reviews_completed',
                'study_time_minutes', 'difficulty_trend', 'engagement_score'
            ]
            for field in expected_fields:
                self.assertIn(field, trend)


class LearningRecommendationsViewTest(BusinessIntelligenceViewTest):
    """Test LearningRecommendationsView"""
    
    @patch('business_intelligence.views.RecommendationEngine')
    def test_learning_recommendations_success(self, mock_engine_class):
        """Test successful learning recommendations retrieval"""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.generate_recommendations.return_value = [
            {
                'type': 'schedule_optimization',
                'title': 'Optimize Study Schedule',
                'message': 'Consider studying at 2 PM for better performance',
                'priority': 'high',
                'action_required': True
            },
            {
                'type': 'content_recommendation',
                'title': 'Focus on Weak Areas',
                'message': 'Spend more time on History category',
                'priority': 'medium',
                'action_required': False
            }
        ]
        
        self._authenticate_user()
        
        url = reverse('business_intelligence:learning-recommendations')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the mock was called correctly
        mock_engine_class.assert_called_once_with(self.user)
        mock_engine.generate_recommendations.assert_called_once()
        
        # Check response is a list
        data = response.data
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        
        # Check structure of first recommendation
        if data:
            recommendation = data[0]
            expected_fields = [
                'type', 'title', 'message', 'priority', 'action_required'
            ]
            for field in expected_fields:
                self.assertIn(field, recommendation)
    
    @patch('business_intelligence.views.RecommendationEngine')
    def test_learning_recommendations_error_handling(self, mock_engine_class):
        """Test error handling in learning recommendations"""
        mock_engine_class.side_effect = Exception("Recommendation engine error")
        
        self._authenticate_user()
        
        url = reverse('business_intelligence:learning-recommendations')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('detail', response.data)


class SubscriptionInsightsViewTest(BusinessIntelligenceViewTest):
    """Test SubscriptionInsightsView"""
    
    @patch('business_intelligence.views.LearningAnalyticsEngine')
    def test_subscription_insights_with_subscription(self, mock_engine_class):
        """Test subscription insights for user with subscription"""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.get_learning_insights.return_value = {
            'average_daily_reviews': 8.5,
            'learning_consistency_score': 75.0
        }
        
        self._authenticate_user()
        
        url = reverse('business_intelligence:subscription-insights')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        expected_fields = [
            'current_tier', 'tier_duration_days', 'feature_utilization_rate',
            'upgrade_recommendation', 'usage_efficiency_score',
            'cost_per_review', 'projected_monthly_value'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
        
        # Check specific values
        self.assertEqual(data['current_tier'], 'BASIC')
        self.assertGreaterEqual(data['tier_duration_days'], 0)
        self.assertIsInstance(data['feature_utilization_rate'], (int, float))
        self.assertIsInstance(data['upgrade_recommendation'], str)
    
    def test_subscription_insights_without_subscription(self):
        """Test subscription insights for user without subscription"""
        # Create user without subscription
        user_no_sub = User.objects.create_user(
            email='nosub@example.com',
            password='testpass123'
        )
        user_no_sub.is_email_verified = True
        user_no_sub.save()
        
        refresh = RefreshToken.for_user(user_no_sub)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('business_intelligence:subscription-insights')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(data['current_tier'], 'FREE')
        self.assertEqual(data['tier_duration_days'], 0)
        self.assertEqual(data['cost_per_review'], 0.0)


class BusinessDashboardViewTest(BusinessIntelligenceViewTest):
    """Test BusinessDashboardView (Admin only)"""
    
    @patch('business_intelligence.views.BusinessMetricsEngine')
    def test_business_dashboard_admin_access(self, mock_engine_class):
        """Test admin can access business dashboard"""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.get_business_dashboard.return_value = {
            'user_metrics': {
                'total_users': 1000,
                'active_users': 250,
                'new_users': 25,
                'churn_rate': 2.5
            },
            'revenue_metrics': {
                'total_revenue': 15000.0,
                'mrr': 5000.0,
                'arpu': 12.50
            },
            'engagement_metrics': {
                'daily_active_users': 180,
                'session_duration': 25.5,
                'retention_rate': 85.0
            },
            'content_metrics': {
                'total_content': 5000,
                'content_completion_rate': 75.0,
                'average_reviews_per_content': 8.5
            },
            'subscription_metrics': {
                'conversion_rate': 15.0,
                'upgrade_rate': 8.0,
                'cancellation_rate': 3.0
            },
            'ai_usage_metrics': {
                'total_ai_requests': 10000,
                'ai_success_rate': 95.0,
                'ai_cost_efficiency': 0.05
            },
            'system_performance': {
                'avg_response_time': 180,
                'uptime': 99.9,
                'error_rate': 0.1
            }
        }
        
        self._authenticate_admin()
        
        url = reverse('business_intelligence:business-dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the mock was called correctly
        mock_engine_class.assert_called_once()
        mock_engine.get_business_dashboard.assert_called_once_with(30)  # default days
        
        # Check response structure
        data = response.data
        expected_sections = [
            'user_metrics', 'revenue_metrics', 'engagement_metrics',
            'content_metrics', 'subscription_metrics', 'ai_usage_metrics',
            'system_performance'
        ]
        
        for section in expected_sections:
            self.assertIn(section, data)
    
    def test_business_dashboard_regular_user_denied(self):
        """Test regular user cannot access business dashboard"""
        self._authenticate_user()
        
        url = reverse('business_intelligence:business-dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_business_dashboard_unauthenticated_denied(self):
        """Test unauthenticated user cannot access business dashboard"""
        url = reverse('business_intelligence:business-dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    @patch('business_intelligence.views.BusinessMetricsEngine')
    def test_business_dashboard_custom_days(self, mock_engine_class):
        """Test business dashboard with custom days parameter"""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.get_business_dashboard.return_value = {}
        
        self._authenticate_admin()
        
        url = reverse('business_intelligence:business-dashboard')
        response = self.client.get(url, {'days': 60})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_engine.get_business_dashboard.assert_called_once_with(60)


class UpdateLearningPatternViewTest(BusinessIntelligenceViewTest):
    """Test update_learning_pattern view"""
    
    def test_update_learning_pattern_new_record(self):
        """Test creating new learning pattern record"""
        self._authenticate_user()
        
        target_date = timezone.now().date()
        data = {
            'date': target_date.isoformat(),
            'session_duration_minutes': 90,
            'peak_activity_hour': 14
        }
        
        url = reverse('business_intelligence:update-learning-pattern')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response
        response_data = response.data
        self.assertIn('message', response_data)
        self.assertEqual(response_data['date'], target_date)
        self.assertEqual(response_data['session_duration_minutes'], 90)
        
        # Verify record was created
        pattern = LearningPattern.objects.get(user=self.user, date=target_date)
        self.assertEqual(pattern.session_duration_minutes, 90)
        self.assertEqual(pattern.peak_activity_hour, 14)
    
    def test_update_learning_pattern_existing_record(self):
        """Test updating existing learning pattern record"""
        target_date = timezone.now().date()
        
        # Create existing pattern
        existing_pattern = LearningPattern.objects.create(
            user=self.user,
            date=target_date,
            session_duration_minutes=60,
            peak_activity_hour=10
        )
        
        self._authenticate_user()
        
        data = {
            'date': target_date.isoformat(),
            'session_duration_minutes': 30,  # Additional time
            'peak_activity_hour': 14  # New peak hour
        }
        
        url = reverse('business_intelligence:update-learning-pattern')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check updated values
        existing_pattern.refresh_from_db()
        self.assertEqual(existing_pattern.session_duration_minutes, 90)  # 60 + 30
        self.assertEqual(existing_pattern.peak_activity_hour, 14)  # Updated
    
    def test_update_learning_pattern_default_date(self):
        """Test updating learning pattern with default date (today)"""
        self._authenticate_user()
        
        data = {
            'session_duration_minutes': 45
        }
        
        url = reverse('business_intelligence:update-learning-pattern')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should use today's date
        today = timezone.now().date()
        pattern = LearningPattern.objects.get(user=self.user, date=today)
        self.assertEqual(pattern.session_duration_minutes, 45)
    
    def test_update_learning_pattern_unauthenticated(self):
        """Test updating learning pattern requires authentication"""
        data = {
            'session_duration_minutes': 45
        }
        
        url = reverse('business_intelligence:update-learning-pattern')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SubscriptionAnalysisViewTest(BusinessIntelligenceViewTest):
    """Test SubscriptionAnalysisView (Admin only)"""
    
    @patch('business_intelligence.views.SubscriptionAnalyzer')
    def test_subscription_analysis_conversion_funnel(self, mock_analyzer_class):
        """Test subscription conversion funnel analysis"""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.analyze_conversion_funnel.return_value = {
            'stages': [
                {'stage': 'visitor', 'count': 1000, 'conversion_rate': 100.0},
                {'stage': 'signup', 'count': 200, 'conversion_rate': 20.0},
                {'stage': 'trial', 'count': 50, 'conversion_rate': 25.0},
                {'stage': 'paid', 'count': 15, 'conversion_rate': 30.0}
            ],
            'overall_conversion_rate': 1.5
        }
        
        self._authenticate_admin()
        
        url = reverse('business_intelligence:subscription-analysis')
        response = self.client.get(url, {'analysis_type': 'conversion-funnel'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the mock was called correctly
        mock_analyzer.analyze_conversion_funnel.assert_called_once_with(30)  # default days
        
        # Check response structure
        data = response.data
        self.assertIn('stages', data)
        self.assertIn('overall_conversion_rate', data)
    
    @patch('business_intelligence.views.SubscriptionAnalyzer')
    def test_subscription_analysis_churn_patterns(self, mock_analyzer_class):
        """Test subscription churn patterns analysis"""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.analyze_churn_patterns.return_value = {
            'churn_rate': 5.2,
            'churn_reasons': [
                {'reason': 'price', 'percentage': 35.0},
                {'reason': 'lack_of_use', 'percentage': 28.0},
                {'reason': 'features', 'percentage': 22.0}
            ],
            'at_risk_users': 45
        }
        
        self._authenticate_admin()
        
        url = reverse('business_intelligence:subscription-analysis')
        response = self.client.get(url, {'analysis_type': 'churn-patterns', 'days': 60})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        mock_analyzer.analyze_churn_patterns.assert_called_once_with(60)
        
        data = response.data
        self.assertIn('churn_rate', data)
        self.assertIn('churn_reasons', data)
        self.assertIn('at_risk_users', data)
    
    @patch('business_intelligence.views.SubscriptionAnalyzer')
    def test_subscription_analysis_customer_lifetime_value(self, mock_analyzer_class):
        """Test customer lifetime value analysis"""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.calculate_customer_lifetime_value.return_value = {
            'basic_clv': 125.50,
            'pro_clv': 280.75,
            'average_clv': 165.25,
            'clv_trends': [
                {'month': '2023-10', 'clv': 150.0},
                {'month': '2023-11', 'clv': 160.0}
            ]
        }
        
        self._authenticate_admin()
        
        url = reverse('business_intelligence:subscription-analysis')
        response = self.client.get(url, {
            'analysis_type': 'customer-lifetime-value',
            'tier': 'BASIC'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        mock_analyzer.calculate_customer_lifetime_value.assert_called_once_with('BASIC')
        
        data = response.data
        self.assertIn('basic_clv', data)
        self.assertIn('pro_clv', data)
        self.assertIn('average_clv', data)
    
    def test_subscription_analysis_missing_type(self):
        """Test subscription analysis with missing analysis_type"""
        self._authenticate_admin()
        
        url = reverse('business_intelligence:subscription-analysis')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    def test_subscription_analysis_invalid_type(self):
        """Test subscription analysis with invalid analysis_type"""
        self._authenticate_admin()
        
        url = reverse('business_intelligence:subscription-analysis')
        response = self.client.get(url, {'analysis_type': 'invalid-type'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    def test_subscription_analysis_regular_user_denied(self):
        """Test regular user cannot access subscription analysis"""
        self._authenticate_user()
        
        url = reverse('business_intelligence:subscription-analysis')
        response = self.client.get(url, {'analysis_type': 'conversion-funnel'})
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ConversionProbabilityViewTest(BusinessIntelligenceViewTest):
    """Test ConversionProbabilityView (Admin only)"""
    
    @patch('business_intelligence.views.SubscriptionAnalyzer')
    def test_conversion_probability_success(self, mock_analyzer_class):
        """Test successful conversion probability prediction"""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.predict_conversion_probability.return_value = {
            'user_id': self.user.id,
            'conversion_probability': 75.5,
            'factors': [
                {'factor': 'content_creation', 'weight': 30, 'score': 85},
                {'factor': 'review_activity', 'weight': 25, 'score': 70},
                {'factor': 'streak_consistency', 'weight': 20, 'score': 80}
            ],
            'recommendation': 'High conversion probability - consider targeted upgrade offer'
        }
        
        self._authenticate_admin()
        
        url = reverse('business_intelligence:conversion-probability')
        response = self.client.get(url, {'user_id': str(self.user.id)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        mock_analyzer.predict_conversion_probability.assert_called_once_with(self.user.id)
        
        data = response.data
        expected_fields = [
            'user_id', 'conversion_probability', 'factors', 'recommendation'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)
    
    def test_conversion_probability_missing_user_id(self):
        """Test conversion probability with missing user_id"""
        self._authenticate_admin()
        
        url = reverse('business_intelligence:conversion-probability')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    def test_conversion_probability_invalid_user_id(self):
        """Test conversion probability with invalid user_id"""
        self._authenticate_admin()
        
        url = reverse('business_intelligence:conversion-probability')
        response = self.client.get(url, {'user_id': 'invalid'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    @patch('business_intelligence.views.SubscriptionAnalyzer')
    def test_conversion_probability_user_not_found(self, mock_analyzer_class):
        """Test conversion probability with non-existent user"""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.predict_conversion_probability.return_value = {
            'error': 'User not found'
        }
        
        self._authenticate_admin()
        
        url = reverse('business_intelligence:conversion-probability')
        response = self.client.get(url, {'user_id': '99999'})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_conversion_probability_regular_user_denied(self):
        """Test regular user cannot access conversion probability"""
        self._authenticate_user()
        
        url = reverse('business_intelligence:conversion-probability')
        response = self.client.get(url, {'user_id': str(self.user.id)})
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class BusinessIntelligenceIntegrationTest(APITestCase):
    """Test Business Intelligence system integration"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        self.admin_user.is_email_verified = True
        self.admin_user.save()
        
        # Create comprehensive test data
        self._create_comprehensive_test_data()
    
    def _create_comprehensive_test_data(self):
        """Create comprehensive test data for integration testing"""
        # Create subscription
        Subscription.objects.create(
            user=self.user,
            tier=SubscriptionTier.BASIC,
            amount_paid=Decimal('9.99'),
            is_active=True
        )
        
        # Create content and categories
        category = Category.objects.create(name='Integration Test', user=self.user)
        content = Content.objects.create(
            title='Integration Content',
            content='Content for integration testing',
            author=self.user,
            category=category
        )
        
        # Create learning patterns for multiple days
        for i in range(14):
            date = timezone.now().date() - timedelta(days=i)
            LearningPattern.objects.create(
                user=self.user,
                date=date,
                contents_created=2 + (i % 3),
                reviews_completed=8 + (i % 5),
                ai_questions_generated=3 + (i % 4),
                session_duration_minutes=45 + (i * 5),
                success_rate=70.0 + (i * 2),
                average_review_time_seconds=40 + i,
                peak_activity_hour=9 + (i % 8),
                login_count=1 + (i % 2),
                consecutive_days=max(1, 14 - i)
            )
        
        # Create content effectiveness
        ContentEffectiveness.objects.create(
            content=content,
            total_reviews=30,
            successful_reviews=24,
            average_difficulty_rating=3.2,
            average_review_time_seconds=55,
            time_to_master_days=8,
            ai_questions_generated=12,
            ai_questions_success_rate=85.0,
            last_reviewed=timezone.now(),
            abandonment_risk_score=20.0
        )
        
        # Create review history
        for i in range(20):
            ReviewHistory.objects.create(
                user=self.user,
                content=content,
                result=['remembered', 'partial', 'forgot'][(i % 3)],
                review_date=timezone.now() - timedelta(days=i),
                time_spent=40 + (i % 10)
            )
    
    def test_complete_user_analytics_workflow(self):
        """Test complete user analytics workflow"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Step 1: Update learning pattern
        pattern_url = reverse('business_intelligence:update-learning-pattern')
        pattern_data = {
            'session_duration_minutes': 60,
            'peak_activity_hour': 14
        }
        pattern_response = self.client.post(pattern_url, pattern_data)
        self.assertEqual(pattern_response.status_code, status.HTTP_200_OK)
        
        # Step 2: Get learning insights
        with patch('business_intelligence.views.LearningAnalyticsEngine') as mock_engine:
            mock_engine.return_value.get_learning_insights.return_value = {
                'total_study_days': 14,
                'current_streak': 5,
                'average_daily_reviews': 10.0,
                'overall_success_rate': 80.0,
                'learning_consistency_score': 85.0
            }
            
            insights_url = reverse('business_intelligence:learning-insights')
            insights_response = self.client.get(insights_url)
            self.assertEqual(insights_response.status_code, status.HTTP_200_OK)
        
        # Step 3: Get performance trends
        with patch('business_intelligence.views.LearningAnalyticsEngine') as mock_engine:
            mock_engine.return_value.get_performance_trends.return_value = []
            
            trends_url = reverse('business_intelligence:performance-trends')
            trends_response = self.client.get(trends_url)
            self.assertEqual(trends_response.status_code, status.HTTP_200_OK)
        
        # Step 4: Get recommendations
        with patch('business_intelligence.views.RecommendationEngine') as mock_engine:
            mock_engine.return_value.generate_recommendations.return_value = []
            
            recs_url = reverse('business_intelligence:learning-recommendations')
            recs_response = self.client.get(recs_url)
            self.assertEqual(recs_response.status_code, status.HTTP_200_OK)
        
        # Step 5: Get subscription insights
        sub_url = reverse('business_intelligence:subscription-insights')
        sub_response = self.client.get(sub_url)
        self.assertEqual(sub_response.status_code, status.HTTP_200_OK)
    
    def test_admin_analytics_workflow(self):
        """Test admin analytics workflow"""
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Step 1: Get business dashboard
        with patch('business_intelligence.views.BusinessMetricsEngine') as mock_engine:
            mock_engine.return_value.get_business_dashboard.return_value = {
                'user_metrics': {'total_users': 100},
                'revenue_metrics': {'total_revenue': 1000.0},
                'engagement_metrics': {'daily_active_users': 50},
                'content_metrics': {'total_content': 500},
                'subscription_metrics': {'conversion_rate': 10.0},
                'ai_usage_metrics': {'total_ai_requests': 1000},
                'system_performance': {'avg_response_time': 200}
            }
            
            dashboard_url = reverse('business_intelligence:business-dashboard')
            dashboard_response = self.client.get(dashboard_url)
            self.assertEqual(dashboard_response.status_code, status.HTTP_200_OK)
        
        # Step 2: Analyze subscription conversion funnel
        with patch('business_intelligence.views.SubscriptionAnalyzer') as mock_analyzer:
            mock_analyzer.return_value.analyze_conversion_funnel.return_value = {
                'stages': [],
                'overall_conversion_rate': 5.0
            }
            
            analysis_url = reverse('business_intelligence:subscription-analysis')
            analysis_response = self.client.get(analysis_url, {
                'analysis_type': 'conversion-funnel'
            })
            self.assertEqual(analysis_response.status_code, status.HTTP_200_OK)
        
        # Step 3: Predict user conversion probability
        with patch('business_intelligence.views.SubscriptionAnalyzer') as mock_analyzer:
            mock_analyzer.return_value.predict_conversion_probability.return_value = {
                'user_id': self.user.id,
                'conversion_probability': 75.0,
                'factors': [],
                'recommendation': 'High conversion probability'
            }
            
            prediction_url = reverse('business_intelligence:conversion-probability')
            prediction_response = self.client.get(prediction_url, {
                'user_id': str(self.user.id)
            })
            self.assertEqual(prediction_response.status_code, status.HTTP_200_OK)
    
    def test_access_control_enforcement(self):
        """Test access control is properly enforced across all endpoints"""
        user_endpoints = [
            'business_intelligence:learning-insights',
            'business_intelligence:content-analytics',
            'business_intelligence:performance-trends',
            'business_intelligence:learning-recommendations',
            'business_intelligence:subscription-insights',
        ]
        
        admin_endpoints = [
            'business_intelligence:business-dashboard',
            'business_intelligence:subscription-analysis',
            'business_intelligence:conversion-probability',
        ]
        
        # Test user endpoints with authentication
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        for endpoint_name in user_endpoints:
            url = reverse(endpoint_name)
            if endpoint_name == 'business_intelligence:update-learning-pattern':
                response = self.client.post(url, {})
            else:
                with patch('business_intelligence.views.LearningAnalyticsEngine'), \
                     patch('business_intelligence.views.RecommendationEngine'):
                    response = self.client.get(url)
            
            self.assertNotEqual(
                response.status_code, 
                status.HTTP_401_UNAUTHORIZED,
                f"Authenticated user should access {endpoint_name}"
            )
        
        # Test admin endpoints denied for regular user
        for endpoint_name in admin_endpoints:
            url = reverse(endpoint_name)
            query_params = {}
            
            if 'subscription-analysis' in endpoint_name:
                query_params['analysis_type'] = 'conversion-funnel'
            elif 'conversion-probability' in endpoint_name:
                query_params['user_id'] = str(self.user.id)
            
            response = self.client.get(url, query_params)
            
            self.assertEqual(
                response.status_code, 
                status.HTTP_403_FORBIDDEN,
                f"Regular user should be denied {endpoint_name}"
            )
        
        # Test admin endpoints allowed for admin user
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        for endpoint_name in admin_endpoints:
            url = reverse(endpoint_name)
            query_params = {}
            
            if 'subscription-analysis' in endpoint_name:
                query_params['analysis_type'] = 'conversion-funnel'
            elif 'conversion-probability' in endpoint_name:
                query_params['user_id'] = str(self.user.id)
            
            with patch('business_intelligence.views.BusinessMetricsEngine'), \
                 patch('business_intelligence.views.SubscriptionAnalyzer'):
                response = self.client.get(url, query_params)
            
            self.assertNotEqual(
                response.status_code, 
                status.HTTP_403_FORBIDDEN,
                f"Admin user should access {endpoint_name}"
            )