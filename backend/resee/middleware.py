"""
Production security and monitoring middleware for Resee
"""
import logging
import time
from django.http import JsonResponse, HttpResponseForbidden
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
import re

logger = logging.getLogger(__name__)


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


class RateLimitMiddleware(MiddlewareMixin):
    """Rate limiting middleware for API endpoints"""
    
    RATE_LIMITS = {
        'login': {'limit': 5, 'window': 3600},  # 5 attempts per hour
        'register': {'limit': 3, 'window': 3600},  # 3 attempts per hour
        'api': {'limit': 1000, 'window': 3600},  # 1000 requests per hour
        'password_reset': {'limit': 3, 'window': 3600},  # 3 attempts per hour
    }
    
    def process_request(self, request):
        if not getattr(settings, 'RATE_LIMIT_ENABLE', False):
            return None
            
        # Determine rate limit type based on path
        rate_limit_type = self._get_rate_limit_type(request.path)
        if not rate_limit_type:
            return None
            
        # Get client IP
        client_ip = self._get_client_ip(request)
        cache_key = f"rate_limit:{rate_limit_type}:{client_ip}"
        
        # Check rate limit
        current_requests = cache.get(cache_key, 0)
        limit_config = self.RATE_LIMITS[rate_limit_type]
        
        if current_requests >= limit_config['limit']:
            logger.warning(f"Rate limit exceeded for {client_ip} on {rate_limit_type}")
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': '요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.'
            }, status=429)
        
        # Increment counter
        cache.set(cache_key, current_requests + 1, limit_config['window'])
        
        return None
    
    def _get_rate_limit_type(self, path):
        if '/api/auth/token/' in path:
            return 'login'
        elif '/api/accounts/users/register/' in path:
            return 'register'
        elif '/api/accounts/password-reset/' in path:
            return 'password_reset'
        elif path.startswith('/api/'):
            return 'api'
        return None
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


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