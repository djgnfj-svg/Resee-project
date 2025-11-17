"""
Production security and monitoring middleware for Resee
"""
import logging
import time

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)
performance_logger = logging.getLogger('resee.performance')


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers for production environments"""

    def process_response(self, request, response):
        if getattr(settings, 'ENVIRONMENT', 'development') in ['staging', 'production']:
            # Security headers
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none'"
            )

            # Remove server info
            if 'Server' in response:
                del response['Server']

            response['Server'] = 'Resee'

        return response


class RequestLoggingMiddleware(MiddlewareMixin):
    """Log requests for monitoring and debugging"""

    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time

            # Log slow requests (> 1 second)
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.2f}s - Status: {response.status_code}"
                )

            # Log API errors
            if request.path.startswith('/api/') and response.status_code >= 400:
                logger.error(
                    f"API error: {request.method} {request.path} - "
                    f"Status: {response.status_code} - "
                    f"User: {getattr(request.user, 'email', 'anonymous')} - "
                    f"Duration: {duration:.2f}s"
                )

        return response
