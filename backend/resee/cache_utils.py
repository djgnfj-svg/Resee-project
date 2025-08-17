"""
Cache utilities for improved performance
"""
import json
import hashlib
from functools import wraps
from django.core.cache import cache
from django.conf import settings


def cache_key_generator(*args, **kwargs):
    """
    Generate a cache key from function arguments
    """
    key_data = json.dumps(args + tuple(sorted(kwargs.items())), default=str, sort_keys=True)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached_method(timeout=None, key_prefix=None):
    """
    Decorator for caching method results
    
    Args:
        timeout: Cache timeout in seconds (default from settings)
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Skip caching in tests or if cache is disabled
            if getattr(settings, 'TESTING', False) or not getattr(settings, 'USE_CACHE', True):
                return func(*args, **kwargs)
            
            # Generate cache key
            func_name = f"{func.__module__}.{func.__qualname__}"
            if key_prefix:
                func_name = f"{key_prefix}.{func_name}"
            
            cache_key = f"{func_name}:{cache_key_generator(*args, **kwargs)}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_timeout = timeout or getattr(settings, 'CACHE_TIMEOUT_MEDIUM', 1800)
            cache.set(cache_key, result, cache_timeout)
            
            return result
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern):
    """
    Invalidate cache keys matching a pattern
    """
    try:
        # This is a simplified version - in production you might want
        # to use a more sophisticated cache invalidation strategy
        cache.clear()
    except Exception:
        pass


class CacheManager:
    """
    Helper class for managing cache operations
    """
    
    @staticmethod
    def get_user_cache_key(user_id, cache_type):
        """
        Generate user-specific cache key
        """
        return f"user:{user_id}:{cache_type}"
    
    @staticmethod
    def get_content_cache_key(content_id, cache_type):
        """
        Generate content-specific cache key
        """
        return f"content:{content_id}:{cache_type}"
    
    @staticmethod
    def invalidate_user_cache(user_id):
        """
        Invalidate all cache for a specific user
        """
        patterns = [
            f"user:{user_id}:*",
            f"*:user:{user_id}:*",
        ]
        for pattern in patterns:
            try:
                cache.delete_pattern(pattern)
            except (AttributeError, NotImplementedError):
                # Fallback if cache backend doesn't support pattern deletion
                cache.clear()
                break
    
    @staticmethod
    def invalidate_content_cache(content_id):
        """
        Invalidate all cache for specific content
        """
        patterns = [
            f"content:{content_id}:*",
            f"*:content:{content_id}:*",
        ]
        for pattern in patterns:
            try:
                cache.delete_pattern(pattern)
            except (AttributeError, NotImplementedError):
                cache.clear()
                break
    
    @staticmethod
    def cache_review_data(user_id, data, timeout=None):
        """
        Cache review-related data for user
        """
        cache_key = CacheManager.get_user_cache_key(user_id, 'review_data')
        cache_timeout = timeout or getattr(settings, 'CACHE_TIMEOUT_SHORT', 300)
        cache.set(cache_key, data, cache_timeout)
    
    @staticmethod
    def get_cached_review_data(user_id):
        """
        Get cached review data for user
        """
        cache_key = CacheManager.get_user_cache_key(user_id, 'review_data')
        return cache.get(cache_key)
    
    @staticmethod
    def cache_ai_questions(content_id, questions, timeout=None):
        """
        Cache AI questions for content
        """
        cache_key = CacheManager.get_content_cache_key(content_id, 'ai_questions')
        cache_timeout = timeout or getattr(settings, 'CACHE_TIMEOUT_LONG', 3600)
        cache.set(cache_key, questions, cache_timeout)
    
    @staticmethod
    def get_cached_ai_questions(content_id):
        """
        Get cached AI questions for content
        """
        cache_key = CacheManager.get_content_cache_key(content_id, 'ai_questions')
        return cache.get(cache_key)