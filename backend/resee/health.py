"""
Health check endpoints for monitoring system status
"""
import logging
from django.conf import settings
from django.db import connections
from django.http import JsonResponse
from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Basic health check endpoint"""
    return Response({
        'status': 'healthy',
        'timestamp': __import__('datetime').datetime.now().isoformat()
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def liveness_check(request):
    """Kubernetes liveness probe"""
    return JsonResponse({'status': 'alive'})


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """Kubernetes readiness probe"""
    try:
        # Check database connection
        db_conn = connections['default']
        db_conn.ensure_connection()
        
        return JsonResponse({'status': 'ready'})
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JsonResponse({
            'status': 'not ready',
            'error': str(e)
        }, status=503)


@api_view(['GET'])
@permission_classes([AllowAny])
def detailed_health_check(request):
    """Detailed health check with component status"""
    health_status = {
        'status': 'healthy',
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'components': {}
    }
    
    overall_healthy = True
    
    # Check database
    try:
        db_conn = connections['default']
        db_conn.ensure_connection()
        db_conn.cursor().execute('SELECT 1')
        health_status['components']['database'] = {'status': 'healthy'}
    except Exception as e:
        health_status['components']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        overall_healthy = False
    
    # Check cache (Local Memory)
    try:
        cache.set('health_check', 'ok', timeout=1)
        if cache.get('health_check') == 'ok':
            health_status['components']['cache'] = {'status': 'healthy'}
        else:
            health_status['components']['cache'] = {'status': 'unhealthy'}
            overall_healthy = False
    except Exception as e:
        health_status['components']['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        overall_healthy = False
    
    # Check AI service (optional)
    if hasattr(settings, 'ANTHROPIC_API_KEY') and settings.ANTHROPIC_API_KEY:
        health_status['components']['ai_service'] = {'status': 'configured'}
    else:
        health_status['components']['ai_service'] = {
            'status': 'not configured',
            'note': 'AI features may not work'
        }
    
    if not overall_healthy:
        health_status['status'] = 'unhealthy'
        return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    return Response(health_status, status=status.HTTP_200_OK)