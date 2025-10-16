"""
Custom throttling classes for Resee platform using Redis cache.
"""
from django.core.cache import caches
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle, ScopedRateThrottle
from django.contrib.auth import get_user_model

User = get_user_model()


class RedisThrottleMixin:
    """Mixin to use Redis cache for throttling."""

    cache_name = 'throttle'

    def get_cache(self):
        """Get the Redis throttle cache."""
        return caches[self.cache_name]


class RedisAnonRateThrottle(RedisThrottleMixin, AnonRateThrottle):
    """
    Throttle for anonymous requests using Redis cache.
    Limits requests from unauthenticated users by IP address.
    """
    cache = property(RedisThrottleMixin.get_cache)


class RedisUserRateThrottle(RedisThrottleMixin, UserRateThrottle):
    """
    Throttle for authenticated requests using Redis cache.
    Limits requests from authenticated users by user ID.
    """
    cache = property(RedisThrottleMixin.get_cache)


class EmailRateThrottle(RedisThrottleMixin, AnonRateThrottle):
    """Rate limiting for email-related operations using Redis"""
    scope = 'email'
    cache = property(RedisThrottleMixin.get_cache)

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class LoginRateThrottle(RedisThrottleMixin, AnonRateThrottle):
    """Rate limiting for login attempts using Redis"""
    scope = 'login'
    cache = property(RedisThrottleMixin.get_cache)

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class SubscriptionBasedThrottle(RedisThrottleMixin, UserRateThrottle):
    """Base throttle that considers user subscription tier using Redis"""
    cache = property(RedisThrottleMixin.get_cache)

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


class RegistrationRateThrottle(RedisThrottleMixin, AnonRateThrottle):
    """Rate limiting for user registration using Redis"""
    scope = 'registration'
    cache = property(RedisThrottleMixin.get_cache)

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }