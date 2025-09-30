"""
Health check views for monitoring system status.
"""
import os
import shutil
import time
import redis
from celery import current_app
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """간단한 헬스체크 엔드포인트"""
    return Response({
        'status': 'healthy',
        'timestamp': int(time.time())
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def health_detailed(request):
    """상세한 헬스체크 - 모든 서비스 상태 확인"""
    start_time = time.time()
    health_data = {
        'status': 'healthy',
        'timestamp': int(start_time),
        'services': {}
    }

    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_data['services']['database'] = {
            'status': 'healthy',
            'response_time_ms': round((time.time() - start_time) * 1000, 2)
        }
    except Exception as e:
        health_data['services']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_data['status'] = 'degraded'

    # Cache check (Local Memory)
    cache_start = time.time()
    try:
        cache.set('health_check', 'test', 30)
        cache_result = cache.get('health_check')
        if cache_result == 'test':
            health_data['services']['cache'] = {
                'status': 'healthy',
                'response_time_ms': round((time.time() - cache_start) * 1000, 2)
            }
        else:
            raise Exception("Cache test failed")
    except Exception as e:
        health_data['services']['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_data['status'] = 'degraded'

    # Redis check (Celery Broker)
    redis_start = time.time()
    try:
        redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0')
        redis_client = redis.from_url(redis_url)
        redis_client.ping()
        redis_client.set('health_check_redis', 'test', ex=30)
        redis_result = redis_client.get('health_check_redis')
        if redis_result and redis_result.decode('utf-8') == 'test':
            health_data['services']['redis'] = {
                'status': 'healthy',
                'response_time_ms': round((time.time() - redis_start) * 1000, 2),
                'url': redis_url.replace(redis_url.split('@')[0] + '@' if '@' in redis_url else '', '***@') if '@' in redis_url else redis_url
            }
        else:
            raise Exception("Redis test failed")
    except Exception as e:
        health_data['services']['redis'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_data['status'] = 'degraded'

    # Disk space check
    disk_start = time.time()
    try:
        disk_usage = shutil.disk_usage('/')
        total_gb = disk_usage.total / (1024**3)
        free_gb = disk_usage.free / (1024**3)
        used_gb = (disk_usage.total - disk_usage.free) / (1024**3)
        usage_percent = (used_gb / total_gb) * 100

        disk_status = 'healthy'
        if usage_percent > 90:
            disk_status = 'critical'
            health_data['status'] = 'degraded'
        elif usage_percent > 80:
            disk_status = 'warning'

        health_data['services']['disk'] = {
            'status': disk_status,
            'usage_percent': round(usage_percent, 2),
            'total_gb': round(total_gb, 2),
            'free_gb': round(free_gb, 2),
            'used_gb': round(used_gb, 2),
            'response_time_ms': round((time.time() - disk_start) * 1000, 2)
        }
    except Exception as e:
        health_data['services']['disk'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_data['status'] = 'degraded'

    # Celery check
    celery_start = time.time()
    try:
        # Check active workers
        inspect = current_app.control.inspect()
        active_workers = inspect.active()
        stats = inspect.stats()

        worker_count = len(active_workers) if active_workers else 0
        worker_status = 'healthy' if worker_count > 0 else 'degraded'

        if worker_count == 0:
            health_data['status'] = 'degraded'

        health_data['services']['celery'] = {
            'status': worker_status,
            'active_workers': worker_count,
            'worker_details': active_workers or {},
            'response_time_ms': round((time.time() - celery_start) * 1000, 2)
        }

        if stats:
            health_data['services']['celery']['stats'] = stats
    except Exception as e:
        health_data['services']['celery'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_data['status'] = 'degraded'

    # AI Service check
    ai_mock = getattr(settings, 'AI_USE_MOCK_RESPONSES', True)
    anthropic_key = getattr(settings, 'ANTHROPIC_API_KEY', None)

    if ai_mock:
        health_data['services']['ai'] = {
            'status': 'mock',
            'message': 'Using mock responses'
        }
    elif anthropic_key:
        health_data['services']['ai'] = {
            'status': 'configured',
            'message': 'API key configured'
        }
    else:
        health_data['services']['ai'] = {
            'status': 'unconfigured',
            'message': 'No API key configured'
        }

    # Overall response time
    health_data['total_response_time_ms'] = round((time.time() - start_time) * 1000, 2)

    if health_data['status'] == 'healthy':
        return Response(health_data, status=status.HTTP_200_OK)
    else:
        return Response(health_data, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """Kubernetes 스타일 readiness probe"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        cache.set('readiness', 'ok', 10)
        return Response({
            'ready': True,
            'timestamp': int(time.time())
        })
    except Exception as e:
        return Response({
            'ready': False,
            'error': str(e),
            'timestamp': int(time.time())
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([AllowAny])
def liveness_check(request):
    """Kubernetes 스타일 liveness probe"""
    return Response({
        'alive': True,
        'timestamp': int(time.time())
    })