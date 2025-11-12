"""
Redis caching utilities for API responses
"""
from django.core.cache import cache


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
    cache.delete_many(cache_keys)
