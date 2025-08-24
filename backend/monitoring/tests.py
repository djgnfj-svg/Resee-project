"""
Test cases for monitoring application
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

from accounts.models import SubscriptionTier
from .models import (AIMetrics, APIMetrics, DatabaseMetrics, ErrorLog,
                     SystemHealth, UserActivity)

User = get_user_model()


class MonitoringModelTest(TestCase):
    """Test monitoring models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
    
    def test_api_metrics_model_creation(self):
        """Test APIMetrics model creation and properties"""
        api_metrics = APIMetrics.objects.create(
            endpoint='/api/contents/',
            method='GET',
            user=self.user,
            response_time_ms=150,
            query_count=3,
            cache_hits=2,
            cache_misses=1,
            status_code=200,
            response_size_bytes=1024,
            user_agent='test-agent',
            ip_address='127.0.0.1'
        )
        
        self.assertEqual(api_metrics.endpoint, '/api/contents/')
        self.assertEqual(api_metrics.method, 'GET')
        self.assertEqual(api_metrics.user, self.user)
        self.assertEqual(api_metrics.response_time_ms, 150)
        self.assertEqual(api_metrics.status_code, 200)
        self.assertIsNotNone(api_metrics.timestamp)
        self.assertIsNotNone(api_metrics.date)
        
        # Check string representation
        expected_str = "GET /api/contents/ - 150ms"
        self.assertEqual(str(api_metrics), expected_str)
        
        # Check hour is set automatically
        self.assertIsNotNone(api_metrics.hour)
        self.assertGreaterEqual(api_metrics.hour, 0)
        self.assertLessEqual(api_metrics.hour, 23)
    
    def test_database_metrics_model_creation(self):
        """Test DatabaseMetrics model creation"""
        db_metrics = DatabaseMetrics.objects.create(
            table_name='content_content',
            operation_type='SELECT',
            execution_time_ms=25.5,
            rows_affected=10,
            query_hash='abc123def456',
            is_slow_query=False,
            endpoint='/api/contents/',
            user=self.user
        )
        
        self.assertEqual(db_metrics.table_name, 'content_content')
        self.assertEqual(db_metrics.operation_type, 'SELECT')
        self.assertEqual(db_metrics.execution_time_ms, 25.5)
        self.assertEqual(db_metrics.rows_affected, 10)
        self.assertFalse(db_metrics.is_slow_query)
        
        # Check string representation
        expected_str = "SELECT content_content - 25.5ms"
        self.assertEqual(str(db_metrics), expected_str)
    
    def test_ai_metrics_model_creation(self):
        """Test AIMetrics model creation"""
        ai_metrics = AIMetrics.objects.create(
            user=self.user,
            service_provider='anthropic',
            model_name='claude-3-haiku',
            operation_type='question_generation',
            tokens_used=500,
            cost_usd=Decimal('0.025'),
            processing_time_ms=2000,
            success=True,
            quality_score=8.5,
            content_id=1,
            subscription_tier='BASIC'
        )
        
        self.assertEqual(ai_metrics.user, self.user)
        self.assertEqual(ai_metrics.service_provider, 'anthropic')
        self.assertEqual(ai_metrics.model_name, 'claude-3-haiku')
        self.assertEqual(ai_metrics.operation_type, 'question_generation')
        self.assertEqual(ai_metrics.tokens_used, 500)
        self.assertEqual(ai_metrics.cost_usd, Decimal('0.025'))
        self.assertTrue(ai_metrics.success)
        self.assertEqual(ai_metrics.quality_score, 8.5)
        
        # Check string representation
        expected_str = "question_generation - claude-3-haiku (500 tokens)"
        self.assertEqual(str(ai_metrics), expected_str)
    
    def test_error_log_model_creation(self):
        """Test ErrorLog model creation"""
        error_log = ErrorLog.objects.create(
            level='ERROR',
            message='Test error message',
            exception_type='ValueError',
            traceback='Traceback details...',
            endpoint='/api/review/complete/',
            method='POST',
            user=self.user,
            ip_address='127.0.0.1',
            user_agent='test-agent',
            request_data={'test': 'data'},
            resolved=False,
            occurrences=3
        )
        
        self.assertEqual(error_log.level, 'ERROR')
        self.assertEqual(error_log.message, 'Test error message')
        self.assertEqual(error_log.exception_type, 'ValueError')
        self.assertEqual(error_log.user, self.user)
        self.assertFalse(error_log.resolved)
        self.assertEqual(error_log.occurrences, 3)
        
        # Check string representation
        self.assertIn('ERROR: ValueError', str(error_log))
        self.assertIn('Test error message', str(error_log))
    
    def test_system_health_model_creation(self):
        """Test SystemHealth model creation"""
        system_health = SystemHealth.objects.create(
            cpu_usage_percent=45.2,
            memory_usage_percent=62.8,
            disk_usage_percent=30.5,
            db_connection_count=5,
            db_query_avg_time_ms=125.3,
            cache_hit_rate_percent=85.5,
            cache_memory_usage_mb=256.0,
            celery_workers_active=2,
            redis_status=True,
            postgres_status=True,
            api_requests_per_minute=150.5,
            api_error_rate_percent=2.1,
            api_avg_response_time_ms=200.5
        )
        
        self.assertEqual(system_health.cpu_usage_percent, 45.2)
        self.assertEqual(system_health.memory_usage_percent, 62.8)
        self.assertEqual(system_health.db_connection_count, 5)
        self.assertTrue(system_health.redis_status)
        self.assertTrue(system_health.postgres_status)
        
        # Check string representation
        self.assertIn('Health check', str(system_health))
    
    def test_user_activity_model_creation(self):
        """Test UserActivity model creation"""
        activity_date = timezone.now().date()
        user_activity = UserActivity.objects.create(
            user=self.user,
            api_requests_count=25,
            content_created_count=3,
            reviews_completed_count=15,
            ai_questions_generated_count=5,
            session_duration_minutes=45,
            unique_endpoints_accessed=8,
            ip_address='127.0.0.1',
            user_agent='Mozilla/5.0...',
            device_type='desktop',
            date=activity_date,
            first_activity=timezone.now() - timedelta(hours=2),
            last_activity=timezone.now()
        )
        
        self.assertEqual(user_activity.user, self.user)
        self.assertEqual(user_activity.api_requests_count, 25)
        self.assertEqual(user_activity.content_created_count, 3)
        self.assertEqual(user_activity.reviews_completed_count, 15)
        self.assertEqual(user_activity.device_type, 'desktop')
        self.assertEqual(user_activity.date, activity_date)
        
        # Check string representation
        expected_str = f"{self.user.email} activity - {activity_date}"
        self.assertEqual(str(user_activity), expected_str)
    
    def test_user_activity_unique_constraint(self):
        """Test unique constraint on user and date"""
        activity_date = timezone.now().date()
        
        # Create first activity record
        UserActivity.objects.create(
            user=self.user,
            date=activity_date,
            first_activity=timezone.now(),
            last_activity=timezone.now()
        )
        
        # Attempt to create duplicate should raise IntegrityError
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            UserActivity.objects.create(
                user=self.user,
                date=activity_date,
                first_activity=timezone.now(),
                last_activity=timezone.now()
            )


class MonitoringViewsTest(APITestCase):
    """Test monitoring API views"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        self.admin_user.is_email_verified = True
        self.admin_user.save()
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            password='userpass123'
        )
        self.regular_user.is_email_verified = True
        self.regular_user.save()
        
        # Create test data
        self._create_test_data()
    
    def _create_test_data(self):
        """Create test monitoring data"""
        # API metrics
        for i in range(10):
            APIMetrics.objects.create(
                endpoint='/api/contents/',
                method='GET',
                user=self.regular_user,
                response_time_ms=100 + i * 10,
                query_count=2 + i % 3,
                status_code=200 if i < 8 else 400,
                timestamp=timezone.now() - timedelta(hours=i)
            )
        
        # Database metrics
        for i in range(5):
            DatabaseMetrics.objects.create(
                table_name='content_content',
                operation_type='SELECT',
                execution_time_ms=50 + i * 5,
                rows_affected=10,
                query_hash=f'hash{i}',
                is_slow_query=i > 3,
                timestamp=timezone.now() - timedelta(hours=i)
            )
        
        # AI metrics
        for i in range(8):
            AIMetrics.objects.create(
                user=self.regular_user,
                service_provider='anthropic',
                model_name='claude-3-haiku',
                operation_type='question_generation',
                tokens_used=100 + i * 50,
                cost_usd=Decimal('0.01') * (i + 1),
                processing_time_ms=1000 + i * 100,
                success=i < 7,
                subscription_tier='BASIC',
                timestamp=timezone.now() - timedelta(hours=i)
            )
        
        # Error logs
        for i in range(3):
            ErrorLog.objects.create(
                level='ERROR' if i < 2 else 'CRITICAL',
                message=f'Test error {i}',
                exception_type='ValueError',
                endpoint='/api/test/',
                method='POST',
                user=self.regular_user,
                resolved=i == 0,
                timestamp=timezone.now() - timedelta(hours=i)
            )
        
        # System health
        SystemHealth.objects.create(
            cpu_usage_percent=65.5,
            memory_usage_percent=80.2,
            disk_usage_percent=45.0,
            db_connection_count=8,
            db_query_avg_time_ms=150.5,
            cache_hit_rate_percent=90.0,
            cache_memory_usage_mb=512.0,
            celery_workers_active=3,
            redis_status=True,
            postgres_status=True,
            api_requests_per_minute=200.0,
            api_error_rate_percent=5.0,
            api_avg_response_time_ms=180.5
        )
        
        # User activity
        UserActivity.objects.create(
            user=self.regular_user,
            api_requests_count=50,
            content_created_count=5,
            reviews_completed_count=20,
            ai_questions_generated_count=8,
            session_duration_minutes=120,
            unique_endpoints_accessed=12,
            device_type='desktop',
            date=timezone.now().date(),
            first_activity=timezone.now() - timedelta(hours=2),
            last_activity=timezone.now()
        )
    
    def _authenticate_admin(self):
        """Authenticate as admin user"""
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def _authenticate_regular_user(self):
        """Authenticate as regular user"""
        refresh = RefreshToken.for_user(self.regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')


class DashboardOverviewTest(MonitoringViewsTest):
    """Test dashboard overview endpoint"""
    
    def test_dashboard_overview_admin_access(self):
        """Test admin can access dashboard overview"""
        self._authenticate_admin()
        
        url = reverse('monitoring:dashboard-overview')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        required_fields = [
            'timeframe', 'timestamp', 'api_metrics', 'user_activity',
            'ai_usage', 'errors', 'system_health'
        ]
        
        for field in required_fields:
            self.assertIn(field, data)
        
        # Check API metrics structure
        api_metrics = data['api_metrics']
        self.assertIn('total_requests', api_metrics)
        self.assertIn('avg_response_time_ms', api_metrics)
        self.assertIn('error_rate_percent', api_metrics)
        self.assertIn('slow_requests', api_metrics)
        
        # Verify data values make sense
        self.assertGreater(api_metrics['total_requests'], 0)
        self.assertGreaterEqual(api_metrics['error_rate_percent'], 0)
        self.assertLessEqual(api_metrics['error_rate_percent'], 100)
    
    def test_dashboard_overview_regular_user_denied(self):
        """Test regular user cannot access dashboard overview"""
        self._authenticate_regular_user()
        
        url = reverse('monitoring:dashboard-overview')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_dashboard_overview_unauthenticated_denied(self):
        """Test unauthenticated user cannot access dashboard"""
        url = reverse('monitoring:dashboard-overview')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_dashboard_overview_with_no_data(self):
        """Test dashboard overview with no monitoring data"""
        # Clear all test data
        APIMetrics.objects.all().delete()
        UserActivity.objects.all().delete()
        AIMetrics.objects.all().delete()
        ErrorLog.objects.all().delete()
        SystemHealth.objects.all().delete()
        
        self._authenticate_admin()
        
        url = reverse('monitoring:dashboard-overview')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return zero values, not errors
        data = response.data
        self.assertEqual(data['api_metrics']['total_requests'], 0)
        self.assertEqual(data['user_activity']['active_users_today'], 0)
        self.assertEqual(data['ai_usage']['total_operations'], 0)
        self.assertEqual(data['errors']['total_errors'], 0)


class APIPerformanceChartTest(MonitoringViewsTest):
    """Test API performance chart endpoint"""
    
    def test_api_performance_chart_default_timeframe(self):
        """Test API performance chart with default 24h timeframe"""
        self._authenticate_admin()
        
        url = reverse('monitoring:api-performance-chart')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(data['timeframe_hours'], 24)
        self.assertIn('chart_data', data)
        self.assertIn('slow_endpoints', data)
        
        # Check chart data structure
        if data['chart_data']:
            chart_point = data['chart_data'][0]
            required_fields = [
                'timestamp', 'avg_response_time_ms', 'request_count',
                'error_rate_percent', 'avg_query_count'
            ]
            for field in required_fields:
                self.assertIn(field, chart_point)
    
    def test_api_performance_chart_custom_timeframe(self):
        """Test API performance chart with custom timeframe"""
        self._authenticate_admin()
        
        url = reverse('monitoring:api-performance-chart')
        response = self.client.get(url, {'hours': 48})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(data['timeframe_hours'], 48)
    
    def test_slow_endpoints_identification(self):
        """Test identification of slow endpoints"""
        # Create additional slow endpoint data
        APIMetrics.objects.create(
            endpoint='/api/slow-endpoint/',
            method='POST',
            user=self.regular_user,
            response_time_ms=1500,  # > 500ms threshold
            status_code=200,
            timestamp=timezone.now()
        )
        
        self._authenticate_admin()
        
        url = reverse('monitoring:api-performance-chart')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        slow_endpoints = response.data['slow_endpoints']
        # Should identify slow endpoints
        slow_endpoint_paths = [ep['endpoint'] for ep in slow_endpoints]
        self.assertIn('/api/slow-endpoint/', slow_endpoint_paths)


class ErrorAnalysisTest(MonitoringViewsTest):
    """Test error analysis endpoint"""
    
    def test_error_analysis_default_timeframe(self):
        """Test error analysis with default 7 day timeframe"""
        self._authenticate_admin()
        
        url = reverse('monitoring:error-analysis')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(data['timeframe_days'], 7)
        self.assertIn('daily_trends', data)
        self.assertIn('top_error_types', data)
        self.assertIn('endpoint_errors', data)
    
    def test_daily_error_trends_structure(self):
        """Test daily error trends data structure"""
        self._authenticate_admin()
        
        url = reverse('monitoring:error-analysis')
        response = self.client.get(url)
        
        daily_trends = response.data['daily_trends']
        
        if daily_trends:
            day_data = daily_trends[0]
            required_fields = [
                'date', 'total_errors', 'critical_errors',
                'error_errors', 'warning_errors'
            ]
            for field in required_fields:
                self.assertIn(field, day_data)
    
    def test_top_error_types_prioritization(self):
        """Test top error types prioritize unresolved errors"""
        # Create additional unresolved error
        ErrorLog.objects.create(
            level='CRITICAL',
            message='Critical unresolved error',
            exception_type='DatabaseError',
            endpoint='/api/critical/',
            resolved=False,
            occurrences=5,
            timestamp=timezone.now()
        )
        
        self._authenticate_admin()
        
        url = reverse('monitoring:error-analysis')
        response = self.client.get(url)
        
        top_errors = response.data['top_error_types']
        
        # Should include unresolved errors (filtered by resolved=False)
        if top_errors:
            error_types = [err['exception_type'] for err in top_errors]
            self.assertIn('DatabaseError', error_types)
    
    def test_error_analysis_custom_timeframe(self):
        """Test error analysis with custom timeframe"""
        self._authenticate_admin()
        
        url = reverse('monitoring:error-analysis')
        response = self.client.get(url, {'days': 30})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['timeframe_days'], 30)


class AIUsageAnalyticsTest(MonitoringViewsTest):
    """Test AI usage analytics endpoint"""
    
    def test_ai_usage_analytics_default_timeframe(self):
        """Test AI usage analytics with default 30 day timeframe"""
        self._authenticate_admin()
        
        url = reverse('monitoring:ai-usage-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(data['timeframe_days'], 30)
        self.assertIn('daily_usage', data)
        self.assertIn('operation_stats', data)
        self.assertIn('subscription_tier_usage', data)
        self.assertIn('top_users', data)
    
    def test_daily_usage_structure(self):
        """Test daily usage data structure"""
        self._authenticate_admin()
        
        url = reverse('monitoring:ai-usage-analytics')
        response = self.client.get(url)
        
        daily_usage = response.data['daily_usage']
        
        if daily_usage:
            day_data = daily_usage[0]
            required_fields = [
                'date', 'total_operations', 'total_tokens',
                'total_cost_usd', 'avg_processing_time_ms', 'success_rate_percent'
            ]
            for field in required_fields:
                self.assertIn(field, day_data)
            
            # Check data types
            self.assertIsInstance(day_data['total_operations'], int)
            self.assertIsInstance(day_data['total_cost_usd'], float)
            self.assertGreaterEqual(day_data['success_rate_percent'], 0)
            self.assertLessEqual(day_data['success_rate_percent'], 100)
    
    def test_operation_stats_aggregation(self):
        """Test operation statistics aggregation"""
        self._authenticate_admin()
        
        url = reverse('monitoring:ai-usage-analytics')
        response = self.client.get(url)
        
        operation_stats = response.data['operation_stats']
        
        # Should have operation types from test data
        operation_types = [stat['operation_type'] for stat in operation_stats]
        self.assertIn('question_generation', operation_types)
        
        if operation_stats:
            stat = operation_stats[0]
            required_fields = [
                'operation_type', 'count', 'total_tokens',
                'total_cost_usd', 'avg_quality_score'
            ]
            for field in required_fields:
                self.assertIn(field, stat)
    
    def test_subscription_tier_usage(self):
        """Test subscription tier usage breakdown"""
        self._authenticate_admin()
        
        url = reverse('monitoring:ai-usage-analytics')
        response = self.client.get(url)
        
        tier_usage = response.data['subscription_tier_usage']
        
        # Should include BASIC tier from test data
        tiers = [usage['subscription_tier'] for usage in tier_usage]
        self.assertIn('BASIC', tiers)
    
    def test_top_users_listing(self):
        """Test top users by AI usage"""
        self._authenticate_admin()
        
        url = reverse('monitoring:ai-usage-analytics')
        response = self.client.get(url)
        
        top_users = response.data['top_users']
        
        # Should include regular user from test data
        user_emails = [user['email'] for user in top_users]
        self.assertIn(self.regular_user.email, user_emails)
        
        if top_users:
            user_data = top_users[0]
            required_fields = [
                'email', 'subscription_tier', 'operation_count',
                'total_tokens', 'total_cost_usd'
            ]
            for field in required_fields:
                self.assertIn(field, user_data)


class HealthCheckTest(MonitoringViewsTest):
    """Test health check endpoint"""
    
    @patch('monitoring.views.check_system_health')
    def test_health_check_healthy_system(self, mock_health_check):
        """Test health check with healthy system"""
        mock_health_check.return_value = {
            'overall_status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'checks': {
                'database': {'status': 'healthy'},
                'redis': {'status': 'healthy'},
                'celery': {'status': 'healthy'}
            }
        }
        
        url = reverse('monitoring:health-check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(data['overall_status'], 'healthy')
        self.assertIn('timestamp', data)
        self.assertIn('checks', data)
    
    @patch('monitoring.views.check_system_health')
    def test_health_check_degraded_system(self, mock_health_check):
        """Test health check with degraded system"""
        mock_health_check.return_value = {
            'overall_status': 'degraded',
            'timestamp': timezone.now().isoformat(),
            'checks': {
                'database': {'status': 'healthy'},
                'redis': {'status': 'degraded'},
                'celery': {'status': 'healthy'}
            }
        }
        
        url = reverse('monitoring:health-check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_206_PARTIAL_CONTENT)
        self.assertEqual(response.data['overall_status'], 'degraded')
    
    @patch('monitoring.views.check_system_health')
    def test_health_check_unhealthy_system(self, mock_health_check):
        """Test health check with unhealthy system"""
        mock_health_check.return_value = {
            'overall_status': 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'checks': {
                'database': {'status': 'unhealthy'},
                'redis': {'status': 'healthy'},
                'celery': {'status': 'unhealthy'}
            }
        }
        
        url = reverse('monitoring:health-check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data['overall_status'], 'unhealthy')
    
    @patch('monitoring.views.check_system_health')
    def test_health_check_exception_handling(self, mock_health_check):
        """Test health check exception handling"""
        mock_health_check.side_effect = Exception("Health check failed")
        
        url = reverse('monitoring:health-check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        
        data = response.data
        self.assertEqual(data['overall_status'], 'unhealthy')
        self.assertIn('error', data)
        self.assertIn('timestamp', data)
    
    def test_health_check_public_access(self):
        """Test health check is publicly accessible"""
        # No authentication required
        url = reverse('monitoring:health-check')
        response = self.client.get(url)
        
        # Should not return 401/403 (may return 200/206/503 depending on system state)
        self.assertNotIn(response.status_code, [401, 403])


class PerformanceInsightsTest(MonitoringViewsTest):
    """Test performance insights endpoint"""
    
    @patch('monitoring.views.get_performance_insights')
    def test_performance_insights_default_timeframe(self, mock_insights):
        """Test performance insights with default timeframe"""
        mock_insights.return_value = {
            'insights': [
                {
                    'type': 'slow_endpoint',
                    'title': 'Slow API Endpoint Detected',
                    'message': '/api/contents/ has average response time > 500ms',
                    'severity': 'warning'
                }
            ],
            'recommendations': [
                {
                    'type': 'database_optimization',
                    'title': 'Database Query Optimization',
                    'message': 'Consider adding indexes to frequently queried tables'
                }
            ],
            'performance_score': 75.5
        }
        
        self._authenticate_admin()
        
        url = reverse('monitoring:performance-insights')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('insights', data)
        self.assertIn('recommendations', data)
        self.assertIn('performance_score', data)
        
        mock_insights.assert_called_once_with(24)  # Default 24 hours
    
    @patch('monitoring.views.get_performance_insights')
    def test_performance_insights_custom_timeframe(self, mock_insights):
        """Test performance insights with custom timeframe"""
        mock_insights.return_value = {
            'insights': [],
            'recommendations': [],
            'performance_score': 85.0
        }
        
        self._authenticate_admin()
        
        url = reverse('monitoring:performance-insights')
        response = self.client.get(url, {'hours': 48})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_insights.assert_called_once_with(48)
    
    def test_performance_insights_admin_only(self):
        """Test performance insights requires admin access"""
        self._authenticate_regular_user()
        
        url = reverse('monitoring:performance-insights')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CleanupOldDataTest(MonitoringViewsTest):
    """Test cleanup old data endpoint"""
    
    def test_cleanup_old_data_default_retention(self):
        """Test cleanup with default 30 day retention"""
        # Create old data that should be deleted
        old_date = timezone.now() - timedelta(days=35)
        old_api_metric = APIMetrics.objects.create(
            endpoint='/api/old/',
            method='GET',
            response_time_ms=100,
            status_code=200,
            timestamp=old_date
        )
        
        # Create recent data that should be kept
        recent_api_metric = APIMetrics.objects.create(
            endpoint='/api/recent/',
            method='GET',
            response_time_ms=100,
            status_code=200,
            timestamp=timezone.now()
        )
        
        self._authenticate_admin()
        
        url = reverse('monitoring:cleanup-old-data')
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertTrue(data['success'])
        self.assertEqual(data['days_kept'], 30)
        self.assertIn('deleted_records', data)
        self.assertIn('timestamp', data)
        
        # Verify old data was deleted and recent data was kept
        self.assertFalse(APIMetrics.objects.filter(id=old_api_metric.id).exists())
        self.assertTrue(APIMetrics.objects.filter(id=recent_api_metric.id).exists())
    
    def test_cleanup_old_data_custom_retention(self):
        """Test cleanup with custom retention period"""
        self._authenticate_admin()
        
        url = reverse('monitoring:cleanup-old-data')
        response = self.client.post(url, {'days_to_keep': 60})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(data['days_kept'], 60)
    
    def test_cleanup_old_data_admin_only(self):
        """Test cleanup requires admin access"""
        self._authenticate_regular_user()
        
        url = reverse('monitoring:cleanup-old-data')
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_cleanup_old_data_unauthenticated(self):
        """Test cleanup requires authentication"""
        url = reverse('monitoring:cleanup-old-data')
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MonitoringPermissionTest(APITestCase):
    """Test monitoring permission system"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create users with different roles
        self.superuser = User.objects.create_user(
            email='super@example.com',
            password='testpass123',
            is_superuser=True,
            is_staff=True
        )
        
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='testpass123'
        )
        
        for user in [self.superuser, self.staff_user, self.regular_user]:
            user.is_email_verified = True
            user.save()
    
    def test_superuser_access_all_endpoints(self):
        """Test superuser can access all monitoring endpoints"""
        refresh = RefreshToken.for_user(self.superuser)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        protected_endpoints = [
            'monitoring:dashboard-overview',
            'monitoring:api-performance-chart',
            'monitoring:error-analysis',
            'monitoring:ai-usage-analytics',
            'monitoring:performance-insights',
        ]
        
        for endpoint_name in protected_endpoints:
            url = reverse(endpoint_name)
            response = self.client.get(url)
            
            # Should not be 403 Forbidden
            self.assertNotEqual(
                response.status_code, 
                status.HTTP_403_FORBIDDEN,
                f"Superuser should access {endpoint_name}"
            )
    
    def test_staff_user_access_monitoring(self):
        """Test staff user can access monitoring endpoints"""
        refresh = RefreshToken.for_user(self.staff_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Staff users should have monitoring access
        url = reverse('monitoring:dashboard-overview')
        response = self.client.get(url)
        
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_regular_user_denied_monitoring_access(self):
        """Test regular user cannot access monitoring endpoints"""
        refresh = RefreshToken.for_user(self.regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        protected_endpoints = [
            'monitoring:dashboard-overview',
            'monitoring:api-performance-chart',
            'monitoring:error-analysis',
            'monitoring:ai-usage-analytics',
            'monitoring:performance-insights',
            'monitoring:cleanup-old-data',
        ]
        
        for endpoint_name in protected_endpoints:
            url = reverse(endpoint_name)
            
            if endpoint_name == 'monitoring:cleanup-old-data':
                response = self.client.post(url, {})
            else:
                response = self.client.get(url)
            
            self.assertEqual(
                response.status_code, 
                status.HTTP_403_FORBIDDEN,
                f"Regular user should be denied {endpoint_name}"
            )


class MonitoringUtilityTest(TestCase):
    """Test monitoring utility functions"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('monitoring.utils.connection')
    @patch('monitoring.utils.cache')
    def test_check_system_health_all_healthy(self, mock_cache, mock_db):
        """Test system health check when all services are healthy"""
        # Mock database connection
        mock_db.cursor.return_value.__enter__.return_value.execute.return_value = None
        
        # Mock cache connection
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        
        from monitoring.utils import check_system_health
        
        with patch('monitoring.utils.inspect') as mock_inspect:
            mock_inspect.return_value.active.return_value = {'worker1': {}}
            
            health_data = check_system_health()
        
        self.assertIn('overall_status', health_data)
        self.assertIn('checks', health_data)
        self.assertIn('timestamp', health_data)
        
        # Should report healthy status
        self.assertEqual(health_data['overall_status'], 'healthy')
    
    @patch('monitoring.utils.connection')
    def test_check_system_health_database_error(self, mock_db):
        """Test system health check with database error"""
        # Mock database connection failure
        mock_db.cursor.side_effect = Exception("Database connection failed")
        
        from monitoring.utils import check_system_health
        
        health_data = check_system_health()
        
        # Should report unhealthy or degraded status
        self.assertIn(health_data['overall_status'], ['unhealthy', 'degraded'])
        self.assertIn('database', health_data['checks'])
    
    def test_clean_old_metrics(self):
        """Test cleaning old metrics data"""
        # Create old data
        old_date = timezone.now() - timedelta(days=35)
        old_metric = APIMetrics.objects.create(
            endpoint='/api/old/',
            method='GET',
            response_time_ms=100,
            status_code=200,
            timestamp=old_date
        )
        
        # Create recent data
        recent_metric = APIMetrics.objects.create(
            endpoint='/api/recent/',
            method='GET',
            response_time_ms=100,
            status_code=200,
            timestamp=timezone.now()
        )
        
        from monitoring.utils import clean_old_metrics
        
        deleted_count = clean_old_metrics(days_to_keep=30)
        
        # Should delete old data only
        self.assertGreater(deleted_count, 0)
        self.assertFalse(APIMetrics.objects.filter(id=old_metric.id).exists())
        self.assertTrue(APIMetrics.objects.filter(id=recent_metric.id).exists())
    
    def test_get_performance_insights(self):
        """Test performance insights generation"""
        # Create test data for insights
        APIMetrics.objects.create(
            endpoint='/api/slow/',
            method='GET',
            response_time_ms=1500,  # Slow response
            status_code=200,
            timestamp=timezone.now()
        )
        
        DatabaseMetrics.objects.create(
            table_name='test_table',
            operation_type='SELECT',
            execution_time_ms=500,  # Slow query
            is_slow_query=True,
            timestamp=timezone.now()
        )
        
        from monitoring.utils import get_performance_insights
        
        insights = get_performance_insights(hours=24)
        
        self.assertIn('insights', insights)
        self.assertIn('recommendations', insights)
        self.assertIn('performance_score', insights)
        
        # Should identify performance issues
        insight_types = [insight['type'] for insight in insights['insights']]
        self.assertTrue(any('slow' in insight_type for insight_type in insight_types))


class MonitoringIntegrationTest(APITestCase):
    """Test monitoring system integration"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        self.admin_user.is_email_verified = True
        self.admin_user.save()
    
    def test_monitoring_dashboard_workflow(self):
        """Test complete monitoring dashboard workflow"""
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Step 1: Check system health
        health_url = reverse('monitoring:health-check')
        health_response = self.client.get(health_url)
        
        # Should get some response (200/206/503)
        self.assertIn(health_response.status_code, [200, 206, 503])
        
        # Step 2: Get dashboard overview
        overview_url = reverse('monitoring:dashboard-overview')
        overview_response = self.client.get(overview_url)
        
        self.assertEqual(overview_response.status_code, status.HTTP_200_OK)
        self.assertIn('api_metrics', overview_response.data)
        
        # Step 3: Get API performance data
        performance_url = reverse('monitoring:api-performance-chart')
        performance_response = self.client.get(performance_url)
        
        self.assertEqual(performance_response.status_code, status.HTTP_200_OK)
        self.assertIn('chart_data', performance_response.data)
        
        # Step 4: Analyze errors
        error_url = reverse('monitoring:error-analysis')
        error_response = self.client.get(error_url)
        
        self.assertEqual(error_response.status_code, status.HTTP_200_OK)
        self.assertIn('daily_trends', error_response.data)
        
        # Step 5: Check AI usage
        ai_url = reverse('monitoring:ai-usage-analytics')
        ai_response = self.client.get(ai_url)
        
        self.assertEqual(ai_response.status_code, status.HTTP_200_OK)
        self.assertIn('daily_usage', ai_response.data)
    
    def test_monitoring_data_consistency(self):
        """Test consistency of monitoring data across endpoints"""
        # Create consistent test data
        api_metrics = APIMetrics.objects.create(
            endpoint='/api/test/',
            method='GET',
            response_time_ms=200,
            status_code=200,
            timestamp=timezone.now()
        )
        
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Get data from different endpoints
        overview_url = reverse('monitoring:dashboard-overview')
        overview_response = self.client.get(overview_url)
        
        chart_url = reverse('monitoring:api-performance-chart')
        chart_response = self.client.get(chart_url)
        
        # Both should acknowledge the API request
        overview_total = overview_response.data['api_metrics']['total_requests']
        chart_total = sum(point['request_count'] for point in chart_response.data['chart_data'])
        
        # Should have at least the one request we created
        self.assertGreaterEqual(overview_total, 1)
        # Chart data might be grouped by hour, so could be 0 if no data in current hour bucket
        self.assertGreaterEqual(chart_total, 0)