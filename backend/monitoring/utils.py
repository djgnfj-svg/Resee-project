"""
Utility functions for monitoring and performance analysis
"""
import hashlib
import logging
import re
import time
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from django.core.cache import cache
from django.db import connection
from django.utils import timezone

logger = logging.getLogger('monitoring')


def get_client_ip(request) -> Optional[str]:
    """
    Extract client IP address from request
    """
    # Check for IP in headers (behind proxy/load balancer)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        return x_real_ip.strip()
    
    # Fallback to REMOTE_ADDR
    return request.META.get('REMOTE_ADDR')


def get_device_type(user_agent: str) -> str:
    """
    Determine device type from user agent string
    """
    user_agent_lower = user_agent.lower()
    
    # Mobile patterns
    mobile_patterns = [
        r'mobile', r'android', r'iphone', r'ipod', r'blackberry',
        r'windows phone', r'opera mini', r'mobile safari'
    ]
    
    # Tablet patterns
    tablet_patterns = [
        r'ipad', r'tablet', r'kindle', r'silk', r'android.*tablet'
    ]
    
    # Check for tablet first (more specific)
    for pattern in tablet_patterns:
        if re.search(pattern, user_agent_lower):
            return 'tablet'
    
    # Check for mobile
    for pattern in mobile_patterns:
        if re.search(pattern, user_agent_lower):
            return 'mobile'
    
    # Default to desktop
    return 'desktop'


def should_track_request(request) -> bool:
    """
    Determine if request should be tracked for metrics
    """
    # Skip static files
    if request.path.startswith('/static/') or request.path.startswith('/media/'):
        return False
    
    # Skip admin interface
    if request.path.startswith('/admin/'):
        return False
    
    # Skip health checks
    if request.path in ['/health/', '/api/health/', '/monitoring/health/']:
        return False
    
    # Skip monitoring endpoints to prevent recursion
    if request.path.startswith('/monitoring/'):
        return False
    
    # Skip development tools
    if request.path.startswith('/__debug__/'):
        return False
    
    return True


def normalize_query(query: str) -> str:
    """
    Normalize SQL query for pattern matching
    Removes specific values and normalizes whitespace
    """
    # Remove string literals
    normalized = re.sub(r"'[^']*'", "'?'", query)
    
    # Remove numeric literals
    normalized = re.sub(r'\b\d+\b', '?', normalized)
    
    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', normalized.strip())
    
    return normalized


def get_query_hash(query: str) -> str:
    """
    Generate MD5 hash of normalized query for duplicate detection
    """
    normalized = normalize_query(query)
    return hashlib.md5(normalized.encode()).hexdigest()


def analyze_query_performance(queries: List[Dict]) -> Dict[str, Any]:
    """
    Analyze database queries for performance issues
    """
    if not queries:
        return {
            'total_queries': 0,
            'slow_queries': [],
            'duplicate_queries': [],
            'total_time': 0,
            'avg_time': 0
        }
    
    slow_query_threshold = 100  # ms
    duplicate_threshold = 3  # count
    
    slow_queries = []
    query_patterns = Counter()
    total_time = 0
    
    for query in queries:
        query_time = float(query.get('time', 0)) * 1000  # Convert to ms
        total_time += query_time
        
        # Check for slow queries
        if query_time > slow_query_threshold:
            slow_queries.append({
                'sql': query['sql'][:200] + '...' if len(query['sql']) > 200 else query['sql'],
                'time': query_time,
                'hash': get_query_hash(query['sql'])
            })
        
        # Track query patterns for duplicate detection
        normalized = normalize_query(query['sql'])
        query_patterns[normalized] += 1
    
    # Find duplicate queries
    duplicate_queries = [
        {
            'pattern': pattern,
            'count': count,
            'normalized_sql': pattern[:200] + '...' if len(pattern) > 200 else pattern
        }
        for pattern, count in query_patterns.items()
        if count >= duplicate_threshold
    ]
    
    return {
        'total_queries': len(queries),
        'slow_queries': slow_queries,
        'duplicate_queries': sorted(duplicate_queries, key=lambda x: x['count'], reverse=True),
        'total_time': total_time,
        'avg_time': total_time / len(queries) if queries else 0
    }


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache performance statistics
    """
    try:
        # Get Redis cache stats
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        
        # Get basic info
        info = redis_conn.info()
        
        # Calculate hit rate
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total_ops = hits + misses
        hit_rate = (hits / total_ops * 100) if total_ops > 0 else 0
        
        return {
            'hit_rate_percent': hit_rate,
            'hits': hits,
            'misses': misses,
            'total_operations': total_ops,
            'memory_usage_mb': info.get('used_memory', 0) / 1024 / 1024,
            'connected_clients': info.get('connected_clients', 0),
            'uptime_seconds': info.get('uptime_in_seconds', 0)
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {
            'hit_rate_percent': 0,
            'hits': 0,
            'misses': 0,
            'total_operations': 0,
            'memory_usage_mb': 0,
            'connected_clients': 0,
            'uptime_seconds': 0
        }


def get_database_stats() -> Dict[str, Any]:
    """
    Get database performance statistics
    """
    try:
        with connection.cursor() as cursor:
            # Get connection count
            cursor.execute("""
                SELECT count(*) 
                FROM pg_stat_activity 
                WHERE state = 'active'
            """)
            active_connections = cursor.fetchone()[0]
            
            # Get average query time from pg_stat_statements if available
            try:
                cursor.execute("""
                    SELECT avg(mean_exec_time) 
                    FROM pg_stat_statements 
                    WHERE calls > 10
                """)
                avg_query_time = cursor.fetchone()[0] or 0
            except Exception:
                # pg_stat_statements not enabled
                avg_query_time = 0
            
            # Get database size
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """)
            db_size = cursor.fetchone()[0]
            
            return {
                'active_connections': active_connections,
                'avg_query_time_ms': float(avg_query_time),
                'database_size': db_size,
                'status': 'healthy'
            }
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {
            'active_connections': 0,
            'avg_query_time_ms': 0,
            'database_size': 'unknown',
            'status': 'error'
        }


def check_system_health() -> Dict[str, Any]:
    """
    Comprehensive system health check
    """
    health_data = {
        'timestamp': timezone.now().isoformat(),
        'overall_status': 'healthy',
        'services': {}
    }
    
    # Check database
    try:
        db_stats = get_database_stats()
        health_data['services']['database'] = {
            'status': 'healthy' if db_stats['status'] != 'error' else 'unhealthy',
            'details': db_stats
        }
    except Exception as e:
        health_data['services']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_data['overall_status'] = 'degraded'
    
    # Check cache
    try:
        cache_stats = get_cache_stats()
        cache_healthy = cache_stats['uptime_seconds'] > 0
        health_data['services']['cache'] = {
            'status': 'healthy' if cache_healthy else 'unhealthy',
            'details': cache_stats
        }
        if not cache_healthy:
            health_data['overall_status'] = 'degraded'
    except Exception as e:
        health_data['services']['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_data['overall_status'] = 'degraded'
    
    # Check Celery workers
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        active_workers = inspect.active()
        worker_count = len(active_workers) if active_workers else 0
        
        health_data['services']['celery'] = {
            'status': 'healthy' if worker_count > 0 else 'unhealthy',
            'details': {
                'active_workers': worker_count,
                'workers': list(active_workers.keys()) if active_workers else []
            }
        }
        if worker_count == 0:
            health_data['overall_status'] = 'degraded'
    except Exception as e:
        health_data['services']['celery'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_data['overall_status'] = 'degraded'
    
    return health_data


def calculate_performance_score(metrics: Dict[str, Any]) -> float:
    """
    Calculate overall performance score (0-100)
    """
    score = 100.0
    
    # Response time penalty
    if metrics.get('avg_response_time_ms', 0) > 1000:
        score -= 20
    elif metrics.get('avg_response_time_ms', 0) > 500:
        score -= 10
    
    # Error rate penalty
    error_rate = metrics.get('error_rate_percent', 0)
    if error_rate > 5:
        score -= 30
    elif error_rate > 1:
        score -= 15
    
    # Database performance penalty
    avg_query_time = metrics.get('avg_query_time_ms', 0)
    if avg_query_time > 100:
        score -= 15
    elif avg_query_time > 50:
        score -= 8
    
    # Cache performance bonus/penalty
    cache_hit_rate = metrics.get('cache_hit_rate_percent', 0)
    if cache_hit_rate > 90:
        score += 5
    elif cache_hit_rate < 50:
        score -= 10
    
    return max(0, min(100, score))


def batch_insert_metrics(model_class, metrics_data: List[Dict], batch_size: int = 100):
    """
    Efficiently insert metrics data in batches
    """
    if not metrics_data:
        return
    
    try:
        # Create model instances
        instances = [model_class(**data) for data in metrics_data]
        
        # Bulk create in batches
        for i in range(0, len(instances), batch_size):
            batch = instances[i:i + batch_size]
            model_class.objects.bulk_create(batch, batch_size=batch_size)
            
        logger.info(f"Successfully inserted {len(metrics_data)} {model_class.__name__} records")
        
    except Exception as e:
        logger.error(f"Failed to batch insert {model_class.__name__} metrics: {e}")


def clean_old_metrics(days_to_keep: int = 30):
    """
    Clean up old metrics data to prevent database bloat
    """
    from .models import (AIMetrics, APIMetrics, DatabaseMetrics, ErrorLog,
                         SystemHealth, UserActivity)
    
    cutoff_date = timezone.now().date() - timezone.timedelta(days=days_to_keep)
    
    models_to_clean = [
        (APIMetrics, 'API metrics'),
        (DatabaseMetrics, 'Database metrics'),
        (AIMetrics, 'AI metrics'), 
        (ErrorLog, 'Error logs'),
        (SystemHealth, 'System health'),
        (UserActivity, 'User activity')
    ]
    
    total_deleted = 0
    
    for model_class, description in models_to_clean:
        try:
            deleted_count = model_class.objects.filter(date__lt=cutoff_date).delete()[0]
            total_deleted += deleted_count
            logger.info(f"Cleaned {deleted_count} old {description} records")
        except Exception as e:
            logger.error(f"Failed to clean old {description}: {e}")
    
    logger.info(f"Total cleaned records: {total_deleted}")
    return total_deleted


def get_performance_insights(timeframe_hours: int = 24) -> Dict[str, Any]:
    """
    Generate performance insights for the specified timeframe
    """
    from .models import APIMetrics, DatabaseMetrics, ErrorLog
    
    since = timezone.now() - timezone.timedelta(hours=timeframe_hours)
    
    # API performance insights
    api_metrics = APIMetrics.objects.filter(timestamp__gte=since)
    
    insights = {
        'timeframe_hours': timeframe_hours,
        'api_insights': {},
        'database_insights': {},
        'error_insights': {},
        'recommendations': []
    }
    
    # API insights
    if api_metrics.exists():
        avg_response_time = api_metrics.aggregate(
            avg_time=models.Avg('response_time_ms')
        )['avg_time'] or 0
        
        slow_endpoints = api_metrics.filter(
            response_time_ms__gt=1000
        ).values('endpoint').annotate(
            count=models.Count('id'),
            avg_time=models.Avg('response_time_ms')
        ).order_by('-avg_time')[:5]
        
        insights['api_insights'] = {
            'avg_response_time_ms': avg_response_time,
            'total_requests': api_metrics.count(),
            'slow_endpoints': list(slow_endpoints)
        }
        
        if avg_response_time > 500:
            insights['recommendations'].append(
                "Consider optimizing API response times - current average is above 500ms"
            )
    
    # Error insights
    error_logs = ErrorLog.objects.filter(timestamp__gte=since)
    if error_logs.exists():
        top_errors = error_logs.values('exception_type').annotate(
            count=models.Count('id')
        ).order_by('-count')[:5]
        
        insights['error_insights'] = {
            'total_errors': error_logs.count(),
            'top_error_types': list(top_errors)
        }
        
        if error_logs.count() > 100:
            insights['recommendations'].append(
                f"High error rate detected: {error_logs.count()} errors in {timeframe_hours} hours"
            )
    
    return insights