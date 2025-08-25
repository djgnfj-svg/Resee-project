"""
Caching utilities for the Resee application
"""
import hashlib
import json
from functools import wraps
from django.core.cache import cache
from django.conf import settings


class CacheManager:
    """Cache management utility class"""
    
    DEFAULT_TIMEOUT = 300  # 5 minutes
    
    @staticmethod
    def get_cache_key(prefix, *args, **kwargs):
        """Generate cache key from arguments"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @staticmethod
    def set_cache(key, value, timeout=None):
        """Set cache value"""
        if timeout is None:
            timeout = CacheManager.DEFAULT_TIMEOUT
        
        try:
            cache.set(key, value, timeout)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_cache(key, default=None):
        """Get cache value"""
        try:
            return cache.get(key, default)
        except Exception:
            return default
    
    @staticmethod
    def delete_cache(key):
        """Delete cache value"""
        try:
            cache.delete(key)
            return True
        except Exception:
            return False
    
    @staticmethod
    def clear_pattern(pattern):
        """Clear cache entries matching pattern"""
        try:
            cache.delete_many(cache.keys(pattern))
            return True
        except Exception:
            return False


def cached_method(timeout=None, key_prefix=''):
    """
    Decorator for caching method results
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate cache key
            cache_key = CacheManager.get_cache_key(
                f"{key_prefix}{self.__class__.__name__}.{func.__name__}",
                self.pk if hasattr(self, 'pk') else str(self),
                *args, **kwargs
            )
            
            # Try to get from cache
            result = CacheManager.get_cache(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(self, *args, **kwargs)
            CacheManager.set_cache(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def cached_function(timeout=None, key_prefix=''):
    """
    Decorator for caching function results
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = CacheManager.get_cache_key(
                f"{key_prefix}{func.__name__}",
                *args, **kwargs
            )
            
            # Try to get from cache
            result = CacheManager.get_cache(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            CacheManager.set_cache(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def invalidate_cache_on_save(sender, instance, **kwargs):
    """
    Django signal handler to invalidate cache on model save
    """
    model_name = sender.__name__.lower()
    CacheManager.clear_pattern(f"*{model_name}*")


def invalidate_cache_on_delete(sender, instance, **kwargs):
    """
    Django signal handler to invalidate cache on model delete
    """
    model_name = sender.__name__.lower()
    CacheManager.clear_pattern(f"*{model_name}*")