"""
Custom exception handlers for Django REST Framework with Slack notifications.
"""
import logging
import traceback
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from utils.slack_notifications import slack_notifier

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that sends Slack alerts for server errors.

    Args:
        exc: The exception instance
        context: Dictionary with 'view' and 'request' keys

    Returns:
        Response: DRF Response object
    """
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)

    # If response is None, it's an unhandled exception (500 error)
    if response is None:
        # Get request details
        request = context.get('request')
        view = context.get('view')

        # Build error context
        error_context = {
            'exception_type': type(exc).__name__,
            'exception_message': str(exc),
            'view': view.__class__.__name__ if view else 'Unknown',
            'method': request.method if request else 'Unknown',
            'path': request.path if request else 'Unknown',
            'user': str(request.user) if request and hasattr(request, 'user') else 'Anonymous',
        }

        # Log the error
        logger.error(
            f"Unhandled exception: {error_context['exception_type']} - {error_context['exception_message']}",
            extra=error_context,
            exc_info=True
        )

        # Send Slack alert for 500 errors
        slack_notifier.send_alert(
            message=f"**Exception:** {error_context['exception_type']}\n"
                    f"**Message:** {error_context['exception_message']}\n"
                    f"**Endpoint:** {error_context['method']} {error_context['path']}\n"
                    f"**User:** {error_context['user']}\n"
                    f"**View:** {error_context['view']}",
            level='error',
            title='500 Server Error Detected'
        )

        # Return generic 500 response
        return Response(
            {
                'error': 'Internal server error',
                'message': 'An unexpected error occurred. The team has been notified.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # For 4xx errors, just log without Slack alert
    if response.status_code >= 400 and response.status_code < 500:
        request = context.get('request')
        logger.warning(
            f"Client error {response.status_code}: {exc}",
            extra={
                'status_code': response.status_code,
                'path': request.path if request else 'Unknown',
                'user': str(request.user) if request and hasattr(request, 'user') else 'Anonymous',
            }
        )

    return response
