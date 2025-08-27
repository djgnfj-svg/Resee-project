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

# Allowed hosts for production (flexible for beta)
ALLOWED_HOSTS = [
    host.strip() 
    for host in os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')
    if host.strip()
]

# Database for production (RDS)
if 'DATABASE_URL' in os.environ:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(os.environ['DATABASE_URL'])
    }
    DATABASES['default']['CONN_MAX_AGE'] = 600  # 10 minutes for AWS RDS
    DATABASES['default']['OPTIONS'] = {
        'MAX_CONNS': 20,
        'charset': 'utf8mb4',
        'init_command': 'SET sql_mode="STRICT_TRANS_TABLES"',
        'isolation_level': 'read committed',
    }
else:
    raise ValueError("DATABASE_URL environment variable is required in production")

# JWT Settings for production
SIMPLE_JWT['SIGNING_KEY'] = SECRET_KEY

# CORS Configuration for production (flexible for beta)
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    origin.strip() 
    for origin in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
    if origin.strip()
]

CORS_ALLOW_CREDENTIALS = True

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

# Production security settings (flexible for beta)
# Only enable HTTPS settings if specified
if os.environ.get('USE_HTTPS', 'false').lower() == 'true':
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_SSL_REDIRECT = False
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookie security (flexible for beta)
SESSION_COOKIE_SECURE = os.environ.get('USE_HTTPS', 'false').lower() == 'true'
CSRF_COOKIE_SECURE = os.environ.get('USE_HTTPS', 'false').lower() == 'true'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Additional security headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'DENY'

# Production-specific middleware
MIDDLEWARE.insert(1, 'django.middleware.security.SecurityMiddleware')
MIDDLEWARE.insert(2, 'whitenoise.middleware.WhiteNoiseMiddleware')
MIDDLEWARE.insert(3, 'resee.middleware.SecurityHeadersMiddleware')
MIDDLEWARE.insert(4, 'resee.middleware.RateLimitMiddleware')
MIDDLEWARE.insert(-1, 'resee.middleware.RequestLoggingMiddleware')
MIDDLEWARE.insert(-1, 'resee.middleware.SQLInjectionDetectionMiddleware')

# Enhanced rate limiting for production
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'].update({
    'anon': '50/hour',  # Stricter for production
    'user': '500/hour',  # Reasonable limit
    'login': '3/min',   # Stricter login attempts
    'registration': '2/min',  # Stricter registration
    'register': '2/min',
    'email': '5/hour',  # Stricter email sending
    'ai_endpoint': '30/hour',  # Stricter AI usage
})

# Static files configuration for production (without S3)
if not os.environ.get('USE_S3'):
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    
    # WhiteNoise settings
    WHITENOISE_USE_FINDERS = True
    WHITENOISE_AUTOREFRESH = False
    WHITENOISE_STATIC_PREFIX = '/static/'

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

# Security settings for beta deployment
ENVIRONMENT = 'production'
RATE_LIMIT_ENABLE = os.environ.get('RATE_LIMIT_ENABLE', 'true').lower() == 'true'
ADMIN_IP_WHITELIST = os.environ.get('ADMIN_IP_WHITELIST', '').split(',') if os.environ.get('ADMIN_IP_WHITELIST') else []

# File upload security
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Enhanced password validation
AUTH_PASSWORD_VALIDATORS.extend([
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8}
    },
])

# Session security
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

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
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')

if AWS_STORAGE_BUCKET_NAME and AWS_ACCESS_KEY_ID:
    # CloudFront or direct S3 domain
    AWS_S3_CUSTOM_DOMAIN = os.environ.get('AWS_S3_CUSTOM_DOMAIN')
    if not AWS_S3_CUSTOM_DOMAIN:
        AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    
    # Static files
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    
    # Media files
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    
    # S3 Settings
    AWS_DEFAULT_ACL = None  # Use bucket policy instead
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = False
    
    # Performance optimizations
    AWS_S3_MAX_MEMORY_SIZE = 128 * 1024 * 1024  # 128MB
    AWS_S3_USE_THREADS = True
    
else:
    # Fallback to local static files
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

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