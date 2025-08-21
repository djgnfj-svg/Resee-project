"""
Metric collection service for alert system
"""
import logging
from datetime import timedelta
from django.db.models import Avg, Count, Sum, Max
from django.utils import timezone
from django.core.cache import cache

from monitoring.models import (
    APIMetrics, SystemHealth, ErrorLog, 
    AIMetrics, UserActivity, DatabaseMetrics
)

logger = logging.getLogger(__name__)


class MetricCollector:
    """
    Collect metrics from monitoring system for alert evaluation
    """
    
    def __init__(self):
        self.cache_timeout = 60  # 1 minute cache
    
    def get_metric_value(self, metric_name: str, time_window_minutes: int) -> float:
        """
        Get current metric value for the specified time window
        
        Args:
            metric_name: Name of the metric to collect
            time_window_minutes: Time window in minutes
            
        Returns:
            Current metric value
        """
        cache_key = f'metric_{metric_name}_{time_window_minutes}'
        cached_value = cache.get(cache_key)
        
        if cached_value is not None:
            return cached_value
        
        try:
            value = self._collect_metric(metric_name, time_window_minutes)
            cache.set(cache_key, value, self.cache_timeout)
            return value
        except Exception as e:
            logger.error(f"Error collecting metric {metric_name}: {e}")
            return 0.0
    
    def _collect_metric(self, metric_name: str, time_window_minutes: int) -> float:
        """Internal method to collect specific metrics"""
        end_time = timezone.now()
        start_time = end_time - timedelta(minutes=time_window_minutes)
        
        # System metrics
        if metric_name == 'cpu_usage':
            return self._get_system_metric('cpu_usage_percent', start_time, end_time)
        
        elif metric_name == 'memory_usage':
            return self._get_system_metric('memory_usage_percent', start_time, end_time)
        
        elif metric_name == 'disk_usage':
            return self._get_system_metric('disk_usage_percent', start_time, end_time)
        
        # API metrics
        elif metric_name == 'api_response_time':
            return self._get_api_response_time(start_time, end_time)
        
        elif metric_name == 'api_error_rate':
            return self._get_api_error_rate(start_time, end_time)
        
        elif metric_name == 'api_request_count':
            return self._get_api_request_count(start_time, end_time)
        
        # Database metrics
        elif metric_name == 'db_connection_count':
            return self._get_db_connection_count(start_time, end_time)
        
        elif metric_name == 'db_query_time':
            return self._get_db_query_time(start_time, end_time)
        
        elif metric_name == 'slow_query_count':
            return self._get_slow_query_count(start_time, end_time)
        
        # Error metrics
        elif metric_name == 'error_count':
            return self._get_error_count(start_time, end_time)
        
        elif metric_name == 'critical_error_count':
            return self._get_critical_error_count(start_time, end_time)
        
        # AI metrics
        elif metric_name == 'ai_cost_daily':
            return self._get_ai_daily_cost(start_time, end_time)
        
        elif metric_name == 'ai_token_usage':
            return self._get_ai_token_usage(start_time, end_time)
        
        elif metric_name == 'ai_failure_rate':
            return self._get_ai_failure_rate(start_time, end_time)
        
        # Business metrics
        elif metric_name == 'active_user_count':
            return self._get_active_user_count(start_time, end_time)
        
        elif metric_name == 'signup_count':
            return self._get_signup_count(start_time, end_time)
        
        elif metric_name == 'subscription_count':
            return self._get_subscription_count(start_time, end_time)
        
        else:
            logger.warning(f"Unknown metric: {metric_name}")
            return 0.0
    
    def _get_system_metric(self, field_name: str, start_time, end_time) -> float:
        """Get system metric average value"""
        result = SystemHealth.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).aggregate(avg_value=Avg(field_name))
        
        return result['avg_value'] or 0.0
    
    def _get_api_response_time(self, start_time, end_time) -> float:
        """Get average API response time in milliseconds"""
        result = APIMetrics.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).aggregate(avg_time=Avg('response_time_ms'))
        
        return result['avg_time'] or 0.0
    
    def _get_api_error_rate(self, start_time, end_time) -> float:
        """Get API error rate percentage"""
        total_requests = APIMetrics.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).count()
        
        if total_requests == 0:
            return 0.0
        
        error_requests = APIMetrics.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time,
            status_code__gte=400
        ).count()
        
        return (error_requests / total_requests) * 100
    
    def _get_api_request_count(self, start_time, end_time) -> float:
        """Get total API request count"""
        return APIMetrics.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).count()
    
    def _get_db_connection_count(self, start_time, end_time) -> float:
        """Get average database connection count"""
        result = SystemHealth.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).aggregate(avg_conn=Avg('db_connection_count'))
        
        return result['avg_conn'] or 0.0
    
    def _get_db_query_time(self, start_time, end_time) -> float:
        """Get average database query time"""
        result = DatabaseMetrics.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).aggregate(avg_time=Avg('execution_time_ms'))
        
        return result['avg_time'] or 0.0
    
    def _get_slow_query_count(self, start_time, end_time) -> float:
        """Get count of slow database queries"""
        return DatabaseMetrics.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time,
            is_slow_query=True
        ).count()
    
    def _get_error_count(self, start_time, end_time) -> float:
        """Get total error count"""
        return ErrorLog.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).count()
    
    def _get_critical_error_count(self, start_time, end_time) -> float:
        """Get critical error count"""
        return ErrorLog.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time,
            level='CRITICAL'
        ).count()
    
    def _get_ai_daily_cost(self, start_time, end_time) -> float:
        """Get daily AI cost in USD"""
        result = AIMetrics.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).aggregate(total_cost=Sum('cost_usd'))
        
        return float(result['total_cost'] or 0.0)
    
    def _get_ai_token_usage(self, start_time, end_time) -> float:
        """Get AI token usage count"""
        result = AIMetrics.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).aggregate(total_tokens=Sum('tokens_used'))
        
        return result['total_tokens'] or 0.0
    
    def _get_ai_failure_rate(self, start_time, end_time) -> float:
        """Get AI failure rate percentage"""
        total_requests = AIMetrics.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).count()
        
        if total_requests == 0:
            return 0.0
        
        failed_requests = AIMetrics.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time,
            success=False
        ).count()
        
        return (failed_requests / total_requests) * 100
    
    def _get_active_user_count(self, start_time, end_time) -> float:
        """Get count of active users"""
        date_start = start_time.date()
        date_end = end_time.date()
        
        return UserActivity.objects.filter(
            date__gte=date_start,
            date__lte=date_end
        ).values('user').distinct().count()
    
    def _get_signup_count(self, start_time, end_time) -> float:
        """Get signup count (approximation from user activity)"""
        from accounts.models import User
        
        return User.objects.filter(
            date_joined__gte=start_time,
            date_joined__lte=end_time
        ).count()
    
    def _get_subscription_count(self, start_time, end_time) -> float:
        """Get subscription count (approximation from payment activity)"""
        # This would need to be connected to the payments app
        # For now, return 0
        return 0.0