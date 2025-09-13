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


class QueryPerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor database query performance
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Get settings with defaults
        self.slow_query_threshold = getattr(settings, 'MONITORING', {}).get(
            'SLOW_QUERY_THRESHOLD', 1.0
        )
        self.query_count_threshold = 50
        self.enable_performance_tracking = getattr(settings, 'MONITORING', {}).get(
            'ENABLE_PERFORMANCE_TRACKING', True
        )
        super().__init__(get_response)

    def process_request(self, request):
        if not self.enable_performance_tracking:
            return

        # Reset query log and store initial state
        connection.queries_log.clear()
        request._start_time = time.time()
        request._start_queries = len(connection.queries)
        request._db_queries_start = list(connection.queries)

    def process_response(self, request, response):
        if not self.enable_performance_tracking:
            return response

        # Calculate metrics
        end_time = time.time()
        start_time = getattr(request, '_start_time', end_time)
        start_queries = getattr(request, '_start_queries', 0)

        total_time = end_time - start_time
        current_queries = connection.queries
        query_count = len(current_queries) - start_queries

        # Calculate query execution time
        query_time = 0.0
        slow_queries = []
        duplicate_queries = {}

        for query in current_queries[start_queries:]:
            query_exec_time = float(query.get('time', 0))
            query_time += query_exec_time

            # Track slow queries
            if query_exec_time > self.slow_query_threshold:
                slow_queries.append({
                    'sql': query['sql'][:200] + '...' if len(query['sql']) > 200 else query['sql'],
                    'time': query_exec_time
                })

            # Track duplicate queries
            sql = query['sql']
            if sql in duplicate_queries:
                duplicate_queries[sql] += 1
            else:
                duplicate_queries[sql] = 1

        # Find duplicate queries (N+1 problems)
        duplicates = {sql: count for sql, count in duplicate_queries.items() if count > 1}

        # Log performance metrics
        self._log_performance_metrics(
            request, response, total_time, query_count, query_time, slow_queries, duplicates
        )

        return response

    def _log_performance_metrics(self, request, response, total_time, query_count,
                                query_time, slow_queries, duplicates):
        """Log detailed performance metrics"""
        path = request.path
        method = request.method
        status_code = response.status_code
        user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None

        # Base metrics
        metrics = {
            'method': method,
            'path': path,
            'status_code': status_code,
            'total_time': round(total_time, 3),
            'query_count': query_count,
            'query_time': round(query_time, 3),
            'user_id': user_id,
        }

        # Log slow requests
        if total_time > self.slow_query_threshold:
            performance_logger.warning(
                f"SLOW_REQUEST: {method} {path} - "
                f"Time: {total_time:.3f}s, Queries: {query_count}, "
                f"Query Time: {query_time:.3f}s, Status: {status_code}, User: {user_id}",
                extra=metrics
            )

        # Log requests with too many queries (potential N+1 problems)
        if query_count > self.query_count_threshold:
            performance_logger.warning(
                f"HIGH_QUERY_COUNT: {method} {path} - "
                f"Queries: {query_count}, Time: {total_time:.3f}s, Status: {status_code}",
                extra=metrics
            )

        # Log slow individual queries
        for slow_query in slow_queries:
            performance_logger.warning(
                f"SLOW_QUERY: {method} {path} - "
                f"Time: {slow_query['time']:.3f}s, SQL: {slow_query['sql']}",
                extra={**metrics, 'sql': slow_query['sql'], 'sql_time': slow_query['time']}
            )

        # Log duplicate queries (N+1 indicators)
        for sql, count in duplicates.items():
            if count > 3:  # Only log if more than 3 duplicates
                performance_logger.warning(
                    f"DUPLICATE_QUERIES: {method} {path} - "
                    f"SQL executed {count} times: {sql[:100]}...",
                    extra={**metrics, 'duplicate_sql': sql[:100], 'duplicate_count': count}
                )

        # Log all API requests for analysis (info level)
        if path.startswith('/api/'):
            performance_logger.info(
                f"API_REQUEST: {method} {path} - "
                f"Time: {total_time:.3f}s, Queries: {query_count}, Status: {status_code}",
                extra=metrics
            )


class DatabaseHealthMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor database connection health and performance
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.connection_error_count = 0
        self.last_health_check = 0
        super().__init__(get_response)

    def process_request(self, request):
        current_time = time.time()

        # Perform health check every 60 seconds
        if current_time - self.last_health_check > 60:
            self._check_database_health()
            self.last_health_check = current_time

    def process_response(self, request, response):
        # Monitor database connection pool
        try:
            if hasattr(connection, 'connection') and connection.connection:
                # Add database health headers for monitoring
                response['X-Database-Status'] = 'healthy'

                # Monitor connection pool if available
                if hasattr(connection.connection, 'get_dsn_parameters'):
                    response['X-Database-Pool'] = 'postgresql'
        except Exception as e:
            performance_logger.error(f"Database connection error: {e}")
            response['X-Database-Status'] = 'unhealthy'

        return response

    def _check_database_health(self):
        """Perform basic database health check"""
        try:
            with connection.cursor() as cursor:
                start_time = time.time()
                cursor.execute("SELECT 1")
                query_time = time.time() - start_time

                # Log slow health checks
                if query_time > 1.0:
                    performance_logger.warning(
                        f"SLOW_DB_HEALTH_CHECK: {query_time:.3f}s",
                        extra={'health_check_time': query_time}
                    )

                # Reset error count on success
                self.connection_error_count = 0

        except Exception as e:
            self.connection_error_count += 1
            performance_logger.error(
                f"DATABASE_HEALTH_CHECK_FAILED: {e} (error count: {self.connection_error_count})",
                extra={'db_error_count': self.connection_error_count, 'error': str(e)}
            )


class MemoryUsageMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor memory usage during requests
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.memory_threshold = getattr(settings, 'MONITORING', {}).get(
            'MEMORY_USAGE_THRESHOLD', 500
        )  # 500MB threshold
        super().__init__(get_response)

    def process_request(self, request):
        try:
            import psutil
            process = psutil.Process()
            request._memory_start = process.memory_info().rss
        except ImportError:
            # psutil not available
            request._memory_start = None

    def process_response(self, request, response):
        if not hasattr(request, '_memory_start') or request._memory_start is None:
            return response

        try:
            import psutil
            process = psutil.Process()
            current_memory = process.memory_info().rss
            memory_used = (current_memory - request._memory_start) / 1024 / 1024  # MB

            # Log high memory usage requests
            if current_memory / 1024 / 1024 > self.memory_threshold:
                performance_logger.warning(
                    f"HIGH_MEMORY_USAGE: {request.method} {request.path} - "
                    f"Memory: {current_memory / 1024 / 1024:.1f}MB, "
                    f"Request usage: {memory_used:.1f}MB",
                    extra={
                        'memory_usage_mb': current_memory / 1024 / 1024,
                        'request_memory_mb': memory_used,
                        'path': request.path,
                        'method': request.method
                    }
                )

        except ImportError:
            pass

        return response