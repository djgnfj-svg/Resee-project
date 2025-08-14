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
    """Enhanced rate limiting middleware with tier-based limits"""
    
    # IP 기반 기본 제한
    DEFAULT_IP_LIMITS = {
        'minute': 100,    # 분당 100회
        'hour': 1000,     # 시간당 1000회 
        'day': 10000,     # 일당 10000회
    }
    
    # 구독 티어별 제한
    TIER_LIMITS = {
        'free': {
            'minute': 30,
            'hour': 500,
            'ai_hour': 10,
            'upload_hour': 5,
        },
        'basic': {
            'minute': 60,
            'hour': 1000,
            'ai_hour': 50,
            'upload_hour': 20,
        },
        'premium': {
            'minute': 120,
            'hour': 2000,
            'ai_hour': 100,
            'upload_hour': 50,
        },
        'pro': {
            'minute': 200,
            'hour': 5000,
            'ai_hour': 200,
            'upload_hour': 100,
        }
    }
    
    # 엔드포인트별 특별 제한
    ENDPOINT_LIMITS = {
        '/api/auth/token/': {'minute': 5, 'hour': 20},
        '/api/accounts/users/register/': {'hour': 3, 'day': 5},
        '/api/accounts/password-reset/': {'hour': 3, 'day': 10},
        '/api/ai-review/generate-questions/': {'minute': 2, 'hour': 20},
        '/api/payments/webhook/': {'minute': 100},  # Stripe webhook
    }
    
    # 화이트리스트 IP
    WHITELIST_IPS = ['127.0.0.1', '::1']
    
    def __init__(self, get_response):
        self.get_response = get_response
        # 화이트리스트 IP 로드
        admin_whitelist = getattr(settings, 'ADMIN_IP_WHITELIST', '')
        if admin_whitelist:
            if isinstance(admin_whitelist, str):
                self.WHITELIST_IPS.extend(admin_whitelist.split(','))
            else:
                self.WHITELIST_IPS.extend(admin_whitelist)
        super().__init__(get_response)
    
    def process_request(self, request):
        if not getattr(settings, 'RATE_LIMIT_ENABLE', True):
            return None
            
        client_ip = self._get_client_ip(request)
        
        # 화이트리스트 확인
        if client_ip in self.WHITELIST_IPS:
            return None
        
        # Health check, static files 제외
        if (request.path.startswith('/api/health/') or 
            request.path.startswith('/static/') or 
            request.path.startswith('/media/')):
            return None
        
        # 1. IP 기반 제한 확인
        ip_limit_result = self._check_ip_limits(request, client_ip)
        if ip_limit_result:
            return ip_limit_result
        
        # 2. 엔드포인트별 제한 확인  
        endpoint_limit_result = self._check_endpoint_limits(request, client_ip)
        if endpoint_limit_result:
            return endpoint_limit_result
        
        # 3. 사용자별 제한 확인 (인증된 사용자)
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_limit_result = self._check_user_limits(request)
            if user_limit_result:
                return user_limit_result
        
        return None
    
    def _check_ip_limits(self, request, client_ip):
        """IP 기반 제한 확인"""
        for period, limit in self.DEFAULT_IP_LIMITS.items():
            cache_key = f"rate_limit:ip:{client_ip}:{period}"
            window = {'minute': 60, 'hour': 3600, 'day': 86400}[period]
            
            if self._is_rate_limited(cache_key, limit, window):
                logger.warning(f"IP rate limit exceeded: {client_ip} - {period} limit")
                return self._create_rate_limit_response(
                    f"IP 기반 {period} 요청 한도를 초과했습니다.",
                    limit, window
                )
        return None
    
    def _check_endpoint_limits(self, request, client_ip):
        """엔드포인트별 제한 확인"""
        endpoint_limits = self.ENDPOINT_LIMITS.get(request.path)
        if not endpoint_limits:
            return None
            
        for period, limit in endpoint_limits.items():
            cache_key = f"rate_limit:endpoint:{client_ip}:{request.path}:{period}"
            window = {'minute': 60, 'hour': 3600, 'day': 86400}[period]
            
            if self._is_rate_limited(cache_key, limit, window):
                logger.warning(f"Endpoint rate limit exceeded: {client_ip} - {request.path}")
                return self._create_rate_limit_response(
                    f"이 엔드포인트의 {period} 요청 한도를 초과했습니다.",
                    limit, window
                )
        return None
    
    def _check_user_limits(self, request):
        """사용자별 제한 확인"""
        user = request.user
        tier = self._get_user_tier(user)
        tier_limits = self.TIER_LIMITS.get(tier, self.TIER_LIMITS['free'])
        
        # 일반 요청 제한
        for period in ['minute', 'hour']:
            if period not in tier_limits:
                continue
                
            cache_key = f"rate_limit:user:{user.id}:{period}"
            window = {'minute': 60, 'hour': 3600}[period]
            limit = tier_limits[period]
            
            if self._is_rate_limited(cache_key, limit, window):
                logger.warning(f"User rate limit exceeded: {user.id} ({tier}) - {period}")
                return self._create_rate_limit_response(
                    f"{tier} 구독 {period} 요청 한도를 초과했습니다.",
                    limit, window
                )
        
        # AI 요청 제한
        if '/ai-review/' in request.path:
            cache_key = f"rate_limit:user_ai:{user.id}:hour"
            limit = tier_limits.get('ai_hour', 10)
            
            if self._is_rate_limited(cache_key, limit, 3600):
                logger.warning(f"User AI rate limit exceeded: {user.id} ({tier})")
                return self._create_rate_limit_response(
                    f"{tier} 구독 AI 요청 한도를 초과했습니다. 구독을 업그레이드하세요.",
                    limit, 3600
                )
        
        # 파일 업로드 제한
        if request.method == 'POST' and ('upload' in request.path or 'files' in request.path):
            cache_key = f"rate_limit:user_upload:{user.id}:hour"
            limit = tier_limits.get('upload_hour', 5)
            
            if self._is_rate_limited(cache_key, limit, 3600):
                logger.warning(f"User upload rate limit exceeded: {user.id} ({tier})")
                return self._create_rate_limit_response(
                    f"{tier} 구독 업로드 한도를 초과했습니다.",
                    limit, 3600
                )
        
        return None
    
    def _is_rate_limited(self, cache_key, limit, window):
        """Rate limit 확인 및 카운터 증가"""
        try:
            current = cache.get(cache_key, 0)
            if current >= limit:
                return True
            
            # 카운터 증가
            cache.set(cache_key, current + 1, window)
            return False
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return False
    
    def _get_user_tier(self, user):
        """사용자 구독 티어 확인"""
        try:
            return user.subscription.tier.lower()
        except:
            return 'free'
    
    def _create_rate_limit_response(self, message, limit, window):
        """Rate limit 응답 생성"""
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
        """클라이언트 실제 IP 주소 추출 (AWS ALB 지원)"""
        # AWS ALB X-Forwarded-For 헤더
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        
        # CloudFlare CF-Connecting-IP
        cf_ip = request.META.get('HTTP_CF_CONNECTING_IP') 
        if cf_ip:
            return cf_ip
            
        return request.META.get('REMOTE_ADDR', '127.0.0.1')
    
    def process_response(self, request, response):
        """응답에 Rate Limit 헤더 추가"""
        if getattr(settings, 'RATE_LIMIT_ENABLE', True):
            # 현재 IP의 분당 제한 정보 추가
            client_ip = self._get_client_ip(request)
            cache_key = f"rate_limit:ip:{client_ip}:minute"
            
            try:
                current = cache.get(cache_key, 0)
                limit = self.DEFAULT_IP_LIMITS['minute']
                remaining = max(0, limit - current)
                
                response['X-RateLimit-Limit'] = str(limit)
                response['X-RateLimit-Remaining'] = str(remaining)
                response['X-RateLimit-Window'] = '60'
                
            except Exception as e:
                logger.error(f"Failed to add rate limit headers: {e}")
        
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