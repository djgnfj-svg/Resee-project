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


class BasicRateLimitMiddleware(MiddlewareMixin):
    """Basic rate limiting using local memory cache"""

    # Basic IP-based limits
    DEFAULT_LIMITS = {
        'minute': 60,    # 60 requests per minute
        'hour': 1000,    # 1000 requests per hour
    }

    # API endpoint specific limits
    ENDPOINT_LIMITS = {
        '/api/auth/token/': {'minute': 5, 'hour': 20},
        '/api/accounts/users/register/': {'hour': 3, 'day': 5},
        '/api/ai-review/generate-questions/': {'minute': 2, 'hour': 10},
    }

    WHITELIST_IPS = ['127.0.0.1', '::1']

    def process_request(self, request):
        if not getattr(settings, 'RATE_LIMIT_ENABLE', True):
            return None

        client_ip = self._get_client_ip(request)

        # Skip whitelist, health checks, static files
        if (client_ip in self.WHITELIST_IPS or
            request.path.startswith('/api/health/') or
            request.path.startswith('/static/') or
            request.path.startswith('/media/')):
            return None

        # Check IP-based limits
        for period, limit in self.DEFAULT_LIMITS.items():
            cache_key = f"rate_limit:ip:{client_ip}:{period}"
            window = {'minute': 60, 'hour': 3600}[period]

            if self._is_rate_limited(cache_key, limit, window):
                return self._create_rate_limit_response(
                    f"Rate limit exceeded: {limit} requests per {period}",
                    limit, window
                )

        # Check endpoint-specific limits
        endpoint_limits = self.ENDPOINT_LIMITS.get(request.path)
        if endpoint_limits:
            for period, limit in endpoint_limits.items():
                cache_key = f"rate_limit:endpoint:{client_ip}:{request.path}:{period}"
                window = {'minute': 60, 'hour': 3600, 'day': 86400}[period]

                if self._is_rate_limited(cache_key, limit, window):
                    return self._create_rate_limit_response(
                        f"Endpoint rate limit exceeded: {limit} requests per {period}",
                        limit, window
                    )

        return None

    def _is_rate_limited(self, cache_key, limit, window):
        """Check rate limit and increment counter"""
        try:
            current = cache.get(cache_key, 0)
            if current >= limit:
                return True

            cache.set(cache_key, current + 1, window)
            return False

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return False

    def _create_rate_limit_response(self, message, limit, window):
        """Create rate limit response"""
        response_data = {
            'error': 'rate_limit_exceeded',
            'message': message,
            'limit': limit,
            'window_seconds': window,
            'retry_after': window
        }

        response = JsonResponse(response_data, status=429)
        response['X-RateLimit-Limit'] = str(limit)
        response['X-RateLimit-Window'] = str(window)
        response['Retry-After'] = str(window)

        return response

    def _get_client_ip(self, request):
        """Extract real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')


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


