"""
Custom throttling classes for Resee platform
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailRateThrottle(AnonRateThrottle):
    """Rate limiting for email-related operations"""
    scope = 'email'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class LoginRateThrottle(AnonRateThrottle):
    """Rate limiting for login attempts"""
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


class SubscriptionBasedThrottle(UserRateThrottle):
    """Base throttle that considers user subscription tier"""
    
    def allow_request(self, request, view):
        if not request.user.is_authenticated:
            return super().allow_request(request, view)
        
        # Get user's subscription tier
        subscription = getattr(request.user, 'subscription', None)
        if not subscription:
            self.scope = 'free'
        else:
            # Handle both string and object tier types
            if hasattr(subscription.tier, 'name'):
                tier = subscription.tier.name.lower()
            else:
                tier = str(subscription.tier).lower()
            self.scope = f"{self.base_scope}_{tier}"
        
        return super().allow_request(request, view)


class APIRateThrottle(SubscriptionBasedThrottle):
    """API rate limiting based on subscription tier"""
    base_scope = 'api'


class AIEndpointThrottle(SubscriptionBasedThrottle):
    """AI endpoint rate limiting based on subscription tier"""
    base_scope = 'ai'


class RegistrationRateThrottle(AnonRateThrottle):
    """Rate limiting for user registration"""
    scope = 'registration'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }