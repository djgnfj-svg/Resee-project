"""
Performance optimization utilities for Resee
"""
from django.db import models
from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


def cache_result(timeout=300, key_prefix='resee'):
    """
    Decorator to cache function results
    
    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        key_prefix: Cache key prefix
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            cache_key = f"{key_prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"
            
            # Try to get result from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cache miss for {func.__name__}, cached for {timeout}s")
            
            return result
        return wrapper
    return decorator


class OptimizedQueryMixin:
    """Mixin to add query optimization methods to ViewSets"""
    
    def get_queryset(self):
        """Override to add select_related and prefetch_related by default"""
        queryset = super().get_queryset()
        
        # Add common optimizations based on model
        if hasattr(self.serializer_class.Meta.model, 'user'):
            queryset = queryset.select_related('user')
        
        if hasattr(self.serializer_class.Meta.model, 'category'):
            queryset = queryset.select_related('category')
        
        return queryset


def optimize_content_queries(queryset):
    """Optimize Content model queries"""
    return queryset.select_related('user', 'category').prefetch_related('tags')


def optimize_review_queries(queryset):
    """Optimize Review model queries"""
    return queryset.select_related('user', 'content', 'content__category')


def optimize_analytics_queries(queryset):
    """Optimize analytics queries"""
    return queryset.select_related('user').prefetch_related(
        'content_set__category',
        'reviewhistory_set__content'
    )


class DatabaseOptimizer:
    """Database query optimization utilities"""
    
    @staticmethod
    def bulk_create_optimized(model_class, instances, batch_size=1000):
        """Optimized bulk create with batching"""
        if not instances:
            return []
            
        created_instances = []
        for i in range(0, len(instances), batch_size):
            batch = instances[i:i + batch_size]
            created_instances.extend(
                model_class.objects.bulk_create(batch, batch_size=batch_size)
            )
            logger.info(f"Bulk created {len(batch)} {model_class.__name__} instances")
        
        return created_instances
    
    @staticmethod
    def bulk_update_optimized(instances, fields, batch_size=1000):
        """Optimized bulk update with batching"""
        if not instances:
            return
            
        model_class = instances[0].__class__
        for i in range(0, len(instances), batch_size):
            batch = instances[i:i + batch_size]
            model_class.objects.bulk_update(batch, fields, batch_size=batch_size)
            logger.info(f"Bulk updated {len(batch)} {model_class.__name__} instances")


class CacheManager:
    """Centralized cache management"""
    
    # Cache timeouts (in seconds)
    TIMEOUTS = {
        'user_stats': 300,      # 5 minutes
        'category_stats': 600,   # 10 minutes
        'analytics': 1800,       # 30 minutes
        'review_schedule': 60,   # 1 minute
        'content_count': 300,    # 5 minutes
    }
    
    @classmethod
    def get_user_cache_key(cls, user_id, cache_type):
        """Generate user-specific cache key"""
        return f"user:{user_id}:{cache_type}"
    
    @classmethod
    def invalidate_user_cache(cls, user_id, cache_types=None):
        """Invalidate specific user cache entries"""
        if cache_types is None:
            cache_types = cls.TIMEOUTS.keys()
        
        keys_to_delete = [
            cls.get_user_cache_key(user_id, cache_type)
            for cache_type in cache_types
        ]
        
        cache.delete_many(keys_to_delete)
        logger.info(f"Invalidated cache for user {user_id}: {cache_types}")
    
    @classmethod
    def warm_user_cache(cls, user_id):
        """Pre-populate user cache with commonly accessed data"""
        from accounts.models import User
        from content.models import Content
        from review.models import ReviewSchedule
        
        try:
            user = User.objects.get(id=user_id)
            
            # Cache user stats
            content_count = Content.objects.filter(user=user).count()
            review_count = ReviewSchedule.objects.filter(user=user).count()
            
            cache.set(
                cls.get_user_cache_key(user_id, 'content_count'),
                content_count,
                cls.TIMEOUTS['content_count']
            )
            
            cache.set(
                cls.get_user_cache_key(user_id, 'review_count'),
                review_count,
                cls.TIMEOUTS['review_schedule']
            )
            
            logger.info(f"Warmed cache for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to warm cache for user {user_id}: {e}")


class PerformanceMiddleware:
    """Middleware to track and optimize performance"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Track database queries in development
        if settings.DEBUG:
            from django.db import connection, reset_queries
            reset_queries()
            
        response = self.get_response(request)
        
        if settings.DEBUG:
            # Log query count for development
            query_count = len(connection.queries)
            if query_count > 10:  # Warn if too many queries
                logger.warning(
                    f"High query count: {query_count} queries for {request.path}"
                )
        
        return response


# Database connection optimization
DATABASES_OPTIMIZED = {
    'default': {
        'CONN_MAX_AGE': 600,  # Connection pooling
        'OPTIONS': {
            'MAX_CONNS': 20,
            'conn_health_checks': True,
        }
    }
}

# Cache optimization settings
CACHES_OPTIMIZED = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 100,
                'health_check_interval': 30,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'resee',
        'TIMEOUT': 300,  # Default timeout: 5 minutes
    }
}

# Session optimization
SESSION_OPTIMIZED = {
    'SESSION_ENGINE': 'django.contrib.sessions.backends.cache',
    'SESSION_CACHE_ALIAS': 'default',
    'SESSION_COOKIE_AGE': 86400,  # 1 day
    'SESSION_EXPIRE_AT_BROWSER_CLOSE': True,
    'SESSION_SAVE_EVERY_REQUEST': False,  # Only save when modified
}

# Static files optimization for production
STATICFILES_OPTIMIZED = {
    'STATICFILES_STORAGE': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    'STATICFILES_FINDERS': [
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    ],
}

# Email optimization for production
EMAIL_OPTIMIZED = {
    'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
    'EMAIL_TIMEOUT': 10,  # 10 seconds timeout
    'EMAIL_USE_LOCALTIME': True,
}