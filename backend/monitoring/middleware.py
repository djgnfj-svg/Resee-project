"""
Middleware for collecting performance metrics and monitoring data
"""
import time
import logging
from django.utils import timezone
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from .models import APIMetrics, UserActivity
from .utils import get_client_ip, get_device_type, should_track_request
import uuid

logger = logging.getLogger('monitoring')


class MetricsCollectionMiddleware:
    """
    Middleware to collect API performance metrics and user activity
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip tracking for certain requests (static files, admin, etc.)
        if not should_track_request(request):
            return self.get_response(request)
        
        # Record start time and query count
        start_time = time.time()
        initial_queries = len(connection.queries) if settings.DEBUG else 0
        
        # Generate request ID for correlation
        request_id = str(uuid.uuid4())
        request.monitoring_request_id = request_id
        
        # Process request
        response = self.get_response(request)
        
        # Calculate metrics
        end_time = time.time()
        response_time_ms = int((end_time - start_time) * 1000)
        query_count = len(connection.queries) - initial_queries if settings.DEBUG else 0
        
        # Collect metrics asynchronously to avoid impacting response time
        try:
            self._record_api_metrics(request, response, response_time_ms, query_count, request_id)
            self._update_user_activity(request, response_time_ms)
        except Exception as e:
            logger.error(f"Failed to record metrics: {e}", exc_info=True)
        
        # Add performance headers for debugging
        if settings.DEBUG:
            response['X-Response-Time'] = f"{response_time_ms}ms"
            response['X-Query-Count'] = str(query_count)
            response['X-Request-ID'] = request_id
        
        return response
    
    def _record_api_metrics(self, request, response, response_time_ms, query_count, request_id):
        """Record API performance metrics"""
        user = getattr(request, 'user', None)
        if user and not user.is_authenticated:
            user = None
        
        # Use bulk_create for better performance in high-traffic scenarios
        metrics_data = {
            'endpoint': request.path,
            'method': request.method,
            'user': user,
            'response_time_ms': response_time_ms,
            'query_count': query_count,
            'status_code': response.status_code,
            'response_size_bytes': len(response.content) if hasattr(response, 'content') else 0,
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],  # Limit length
            'ip_address': get_client_ip(request),
            'request_id': request_id,
            'timestamp': timezone.now(),
            'date': timezone.now().date(),
            'hour': timezone.now().hour,
        }
        
        # Cache metrics for batch insertion (performance optimization)
        cache_key = f"api_metrics_batch_{timezone.now().strftime('%Y%m%d_%H')}"
        cached_metrics = cache.get(cache_key, [])
        cached_metrics.append(metrics_data)
        cache.set(cache_key, cached_metrics, timeout=3600)  # 1 hour
        
        # If batch is large enough, trigger batch insert
        if len(cached_metrics) >= 100:
            self._flush_metrics_batch(cache_key, cached_metrics)
    
    def _flush_metrics_batch(self, cache_key, metrics_batch):
        """Flush batch of metrics to database"""
        try:
            metrics_objects = [APIMetrics(**data) for data in metrics_batch]
            APIMetrics.objects.bulk_create(metrics_objects, batch_size=100)
            cache.delete(cache_key)
            logger.info(f"Flushed {len(metrics_batch)} API metrics to database")
        except Exception as e:
            logger.error(f"Failed to flush metrics batch: {e}")
    
    def _update_user_activity(self, request, response_time_ms):
        """Update daily user activity tracking"""
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return
        
        today = timezone.now().date()
        now = timezone.now()
        
        # Use get_or_create with update to handle concurrent requests
        activity, created = UserActivity.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                'api_requests_count': 1,
                'device_type': get_device_type(request.META.get('HTTP_USER_AGENT', '')),
                'ip_address': get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                'first_activity': now,
                'last_activity': now,
            }
        )
        
        if not created:
            # Update existing activity record
            activity.api_requests_count += 1
            activity.last_activity = now
            activity.save(update_fields=['api_requests_count', 'last_activity'])


class PerformanceMonitoringMiddleware:
    """
    Middleware for advanced performance monitoring and alerting
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Performance thresholds
        self.slow_request_threshold_ms = getattr(settings, 'SLOW_REQUEST_THRESHOLD_MS', 1000)
        self.high_query_count_threshold = getattr(settings, 'HIGH_QUERY_COUNT_THRESHOLD', 20)
        
    def __call__(self, request):
        start_time = time.time()
        initial_queries = len(connection.queries) if settings.DEBUG else 0
        
        response = self.get_response(request)
        
        # Calculate performance metrics
        response_time_ms = (time.time() - start_time) * 1000
        query_count = len(connection.queries) - initial_queries if settings.DEBUG else 0
        
        # Check for performance issues
        self._check_performance_issues(request, response_time_ms, query_count)
        
        return response
    
    def _check_performance_issues(self, request, response_time_ms, query_count):
        """Check for performance issues and log warnings"""
        endpoint = f"{request.method} {request.path}"
        
        # Check for slow requests
        if response_time_ms > self.slow_request_threshold_ms:
            logger.warning(
                f"Slow request detected: {endpoint}",
                extra={
                    'event_type': 'slow_request',
                    'endpoint': request.path,
                    'method': request.method,
                    'response_time_ms': response_time_ms,
                    'threshold_ms': self.slow_request_threshold_ms,
                    'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                }
            )
        
        # Check for high query count (N+1 problem indicator)
        if query_count > self.high_query_count_threshold:
            logger.warning(
                f"High query count detected: {endpoint}",
                extra={
                    'event_type': 'high_query_count',
                    'endpoint': request.path,
                    'method': request.method,
                    'query_count': query_count,
                    'threshold': self.high_query_count_threshold,
                    'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                }
            )


class DatabaseQueryTrackingMiddleware:
    """
    Middleware to track database query performance
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        if not settings.DEBUG:
            return self.get_response(request)
        
        # Reset queries and start tracking
        from django.db import reset_queries
        reset_queries()
        
        response = self.get_response(request)
        
        # Analyze queries
        self._analyze_queries(request)
        
        return response
    
    def _analyze_queries(self, request):
        """Analyze database queries for performance issues"""
        from .utils import analyze_query_performance
        
        try:
            analysis = analyze_query_performance(connection.queries)
            
            if analysis['slow_queries']:
                logger.warning(
                    f"Slow queries detected for {request.path}",
                    extra={
                        'event_type': 'slow_queries',
                        'endpoint': request.path,
                        'slow_query_count': len(analysis['slow_queries']),
                        'total_queries': analysis['total_queries'],
                        'slowest_query_time': max(q['time'] for q in analysis['slow_queries']),
                    }
                )
            
            if analysis['duplicate_queries']:
                logger.warning(
                    f"Duplicate queries detected for {request.path}",
                    extra={
                        'event_type': 'duplicate_queries',
                        'endpoint': request.path,
                        'duplicate_count': len(analysis['duplicate_queries']),
                        'most_duplicated': analysis['duplicate_queries'][0] if analysis['duplicate_queries'] else None,
                    }
                )
                
        except Exception as e:
            logger.error(f"Failed to analyze queries: {e}")


class CacheMetricsMiddleware:
    """
    Middleware to track cache performance
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Track cache operations during request
        original_get = cache.get
        original_set = cache.set
        
        cache_ops = {'hits': 0, 'misses': 0, 'sets': 0}
        
        def tracked_get(key, default=None, version=None):
            result = original_get(key, default, version)
            if result is not None and result != default:
                cache_ops['hits'] += 1
            else:
                cache_ops['misses'] += 1
            return result
        
        def tracked_set(key, value, timeout=None, version=None):
            cache_ops['sets'] += 1
            return original_set(key, value, timeout, version)
        
        # Monkey patch for this request
        cache.get = tracked_get
        cache.set = tracked_set
        
        try:
            response = self.get_response(request)
            
            # Log cache performance
            total_ops = cache_ops['hits'] + cache_ops['misses']
            if total_ops > 0:
                hit_rate = (cache_ops['hits'] / total_ops) * 100
                
                logger.info(
                    f"Cache performance for {request.path}",
                    extra={
                        'event_type': 'cache_performance',
                        'endpoint': request.path,
                        'cache_hits': cache_ops['hits'],
                        'cache_misses': cache_ops['misses'],
                        'cache_sets': cache_ops['sets'],
                        'hit_rate_percent': hit_rate,
                    }
                )
            
            return response
            
        finally:
            # Restore original methods
            cache.get = original_get
            cache.set = original_set