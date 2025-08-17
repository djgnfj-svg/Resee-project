"""
Custom throttling classes for Resee API endpoints
"""
import hashlib
import time

from django.core.cache import cache
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """
    Rate limiting for login attempts to prevent brute force attacks
    """
    scope = 'login'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class AIEndpointThrottle(UserRateThrottle):
    """
    Rate limiting for AI-related endpoints (expensive operations)
    Enhanced with tier-based limits and usage tracking
    """
    scope = 'ai'
    
    def allow_request(self, request, view):
        """
        Custom logic to allow higher limits for premium users
        """
        if not request.user.is_authenticated:
            # Anonymous users not allowed for AI endpoints
            return False
            
        # Get user's subscription tier and adjust limits
        tier_rates = {
            'PRO': '200/hour',
            'PREMIUM': '100/hour', 
            'BASIC': '50/hour',
            'FREE': '10/hour'
        }
        
        if hasattr(request.user, 'subscription'):
            tier = request.user.subscription.tier.upper()
            self.rate = tier_rates.get(tier, '10/hour')
        else:
            self.rate = '10/hour'  # Default for users without subscription
        
        # Check if user has exceeded their AI usage quota for the day
        from ai_review.models import AIUsageTracking
        
        try:
            usage = AIUsageTracking.get_daily_usage(request.user)
            if usage['used'] >= usage['limit']:
                # Daily AI quota exceeded
                return False
        except Exception:
            # If we can't check usage, allow the request
            pass
        
        return super().allow_request(request, view)
    
    def throttle_failure(self):
        """
        Custom throttle failure message with subscription info
        """
        return {
            'error': 'ai_rate_limit_exceeded',
            'message': 'AI 요청 한도를 초과했습니다. 더 높은 구독 플랜으로 업그레이드하세요.',
            'upgrade_url': '/subscription/upgrade/'
        }


class RegistrationRateThrottle(AnonRateThrottle):
    """
    Rate limiting for user registration to prevent spam
    """
    scope = 'register'
    
    def get_cache_key(self, request, view):
        # Use IP address for anonymous registration attempts
        ident = self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class UploadRateThrottle(UserRateThrottle):
    """
    Rate limiting for file upload endpoints
    """
    scope = 'upload'
    
    def allow_request(self, request, view):
        """
        Additional validation for upload size and type
        """
        if not super().allow_request(request, view):
            return False
        
        # Additional checks can be added here for file size, type, etc.
        return True


class EmailRateThrottle(AnonRateThrottle):
    """
    Rate limiting for email-related endpoints (verification, password reset)
    """
    scope = 'email'
    rate = '5/hour'
    
    def get_cache_key(self, request, view):
        # Combine IP and email for rate limiting
        ident = self.get_ident(request)
        email = request.data.get('email', '')
        
        if email:
            # Hash email to protect privacy
            email_hash = hashlib.md5(email.encode()).hexdigest()
            ident = f"{ident}:{email_hash}"
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class PerUserContentThrottle(UserRateThrottle):
    """
    Rate limiting for content creation per user
    """
    scope = 'content'
    rate = '100/hour'  # Users can create up to 100 pieces of content per hour
    
    def get_cache_key(self, request, view):
        return self.cache_format % {
            'scope': self.scope,
            'ident': request.user.pk
        }


class ReviewRateThrottle(UserRateThrottle):
    """
    Rate limiting for review completions to prevent gaming the system
    """
    scope = 'review'
    rate = '200/hour'  # Users can complete up to 200 reviews per hour
    
    def allow_request(self, request, view):
        """
        Allow unlimited reviews for premium users
        """
        if request.user.is_authenticated and hasattr(request.user, 'subscription'):
            if request.user.subscription.tier in ['PREMIUM', 'PRO']:
                return True  # No limit for premium users
        
        return super().allow_request(request, view)


class BurstUserRateThrottle(UserRateThrottle):
    """
    Rate limiting that allows short bursts but lower sustained rates
    """
    scope = 'burst'
    rate = '60/min'  # Allow 60 requests per minute for burst activity
    
    def __init__(self):
        super().__init__()
        # Also track hourly limits
        self.hourly_rate = '500/hour'
    
    def allow_request(self, request, view):
        # Check both minute and hourly limits
        minute_allowed = super().allow_request(request, view)
        
        if not minute_allowed:
            return False
        
        # Check hourly limit
        self.rate = self.hourly_rate
        hourly_allowed = super().allow_request(request, view)
        
        # Reset rate back to minute limit for next check
        self.rate = '60/min'
        
        return hourly_allowed


class SubscriptionTierThrottle(UserRateThrottle):
    """
    Dynamic rate limiting based on subscription tier
    """
    scope = 'tier_based'
    
    # Tier-based rate limits
    TIER_RATES = {
        'FREE': '500/hour',
        'BASIC': '1000/hour', 
        'PREMIUM': '2000/hour',
        'PRO': '5000/hour'
    }
    
    def allow_request(self, request, view):
        """
        Set rate limit based on user's subscription tier
        """
        if not request.user.is_authenticated:
            self.rate = '100/hour'  # Anonymous users
            return super().allow_request(request, view)
        
        # Get user's subscription tier
        tier = 'FREE'
        if hasattr(request.user, 'subscription'):
            tier = request.user.subscription.tier.upper()
        
        self.rate = self.TIER_RATES.get(tier, self.TIER_RATES['FREE'])
        return super().allow_request(request, view)


class PaymentEndpointThrottle(AnonRateThrottle):
    """
    Special rate limiting for payment endpoints (Stripe webhooks)
    """
    scope = 'payment'
    rate = '1000/hour'  # High limit for Stripe webhooks
    
    def get_cache_key(self, request, view):
        """
        Special handling for payment endpoints
        """
        # For Stripe webhooks, use a special identifier
        if 'webhook' in request.path:
            return f"payment:webhook:{self.get_ident(request)}"
        
        return super().get_cache_key(request, view)


class SlidingWindowThrottle(UserRateThrottle):
    """
    Sliding window rate limiter for more precise control
    """
    scope = 'sliding'
    rate = '100/hour'
    
    def __init__(self):
        super().__init__()
        self.window_size = 3600  # 1 hour in seconds
        self.request_limit = 100
    
    def allow_request(self, request, view):
        """
        Implement sliding window algorithm
        """
        if not request.user.is_authenticated:
            return super().allow_request(request, view)
        
        cache_key = f"sliding:{request.user.pk}"
        now = time.time()
        
        # Get request timestamps from cache
        request_times = cache.get(cache_key, [])
        
        # Remove timestamps outside the current window
        request_times = [t for t in request_times if now - t < self.window_size]
        
        # Check if limit exceeded
        if len(request_times) >= self.request_limit:
            return False
        
        # Add current request timestamp
        request_times.append(now)
        cache.set(cache_key, request_times, self.window_size + 60)  # TTL with buffer
        
        return True


class DynamicRateThrottle(UserRateThrottle):
    """
    Dynamic rate limiting that adjusts based on system load
    """
    scope = 'dynamic'
    base_rate = '1000/hour'
    
    def allow_request(self, request, view):
        """
        Adjust rate limit based on current system metrics
        """
        # Get current system load (simplified example)
        import psutil
        
        try:
            # Get CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            # Adjust rate based on system load
            if cpu_percent > 90 or memory_percent > 90:
                # High load: reduce rate limit by 50%
                self.rate = '500/hour'
            elif cpu_percent > 70 or memory_percent > 70:
                # Medium load: reduce rate limit by 25% 
                self.rate = '750/hour'
            else:
                # Normal load: use base rate
                self.rate = self.base_rate
                
        except Exception:
            # If we can't check system metrics, use base rate
            self.rate = self.base_rate
        
        return super().allow_request(request, view)


class GeographicRateThrottle(AnonRateThrottle):
    """
    Rate limiting based on geographic location
    """
    scope = 'geo'
    
    # Country-specific rate limits
    COUNTRY_RATES = {
        'KR': '2000/hour',  # South Korea - higher limit
        'US': '1000/hour',  # United States
        'JP': '1000/hour',  # Japan
        'DEFAULT': '500/hour'  # Other countries
    }
    
    def allow_request(self, request, view):
        """
        Set rate limit based on client's geographic location
        """
        # Get country code from request headers or IP geolocation
        country_code = self._get_country_code(request)
        self.rate = self.COUNTRY_RATES.get(country_code, self.COUNTRY_RATES['DEFAULT'])
        
        return super().allow_request(request, view)
    
    def _get_country_code(self, request):
        """
        Get country code from request
        """
        # Check CloudFlare header
        cf_country = request.META.get('HTTP_CF_IPCOUNTRY')
        if cf_country:
            return cf_country
        
        # Check other geolocation headers
        country = request.META.get('HTTP_X_COUNTRY_CODE')
        if country:
            return country
        
        # Default to unknown
        return 'DEFAULT'