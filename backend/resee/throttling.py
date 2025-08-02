"""
Custom throttling classes for Resee API endpoints
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.core.cache import cache
import hashlib
import time


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
    """
    scope = 'ai'
    
    def allow_request(self, request, view):
        """
        Custom logic to allow higher limits for premium users
        """
        if request.user.is_authenticated:
            # Check user's subscription tier and adjust limits
            if hasattr(request.user, 'subscription'):
                subscription = request.user.subscription
                if subscription.tier == 'PRO':
                    self.rate = '200/hour'  # Higher limit for PRO users
                elif subscription.tier == 'PREMIUM':
                    self.rate = '100/hour'  # Higher limit for PREMIUM users
                elif subscription.tier == 'BASIC':
                    self.rate = '50/hour'   # Default AI limit
                else:
                    self.rate = '10/hour'   # Limited for FREE users
            else:
                self.rate = '10/hour'       # Default for users without subscription
        
        return super().allow_request(request, view)


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