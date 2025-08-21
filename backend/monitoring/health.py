"""
Health check endpoints for monitoring system availability
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import time
import logging

logger = logging.getLogger(__name__)

def health_check_basic(request):
    """
    Basic health check endpoint
    Returns 200 if service is running
    """
    return JsonResponse({
        'status': 'healthy',
        'timestamp': time.time(),
        'service': 'resee-backend'
    })

def health_check_detailed(request):
    """
    Detailed health check with dependency verification
    """
    status = 'healthy'
    checks = {}
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        checks['database'] = 'healthy'
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks['database'] = 'unhealthy'
        status = 'unhealthy'
    
    # Cache check (Redis)
    try:
        cache_key = 'health_check_test'
        cache.set(cache_key, 'test', timeout=30)
        test_value = cache.get(cache_key)
        if test_value == 'test':
            checks['cache'] = 'healthy'
        else:
            checks['cache'] = 'unhealthy'
            status = 'unhealthy'
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        checks['cache'] = 'unhealthy'
        status = 'unhealthy'
    
    # Celery check (optional)
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        if stats:
            checks['celery'] = 'healthy'
        else:
            checks['celery'] = 'unhealthy'
            # Don't fail overall health for celery issues in beta
    except Exception as e:
        logger.warning(f"Celery health check failed: {e}")
        checks['celery'] = 'warning'
    
    return JsonResponse({
        'status': status,
        'timestamp': time.time(),
        'service': 'resee-backend',
        'checks': checks,
        'version': getattr(settings, 'VERSION', '1.0.0')
    })

def readiness_check(request):
    """
    Readiness check - service is ready to receive traffic
    """
    # Check if migrations are up to date
    try:
        from django.core.management import execute_from_command_line
        from io import StringIO
        import sys
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            execute_from_command_line(['manage.py', 'showmigrations', '--plan'])
            output = captured_output.getvalue()
            # Check if there are unapplied migrations
            if '[ ]' in output:
                return JsonResponse({
                    'status': 'not_ready',
                    'reason': 'unapplied_migrations'
                }, status=503)
        finally:
            sys.stdout = old_stdout
            
    except Exception as e:
        logger.error(f"Migration check failed: {e}")
        return JsonResponse({
            'status': 'not_ready',
            'reason': 'migration_check_failed'
        }, status=503)
    
    return JsonResponse({
        'status': 'ready',
        'timestamp': time.time(),
        'service': 'resee-backend'
    })

def liveness_check(request):
    """
    Liveness check - service is alive (basic functionality)
    """
    # Very basic check - just return success if Django is running
    return JsonResponse({
        'status': 'alive',
        'timestamp': time.time(),
        'service': 'resee-backend'
    })