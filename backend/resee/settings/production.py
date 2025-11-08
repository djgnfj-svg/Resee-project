"""
Production settings for Resee
"""
import os
import dj_database_url
from .base import *

# Security settings - SECRET_KEY is mandatory in production
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required in production")

# JWT Settings for production
SIMPLE_JWT['SIGNING_KEY'] = SECRET_KEY

# Debug settings
DEBUG = False
TEMPLATE_DEBUG = False

# Security settings
# Monkey-patch Django's validate_host to support VPC IP validation
from django.http import request as django_request

_original_validate_host = django_request.validate_host

def validate_host_with_vpc(host, allowed_hosts):
    """
    Custom validate_host that allows:
    1. All patterns supported by Django's original validate_host
    2. VPC private IPs (172.31.0.0/16) for ALB health checks
    3. localhost for local testing
    """
    # Check for VPC private IPs (172.31.0.0/16)
    if host.startswith('172.31.'):
        return True

    # Check for localhost
    if host in ['localhost', '127.0.0.1']:
        return True

    # Fall back to Django's original validation
    return _original_validate_host(host, allowed_hosts)

# Replace Django's validate_host with our custom version
django_request.validate_host = validate_host_with_vpc

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')

# Add api subdomain to allowed hosts if not already present
if 'api.reseeall.com' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('api.reseeall.com')

# Add api subdomain to CSRF trusted origins
if 'https://api.reseeall.com' not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append('https://api.reseeall.com')

# CORS settings for production
CORS_ALLOWED_ORIGINS = [
    "https://reseeall.com",
    "https://www.reseeall.com",
]

# Allow Vercel preview deployments (for PR previews)
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",
]

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# SSL settings for production (CloudFlare handles SSL termination)
SECURE_SSL_REDIRECT = False  # CloudFlare handles SSL, don't redirect at Django level
SECURE_PROXY_SSL_HEADER = ('HTTP_CF_VISITOR', '{"scheme":"https"}')
SESSION_COOKIE_SECURE = True  # Only send session cookies over HTTPS
CSRF_COOKIE_SECURE = True    # Only send CSRF cookies over HTTPS

# CloudFlare specific headers
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Database configuration will be set at the end of this file

# Cache settings - Local Memory Cache for general use + Redis for rate limiting
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'resee-prod-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 5000,  # More entries for production
            'CULL_FREQUENCY': 4,
        },
        'KEY_PREFIX': 'resee_prod',
        'TIMEOUT': 300,
        'VERSION': 1,
    },
    # Redis cache for rate limiting
    'throttle': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'throttle',
        'TIMEOUT': 3600,  # 1 hour default
    },
    # Redis cache for API responses
    'api': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/1'),  # Database 1
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'api',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Session settings - Database Backend (No Redis needed)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 1 day
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = '/app/static'
STATICFILES_DIRS = []  # Clear STATICFILES_DIRS in production to avoid conflict with STATIC_ROOT
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = '/app/media'

# Email settings
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')


# Email verification settings for production
ENFORCE_EMAIL_VERIFICATION = os.environ.get('ENFORCE_EMAIL_VERIFICATION', 'True') == 'True'
EMAIL_VERIFICATION_TIMEOUT_DAYS = 1  # 이메일 인증 유효기간 (일)

# Frontend URL for email links
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://reseeall.com')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/app/logs/django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.environ.get('LOG_LEVEL', 'INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.environ.get('LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'resee': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Performance settings
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Rate limiting (more restrictive in production)
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '100/hour',
    'user': '1000/hour',
    'login': '5/minute',
    'registration': '3/minute',
    'email': '10/hour',
}

# Disable DRF Browsable API in production (JSON only)
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
]

# Monitoring removed - using logging + Slack alerts instead

# DATABASE CONFIGURATION - Local PostgreSQL
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=300,
        conn_health_checks=True,
    )
}

# PostgreSQL 최적화 옵션
DATABASES['default']['OPTIONS'] = {
    'connect_timeout': 10,
}