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