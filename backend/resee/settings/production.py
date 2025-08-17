"""
Django production settings for resee project.
Settings specific to production environment.
"""

import os

from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required in production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Allowed hosts for production
ALLOWED_HOSTS = [
    'resee.com',
    'www.resee.com',
    '.amazonaws.com',  # ALB 도메인
    '.elb.amazonaws.com',  # ELB 도메인
]

# CloudFront 도메인 추가
cloudfront_domain = os.environ.get('CLOUDFRONT_DOMAIN')
if cloudfront_domain:
    ALLOWED_HOSTS.append(cloudfront_domain)

# Additional allowed hosts from environment
additional_hosts = os.environ.get('ADDITIONAL_ALLOWED_HOSTS', '')
if additional_hosts:
    ALLOWED_HOSTS.extend(additional_hosts.split(','))

# Database for production
DATABASES = {
    'default': dj_database_url.parse(
        os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True,
    )
}

if not os.environ.get('DATABASE_URL'):
    raise ValueError("DATABASE_URL environment variable is required in production")

# JWT Settings for production
SIMPLE_JWT['SIGNING_KEY'] = SECRET_KEY

# CORS Configuration for production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://resee.com",
    "https://www.resee.com",
]

# Add CloudFront domain to CORS if available
if cloudfront_domain:
    CORS_ALLOWED_ORIGINS.append(f"https://{cloudfront_domain}")

# Email Configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.aws.amazon.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

if not all([EMAIL_HOST_USER, EMAIL_HOST_PASSWORD]):
    print("WARNING: Email credentials not set. Email functionality may not work.")

# Production logging
LOGGING['handlers'].update({
    'file': {
        'level': 'ERROR',
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': '/var/log/django/error.log',
        'maxBytes': 1024*1024*50,  # 50MB
        'backupCount': 5,
        'formatter': 'verbose',
    },
})

LOGGING['formatters'] = {
    'verbose': {
        'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
        'style': '{',
    },
}

LOGGING['loggers'] = {
    'django': {
        'handlers': ['console', 'file'],
        'level': 'WARNING',
    },
    'django.security': {
        'handlers': ['console', 'file'],
        'level': 'ERROR',
        'propagate': False,
    },
    'accounts': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'ai_review': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'review': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'content': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'payments': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# Production security settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookie security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Production-specific middleware
PRODUCTION_MIDDLEWARE = [
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
]
MIDDLEWARE = PRODUCTION_MIDDLEWARE + MIDDLEWARE

# Production caching (longer timeouts)
CACHE_TIMEOUT_SHORT = 300  # 5 minutes
CACHE_TIMEOUT_MEDIUM = 1800  # 30 minutes
CACHE_TIMEOUT_LONG = 3600  # 1 hour

# Production-specific monitoring
MONITORING.update({
    'ENABLE_PERFORMANCE_TRACKING': True,
    'ENABLE_ERROR_TRACKING': True,
    'SLOW_QUERY_THRESHOLD': 0.5,  # Stricter in production
    'MEMORY_USAGE_THRESHOLD': 300,  # MB
})

# Production feature flags
FEATURE_FLAGS.update({
    'ENABLE_DEBUG_TOOLBAR': False,
    'ENABLE_DETAILED_LOGGING': False,
})

# Email verification is enforced in production
ENFORCE_EMAIL_VERIFICATION = True

# Google OAuth settings for production
GOOGLE_OAUTH2_CLIENT_ID = os.environ.get('GOOGLE_OAUTH2_CLIENT_ID')
GOOGLE_OAUTH2_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH2_CLIENT_SECRET')

if not all([GOOGLE_OAUTH2_CLIENT_ID, GOOGLE_OAUTH2_CLIENT_SECRET]):
    print("WARNING: Google OAuth credentials not set.")

# Stripe settings for production (live keys)
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
STRIPE_PRICE_ID_BASIC = os.environ.get('STRIPE_PRICE_ID_BASIC')
STRIPE_PRICE_ID_PREMIUM = os.environ.get('STRIPE_PRICE_ID_PREMIUM')
STRIPE_PRICE_ID_PRO = os.environ.get('STRIPE_PRICE_ID_PRO')

if not all([STRIPE_PUBLIC_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET]):
    print("WARNING: Stripe credentials not set. Payment functionality may not work.")

# AI Service validation
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is required in production")

# AWS S3 Configuration for production static/media files
if os.environ.get('USE_S3'):
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'ap-northeast-2')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'
    
    # Static files
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    
    # Media files
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }

# Production error monitoring integration
SENTRY_DSN = os.environ.get('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(auto_enabling=True),
            CeleryIntegration(auto_enabling=True),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment='production',
    )

print("Production environment loaded.")
print(f"Allowed hosts: {ALLOWED_HOSTS}")
print(f"Database: {DATABASES['default']['NAME']}")
print(f"Email backend: {EMAIL_BACKEND}")
print(f"Static files: {STATIC_URL}")
print(f"Media files: {MEDIA_URL}")