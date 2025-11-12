"""
Minimal health check views for infrastructure monitoring.
"""
from django.db import connection
from django.http import JsonResponse


def health_check(request):
    """
    Basic health check endpoint for Docker/AWS infrastructure.

    Returns:
        200 OK if service is healthy
        503 Service Unavailable if database is not accessible
    """
    try:
        # Simple DB ping
        connection.ensure_connection()
        return JsonResponse({'status': 'ok'}, status=200)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=503)
