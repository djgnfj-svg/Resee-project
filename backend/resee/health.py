"""
Health check endpoints for monitoring and load balancer health checks.
"""

import logging

import redis
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Basic health check endpoint.
    Returns 200 OK if the service is running.
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'resee-backend'
    })


def detailed_health_check(request):
    """
    Detailed health check that verifies all critical services.
    """
    health_status = {
        'status': 'healthy',
        'service': 'resee-backend',
        'checks': {}
    }
    
    overall_status = True
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status['checks']['database'] = 'unhealthy'
        overall_status = False
    
    # Cache (Redis) check
    try:
        cache.set('health_check', 'test', 30)
        result = cache.get('health_check')
        if result == 'test':
            health_status['checks']['cache'] = 'healthy'
        else:
            health_status['checks']['cache'] = 'unhealthy'
            overall_status = False
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        health_status['checks']['cache'] = 'unhealthy'
        overall_status = False
    
    # Celery broker check (optional - don't fail if celery is not critical)
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        if inspect.ping():
            health_status['checks']['celery'] = 'healthy'
        else:
            health_status['checks']['celery'] = 'unhealthy'
    except Exception as e:
        logger.warning(f"Celery health check failed: {e}")
        health_status['checks']['celery'] = 'warning'
        # Don't fail overall status for Celery issues
    
    if not overall_status:
        health_status['status'] = 'unhealthy'
        return JsonResponse(health_status, status=503)
    
    return JsonResponse(health_status)


def readiness_check(request):
    """
    Readiness check for Kubernetes or container orchestration.
    Checks if the application is ready to serve traffic.
    """
    ready = True
    checks = {}
    
    # Check if migrations are up to date
    try:
        from django.core.management import execute_from_command_line
        from django.db.migrations.executor import MigrationExecutor
        
        executor = MigrationExecutor(connection)
        if executor.migration_plan(executor.loader.graph.leaf_nodes()):
            checks['migrations'] = 'pending'
            ready = False
        else:
            checks['migrations'] = 'up_to_date'
    except Exception as e:
        logger.error(f"Migration check failed: {e}")
        checks['migrations'] = 'error'
        ready = False
    
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks['database'] = 'ready'
    except Exception as e:
        logger.error(f"Database readiness check failed: {e}")
        checks['database'] = 'not_ready'
        ready = False
    
    status = {
        'ready': ready,
        'checks': checks
    }
    
    if ready:
        return JsonResponse(status)
    else:
        return JsonResponse(status, status=503)


def liveness_check(request):
    """
    Liveness check for Kubernetes.
    Simple check to see if the application process is running.
    """
    return JsonResponse({
        'alive': True,
        'service': 'resee-backend'
    })