"""
Custom middleware for security and monitoring
"""

import logging
import time
import json
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.utils import timezone
from ipware import get_client_ip

User = get_user_model()
logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """Add security headers to all responses"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Content Security Policy
        if not settings.DEBUG:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self';"
            )
            response['Content-Security-Policy'] = csp
        
        # HSTS (only in production with HTTPS)
        if not settings.DEBUG and request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response


class RateLimitMiddleware:
    """Rate limiting middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Rate limit configurations
        self.limits = {
            'login': {'requests': 5, 'window': 300},  # 5 requests per 5 minutes
            'api': {'requests': 100, 'window': 60},   # 100 requests per minute
            'upload': {'requests': 10, 'window': 300}, # 10 uploads per 5 minutes
        }

    def __call__(self, request):
        # Get client IP
        client_ip, is_routable = get_client_ip(request)
        if not client_ip:
            client_ip = 'unknown'
        
        # Determine rate limit type
        limit_type = self._get_limit_type(request)
        
        if limit_type and not self._check_rate_limit(client_ip, limit_type, request):
            logger.warning(f"Rate limit exceeded for IP {client_ip} on {request.path}")
            return JsonResponse({
                'error': 'Rate limit exceeded. Please try again later.',
                'retry_after': self.limits[limit_type]['window']
            }, status=429)
        
        response = self.get_response(request)
        
        # Add rate limit headers
        if limit_type:
            self._add_rate_limit_headers(response, client_ip, limit_type)
        
        return response
    
    def _get_limit_type(self, request):
        """Determine which rate limit to apply"""
        path = request.path.lower()
        
        if 'token' in path and request.method == 'POST':
            return 'login'
        elif 'upload' in path:
            return 'upload'
        elif path.startswith('/api/'):
            return 'api'
        
        return None
    
    def _check_rate_limit(self, client_ip, limit_type, request):
        """Check if request is within rate limit"""
        config = self.limits[limit_type]
        cache_key = f"rate_limit:{limit_type}:{client_ip}"
        
        # Get current count
        current_count = cache.get(cache_key, 0)
        
        # Check if limit exceeded
        if current_count >= config['requests']:
            return False
        
        # Increment counter
        cache.set(cache_key, current_count + 1, config['window'])
        
        return True
    
    def _add_rate_limit_headers(self, response, client_ip, limit_type):
        """Add rate limit headers to response"""
        config = self.limits[limit_type]
        cache_key = f"rate_limit:{limit_type}:{client_ip}"
        
        current_count = cache.get(cache_key, 0)
        remaining = max(0, config['requests'] - current_count)
        
        response['X-RateLimit-Limit'] = str(config['requests'])
        response['X-RateLimit-Remaining'] = str(remaining)
        response['X-RateLimit-Reset'] = str(int(time.time()) + config['window'])


class RequestLoggingMiddleware:
    """Log all requests for monitoring and security"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        # Get client info
        client_ip, is_routable = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        response = self.get_response(request)
        
        # Calculate response time
        duration = (time.time() - start_time) * 1000  # milliseconds
        
        # Log request details
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'response_time_ms': round(duration, 2),
            'client_ip': client_ip,
            'user_agent': user_agent[:200],  # Truncate long user agents
            'user': request.user.username if request.user.is_authenticated else 'anonymous',
            'content_length': len(response.content) if hasattr(response, 'content') else 0,
        }
        
        # Log security-relevant requests
        if (response.status_code >= 400 or 
            'login' in request.path.lower() or 
            'admin' in request.path.lower() or
            duration > 5000):  # Slow requests
            
            logger.info(f"Request: {json.dumps(log_data)}")
        
        # Log errors and security events separately
        if response.status_code >= 400:
            logger.warning(f"HTTP {response.status_code}: {request.method} {request.path} from {client_ip}")
        
        if response.status_code == 429:  # Rate limited
            logger.warning(f"Rate limit hit: {client_ip} on {request.path}")
        
        return response


class SQLInjectionDetectionMiddleware:
    """Basic SQL injection detection"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Common SQL injection patterns
        self.sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)",
            r"(\b(UNION|OR|AND)\s+\d+\s*=\s*\d+)",
            r"('|\"|`|;|--|\*|\/\*|\*\/)",
            r"(\b(SCRIPT|JAVASCRIPT|VBSCRIPT|ONLOAD|ONERROR|ONCLICK)\b)",
        ]

    def __call__(self, request):
        # Check query parameters and POST data
        suspicious_data = []
        
        # Check GET parameters
        for key, value in request.GET.items():
            if self._contains_sql_injection(value):
                suspicious_data.append(f"GET:{key}={value}")
        
        # Check POST data
        if hasattr(request, 'POST'):
            for key, value in request.POST.items():
                if self._contains_sql_injection(value):
                    suspicious_data.append(f"POST:{key}={value}")
        
        # Log suspicious activity
        if suspicious_data:
            client_ip, _ = get_client_ip(request)
            logger.critical(f"Potential SQL injection attempt from {client_ip}: {suspicious_data}")
            
            # In production, you might want to block the request
            if not settings.DEBUG:
                return JsonResponse({'error': 'Invalid request'}, status=400)
        
        return self.get_response(request)
    
    def _contains_sql_injection(self, value):
        """Check if value contains SQL injection patterns"""
        import re
        
        if not isinstance(value, str):
            return False
        
        value_lower = value.lower()
        
        for pattern in self.sql_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        
        return False


class LoginAttemptTrackingMiddleware:
    """Track failed login attempts"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Track failed login attempts
        if (request.path.endswith('/token/') and 
            request.method == 'POST' and 
            response.status_code == 401):
            
            self._track_failed_login(request)
        
        # Track successful logins
        elif (request.path.endswith('/token/') and 
              request.method == 'POST' and 
              response.status_code == 200):
            
            self._track_successful_login(request)
        
        return response
    
    def _track_failed_login(self, request):
        """Track failed login attempt"""
        client_ip, _ = get_client_ip(request)
        cache_key = f"failed_login:{client_ip}"
        
        # Get current count
        current_count = cache.get(cache_key, 0)
        new_count = current_count + 1
        
        # Store for 1 hour
        cache.set(cache_key, new_count, 3600)
        
        logger.warning(f"Failed login attempt #{new_count} from {client_ip}")
        
        # Alert on multiple failures
        if new_count >= 5:
            logger.critical(f"Multiple failed login attempts ({new_count}) from {client_ip}")
        
        # Extract username from request if possible
        try:
            if hasattr(request, 'POST') and 'username' in request.POST:
                username = request.POST['username']
                logger.warning(f"Failed login for username '{username}' from {client_ip}")
        except Exception:
            pass
    
    def _track_successful_login(self, request):
        """Track successful login"""
        client_ip, _ = get_client_ip(request)
        
        # Clear failed attempts on successful login
        cache_key = f"failed_login:{client_ip}"
        cache.delete(cache_key)
        
        # Log successful login
        try:
            if hasattr(request, 'POST') and 'username' in request.POST:
                username = request.POST['username']
                logger.info(f"Successful login for username '{username}' from {client_ip}")
        except Exception:
            pass


class IPWhitelistMiddleware:
    """IP whitelist for admin access (if needed)"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Admin IP whitelist (configure in settings)
        self.admin_whitelist = getattr(settings, 'ADMIN_IP_WHITELIST', [])

    def __call__(self, request):
        # Check admin access
        if (request.path.startswith('/admin/') and 
            self.admin_whitelist and 
            not settings.DEBUG):
            
            client_ip, _ = get_client_ip(request)
            
            if client_ip not in self.admin_whitelist:
                logger.critical(f"Unauthorized admin access attempt from {client_ip}")
                return JsonResponse({'error': 'Access denied'}, status=403)
        
        return self.get_response(request)


class ContentTypeValidationMiddleware:
    """Validate request content types"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Allowed content types for API endpoints
        self.allowed_content_types = [
            'application/json',
            'application/x-www-form-urlencoded',
            'multipart/form-data',
            'text/plain',
        ]

    def __call__(self, request):
        # Validate content type for API requests
        if (request.path.startswith('/api/') and 
            request.method in ['POST', 'PUT', 'PATCH'] and
            request.content_type):
            
            content_type = request.content_type.split(';')[0].strip()
            
            if content_type not in self.allowed_content_types:
                logger.warning(f"Invalid content type '{content_type}' from {get_client_ip(request)[0]}")
                return JsonResponse({'error': 'Invalid content type'}, status=400)
        
        return self.get_response(request)


class FileUploadSecurityMiddleware:
    """Security for file uploads"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Allowed file extensions
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        
        # Max file size (10MB)
        self.max_file_size = 10 * 1024 * 1024

    def __call__(self, request):
        # Check file uploads
        if request.method in ['POST', 'PUT'] and request.FILES:
            for file_field, uploaded_file in request.FILES.items():
                if not self._validate_file(uploaded_file, request):
                    client_ip, _ = get_client_ip(request)
                    logger.warning(f"Invalid file upload from {client_ip}: {uploaded_file.name}")
                    return JsonResponse({'error': 'Invalid file'}, status=400)
        
        return self.get_response(request)
    
    def _validate_file(self, uploaded_file, request):
        """Validate uploaded file"""
        import os
        import magic
        
        # Check file size
        if uploaded_file.size > self.max_file_size:
            return False
        
        # Check file extension
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        if file_ext not in self.allowed_extensions:
            return False
        
        # Check MIME type using python-magic
        try:
            mime_type = magic.from_buffer(uploaded_file.read(1024), mime=True)
            uploaded_file.seek(0)  # Reset file pointer
            
            allowed_mime_types = {
                'image/jpeg', 'image/png', 'image/gif', 'image/webp'
            }
            
            if mime_type not in allowed_mime_types:
                return False
                
        except Exception as e:
            logger.error(f"Error checking file MIME type: {e}")
            return False
        
        return True