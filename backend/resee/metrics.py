"""
System metrics and monitoring endpoints for Resee application.

Provides endpoints for monitoring application health, performance, and resource usage.
"""
import os
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from accounts.models import User
from content.models import Content
from review.models import ReviewSchedule
from exams.models import WeeklyTest


@api_view(['GET'])
@permission_classes([IsAdminUser])
def system_metrics(request):
    """
    Get comprehensive system metrics.

    Returns system resource usage, database stats, and application metrics.

    **Requires:** Admin authentication

    **Response:**
    ```json
    {
        "timestamp": "2025-01-18T10:30:00Z",
        "system": {
            "cpu_percent": 45.2,
            "memory": {...},
            "disk": {...}
        },
        "database": {...},
        "cache": {...},
        "application": {...}
    }
    ```
    """
    metrics = {
        'timestamp': timezone.now().isoformat(),
        'system': _get_system_metrics(),
        'database': _get_database_metrics(),
        'cache': _get_cache_metrics(),
        'application': _get_application_metrics(),
    }

    return Response(metrics, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def performance_metrics(request):
    """
    Get application performance metrics.

    Returns request counts, response times, and error rates.

    **Requires:** Admin authentication
    """
    # Get metrics from cache (populated by middleware)
    metrics_key = 'app:metrics:performance'
    perf_metrics = cache.get(metrics_key, {})

    if not perf_metrics:
        perf_metrics = _initialize_performance_metrics()

    return Response({
        'timestamp': timezone.now().isoformat(),
        'performance': perf_metrics
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def business_metrics(request):
    """
    Get business/application-specific metrics.

    Returns user statistics, content statistics, and review metrics.

    **Requires:** Admin authentication
    """
    now = timezone.now()
    today = now.date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    metrics = {
        'timestamp': now.isoformat(),
        'users': {
            'total': User.objects.count(),
            'active_today': User.objects.filter(last_login__date=today).count(),
            'active_week': User.objects.filter(last_login__gte=week_ago).count(),
            'new_this_month': User.objects.filter(date_joined__gte=month_ago).count(),
            'email_verified': User.objects.filter(is_email_verified=True).count(),
        },
        'content': {
            'total': Content.objects.count(),
            'ai_validated': Content.objects.filter(is_ai_validated=True).count(),
            'created_this_month': Content.objects.filter(created_at__gte=month_ago).count(),
        },
        'reviews': {
            'total_scheduled': ReviewSchedule.objects.filter(completed_at__isnull=True).count(),
            'due_today': ReviewSchedule.objects.filter(
                next_review_date__date=today,
                completed_at__isnull=True
            ).count(),
            'completed_this_week': ReviewSchedule.objects.filter(
                completed_at__gte=week_ago
            ).count(),
        },
        'exams': {
            'total': WeeklyTest.objects.count(),
            'active': WeeklyTest.objects.filter(status='not_started').count(),
            'completed_this_month': WeeklyTest.objects.filter(
                completed_at__gte=month_ago
            ).count(),
        },
    }

    return Response(metrics, status=status.HTTP_200_OK)


def _get_system_metrics() -> Dict[str, Any]:
    """Get system resource metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            'cpu_percent': cpu_percent,
            'cpu_count': psutil.cpu_count(),
            'memory': {
                'total_gb': round(memory.total / (1024 ** 3), 2),
                'used_gb': round(memory.used / (1024 ** 3), 2),
                'available_gb': round(memory.available / (1024 ** 3), 2),
                'percent': memory.percent,
            },
            'disk': {
                'total_gb': round(disk.total / (1024 ** 3), 2),
                'used_gb': round(disk.used / (1024 ** 3), 2),
                'free_gb': round(disk.free / (1024 ** 3), 2),
                'percent': disk.percent,
            },
            'uptime_seconds': time.time() - psutil.boot_time(),
        }
    except Exception as e:
        return {'error': str(e)}


def _get_database_metrics() -> Dict[str, Any]:
    """Get database metrics"""
    try:
        with connection.cursor() as cursor:
            # Get database size (PostgreSQL)
            cursor.execute("""
                SELECT pg_database_size(current_database()) as size,
                       pg_size_pretty(pg_database_size(current_database())) as size_pretty
            """)
            db_size = cursor.fetchone()

            # Get connection count
            cursor.execute("SELECT count(*) FROM pg_stat_activity")
            connections = cursor.fetchone()[0]

            # Get table counts
            table_stats = {
                'users': User.objects.count(),
                'content': Content.objects.count(),
                'review_schedules': ReviewSchedule.objects.count(),
                'weekly_tests': WeeklyTest.objects.count(),
            }

        return {
            'size_bytes': db_size[0] if db_size else 0,
            'size_human': db_size[1] if db_size else '0 bytes',
            'connections': connections,
            'table_counts': table_stats,
        }
    except Exception as e:
        return {'error': str(e)}


def _get_cache_metrics() -> Dict[str, Any]:
    """Get Redis cache metrics"""
    try:
        # Test cache connection
        test_key = 'metrics:cache:test'
        cache.set(test_key, 'ok', 10)
        cache_status = 'connected' if cache.get(test_key) == 'ok' else 'disconnected'
        cache.delete(test_key)

        return {
            'status': cache_status,
            'backend': settings.CACHES['default']['BACKEND'],
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


def _get_application_metrics() -> Dict[str, Any]:
    """Get application-specific metrics"""
    return {
        'django_version': settings.DJANGO_VERSION if hasattr(settings, 'DJANGO_VERSION') else 'unknown',
        'debug_mode': settings.DEBUG,
        'environment': os.environ.get('DJANGO_SETTINGS_MODULE', 'unknown').split('.')[-1],
        'allowed_hosts': settings.ALLOWED_HOSTS[:3],  # First 3 hosts only
    }


def _initialize_performance_metrics() -> Dict[str, Any]:
    """Initialize default performance metrics"""
    return {
        'request_count': 0,
        'avg_response_time_ms': 0,
        'error_count': 0,
        'error_rate': 0,
        'last_reset': timezone.now().isoformat(),
    }


# Middleware to track performance metrics
class MetricsMiddleware:
    """
    Middleware to collect performance metrics.

    Tracks request counts, response times, and error rates.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        # Calculate request duration
        duration_ms = (time.time() - start_time) * 1000

        # Update metrics in cache
        self._update_metrics(request, response, duration_ms)

        # Add custom header with response time
        response['X-Response-Time'] = f'{duration_ms:.2f}ms'

        return response

    def _update_metrics(self, request, response, duration_ms):
        """Update performance metrics in cache"""
        metrics_key = 'app:metrics:performance'
        metrics = cache.get(metrics_key, _initialize_performance_metrics())

        # Increment request count
        metrics['request_count'] = metrics.get('request_count', 0) + 1

        # Update average response time (simple moving average)
        current_avg = metrics.get('avg_response_time_ms', 0)
        count = metrics['request_count']
        metrics['avg_response_time_ms'] = ((current_avg * (count - 1)) + duration_ms) / count

        # Track errors (4xx and 5xx)
        if response.status_code >= 400:
            metrics['error_count'] = metrics.get('error_count', 0) + 1

        # Calculate error rate
        metrics['error_rate'] = (metrics['error_count'] / metrics['request_count']) * 100 if metrics['request_count'] > 0 else 0

        # Store updated metrics (expire after 1 hour)
        cache.set(metrics_key, metrics, 3600)
