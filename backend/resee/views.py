"""
Health check views for infrastructure monitoring with Slack notifications.
"""
import logging
from django.db import connection
from django.http import JsonResponse
from django.core.cache import caches
from django.conf import settings
from utils.slack_notifications import slack_notifier

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Basic health check endpoint for Docker/Railway infrastructure.

    Returns:
        200 OK if service is healthy
        503 Service Unavailable if database is not accessible
    """
    try:
        # Simple DB ping
        connection.ensure_connection()
        return JsonResponse({'status': 'ok'}, status=200)
    except Exception as e:
        # Send Slack alert for DB failure
        slack_notifier.send_health_alert(
            service='database',
            status='down',
            details=f'Health check failed: {str(e)}'
        )
        logger.error(f"Health check failed - Database error: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=503)


def detailed_health_check(request):
    """
    Detailed health check for all system components with Slack notifications.

    Checks:
    - Database connectivity
    - Redis connectivity (throttle cache)
    - Celery broker connectivity

    Returns:
        200 OK if all services are healthy
        503 Service Unavailable if any service is down
    """
    health_status = {
        'status': 'ok',
        'timestamp': None,
        'services': {}
    }

    all_healthy = True

    # Check Database
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        health_status['services']['database'] = {'status': 'ok'}
        logger.debug("Database health check passed")
    except Exception as e:
        all_healthy = False
        health_status['services']['database'] = {
            'status': 'error',
            'error': str(e)
        }
        # Send Slack alert
        slack_notifier.send_health_alert(
            service='database',
            status='down',
            details=str(e)
        )
        logger.error(f"Database health check failed: {e}")

    # Check Redis (throttle cache)
    try:
        cache = caches['throttle']
        cache.set('health_check', 'ok', 10)
        result = cache.get('health_check')
        if result != 'ok':
            raise Exception("Cache set/get mismatch")
        cache.delete('health_check')
        health_status['services']['redis'] = {'status': 'ok'}
        logger.debug("Redis health check passed")
    except Exception as e:
        all_healthy = False
        health_status['services']['redis'] = {
            'status': 'error',
            'error': str(e)
        }
        # Send Slack alert
        slack_notifier.send_health_alert(
            service='redis',
            status='down',
            details=str(e)
        )
        logger.error(f"Redis health check failed: {e}")

    # Check Celery broker (Redis-based)
    try:
        from celery import Celery
        app = Celery()
        app.config_from_object('django.conf:settings', namespace='CELERY')

        # Try to inspect Celery workers
        inspect = app.control.inspect(timeout=5)
        stats = inspect.stats()

        if stats:
            health_status['services']['celery'] = {
                'status': 'ok',
                'workers': len(stats)
            }
            logger.debug(f"Celery health check passed - {len(stats)} workers active")
        else:
            # No workers found but broker might be ok
            health_status['services']['celery'] = {
                'status': 'degraded',
                'warning': 'No active workers found'
            }
            logger.warning("Celery health check: No active workers found")
    except Exception as e:
        all_healthy = False
        health_status['services']['celery'] = {
            'status': 'error',
            'error': str(e)
        }
        # Send Slack alert
        slack_notifier.send_health_alert(
            service='celery',
            status='down',
            details=str(e)
        )
        logger.error(f"Celery health check failed: {e}")

    # Set overall status
    if not all_healthy:
        health_status['status'] = 'degraded'

    # Add timestamp
    from datetime import datetime
    health_status['timestamp'] = datetime.now().isoformat()

    status_code = 200 if all_healthy else 503
    return JsonResponse(health_status, status=status_code)


def test_slack_notification(request):
    """
    Test endpoint to verify Slack notifications are working.
    Restricted to staff users only.

    Query parameters:
    - level: Alert level (error, warning, info, success) - default: info
    - message: Custom message - default: Test notification

    Returns:
        200 OK with notification status
        403 Forbidden if not staff user
    """
    # Check if user is staff
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({
            'error': 'Permission denied',
            'message': 'Only staff users can test Slack notifications'
        }, status=403)

    # Get parameters
    level = request.GET.get('level', 'info')
    message = request.GET.get('message', 'This is a test notification from Resee monitoring system')

    # Validate level
    if level not in ['error', 'warning', 'info', 'success']:
        return JsonResponse({
            'error': 'Invalid level',
            'message': 'Level must be one of: error, warning, info, success'
        }, status=400)

    # Send test notification
    result = slack_notifier.send_alert(
        message=message,
        level=level,
        title='Test Notification',
        fields={
            'Triggered by': str(request.user),
            'Environment': settings.DEBUG and 'Development' or 'Production',
        }
    )

    if result:
        return JsonResponse({
            'status': 'success',
            'message': 'Slack notification sent successfully',
            'notification': {
                'level': level,
                'message': message,
                'sent_to': slack_notifier.default_channel
            }
        }, status=200)
    else:
        return JsonResponse({
            'status': 'failed',
            'message': 'Failed to send Slack notification. Check webhook configuration.',
            'webhook_configured': slack_notifier.enabled
        }, status=500)
