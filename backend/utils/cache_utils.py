"""
Redis caching utilities for API responses
"""
from django.core.cache import caches
from functools import wraps
import hashlib
import json


def get_api_cache():
    """Get the API cache backend"""
    return caches['api']


def generate_cache_key(prefix, *args, **kwargs):
    """
    Generate a cache key from prefix and arguments

    Args:
        prefix: Cache key prefix (e.g., 'review:today')
        *args: Positional arguments to include in key
        **kwargs: Keyword arguments to include in key

    Returns:
        str: Cache key (e.g., 'api:review:today:123')
    """
    # Convert args and kwargs to string
    key_parts = [str(arg) for arg in args]

    # Sort kwargs for consistent key generation
    for k in sorted(kwargs.keys()):
        key_parts.append(f"{k}={kwargs[k]}")

    # Join all parts
    key_data = ":".join(key_parts)

    # For long keys, use hash
    if len(key_data) > 200:
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{key_hash}"

    return f"{prefix}:{key_data}" if key_data else prefix


def cache_response(cache_key_func=None, timeout=300):
    """
    Decorator to cache API responses

    Args:
        cache_key_func: Function to generate cache key from request
        timeout: Cache TTL in seconds (default: 5 minutes)

    Example:
        @cache_response(
            cache_key_func=lambda request: f'review:today:{request.user.id}',
            timeout=3600
        )
        def get(self, request):
            # ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # Skip caching for non-GET requests
            if request.method != 'GET':
                return func(self, request, *args, **kwargs)

            # Generate cache key
            if cache_key_func:
                cache_key = cache_key_func(request, *args, **kwargs)
            else:
                # Default: use view name + user ID
                cache_key = f"{func.__name__}:{request.user.id if request.user.is_authenticated else 'anon'}"

            # Try to get from cache
            cache = get_api_cache()
            cached_response = cache.get(cache_key)

            if cached_response is not None:
                return cached_response

            # Call the actual view
            response = func(self, request, *args, **kwargs)

            # Cache successful responses only (200-299)
            if 200 <= response.status_code < 300:
                cache.set(cache_key, response, timeout=timeout)

            return response

        return wrapper
    return decorator


def invalidate_cache(*cache_keys):
    """
    Invalidate multiple cache keys

    Args:
        *cache_keys: Cache keys to delete

    Example:
        invalidate_cache(
            f'review:today:{user_id}',
            f'analytics:stats:{user_id}'
        )
    """
    cache = get_api_cache()
    cache.delete_many(cache_keys)


def invalidate_pattern(pattern):
    """
    Invalidate all cache keys matching a pattern

    Args:
        pattern: Redis pattern (e.g., 'review:*')

    Example:
        invalidate_pattern(f'content:user:{user_id}:*')
    """
    cache = get_api_cache()

    # django-redis specific method
    if hasattr(cache, 'delete_pattern'):
        cache.delete_pattern(f"api:{pattern}")


class CacheInvalidationMixin:
    """
    Mixin to automatically invalidate cache on create/update/delete

    Usage:
        class ContentCreateView(CacheInvalidationMixin, APIView):
            cache_patterns_to_invalidate = [
                lambda self, request, obj: f'content:user:{request.user.id}:*',
                lambda self, request, obj: f'content:list:*',
            ]
    """
    cache_patterns_to_invalidate = []

    def invalidate_related_caches(self, request, obj=None):
        """Invalidate caches based on patterns"""
        for pattern_func in self.cache_patterns_to_invalidate:
            pattern = pattern_func(self, request, obj)
            invalidate_pattern(pattern)


# Specific cache key generators
def review_today_cache_key(request, *args, **kwargs):
    """Cache key for today's review list"""
    return f'review:today:{request.user.id}'


def content_list_cache_key(request, *args, **kwargs):
    """Cache key for content list with pagination"""
    page = request.query_params.get('page', 1)
    category = request.query_params.get('category', '')
    search = request.query_params.get('search', '')

    return generate_cache_key(
        f'content:list:{request.user.id}',
        page=page,
        category=category,
        search=search
    )


def analytics_stats_cache_key(request, *args, **kwargs):
    """Cache key for analytics stats"""
    return f'analytics:stats:{request.user.id}'
