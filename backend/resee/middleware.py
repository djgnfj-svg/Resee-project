"""
Production security and monitoring middleware for Resee
"""
import logging
import re
import time

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import HttpResponseForbidden, JsonResponse
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


class SQLInjectionDetectionMiddleware(MiddlewareMixin):
    """Detect potential SQL injection attempts"""
    
    SQL_INJECTION_PATTERNS = [
        r"(\bunion\b.*\bselect\b)|(\bselect\b.*\bunion\b)",
        r"(\bdrop\b.*\btable\b)|(\btable\b.*\bdrop\b)",
        r"(\binsert\b.*\binto\b)|(\binto\b.*\binsert\b)",
        r"(\bdelete\b.*\bfrom\b)|(\bfrom\b.*\bdelete\b)",
        r"(\bupdate\b.*\bset\b)|(\bset\b.*\bupdate\b)",
        r"(\bexec\b.*\bsp_\b)|(\bsp_\b.*\bexec\b)",
        r"(\bor\b.*1.*=.*1)|(\band\b.*1.*=.*1)",
        r"(\bor\b.*'.*'.*=.*'.*')|(\band\b.*'.*'.*=.*'.*')",
        r"(\b--)|(\b#)|(\b/\*.*\*/)",
        r"(\bxp_cmdshell\b)|(\bsp_executesql\b)",
    ]
    
    def process_request(self, request):
        # Check query parameters
        for key, value in request.GET.items():
            if self._is_sql_injection(value):
                logger.critical(f"SQL injection attempt detected in GET param '{key}': {value}")
                return HttpResponseForbidden("잘못된 요청입니다.")
        
        # Check POST data
        if hasattr(request, 'POST'):
            for key, value in request.POST.items():
                if self._is_sql_injection(str(value)):
                    logger.critical(f"SQL injection attempt detected in POST param '{key}': {value}")
                    return HttpResponseForbidden("잘못된 요청입니다.")
        
        return None
    
    def _is_sql_injection(self, value):
        value_lower = str(value).lower()
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False


