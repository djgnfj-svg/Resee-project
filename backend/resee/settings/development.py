"""
Django development settings for resee project.
Settings specific to development environment.
"""

import os

from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-development-key-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allowed hosts for development
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'backend', '0.0.0.0']

# Database for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'resee_db'),
        'USER': os.environ.get('DB_USER', 'resee_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'resee_password'),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 60,
    }
}

# JWT Settings for development
SIMPLE_JWT['SIGNING_KEY'] = SECRET_KEY

# CORS Configuration for development (보안 강화)
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://frontend:3000",
]

# 개발환경에서는 HTTPS 관련 설정 비활성화
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Email Configuration for development
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '25'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'False') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@resee.com')

# Development-specific apps
DEVELOPMENT_APPS = [
    'django_extensions',
]
INSTALLED_APPS += DEVELOPMENT_APPS

# Development middleware
DEVELOPMENT_MIDDLEWARE = []
MIDDLEWARE += DEVELOPMENT_MIDDLEWARE

# Development-specific settings
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Email verification bypass for development
ENFORCE_EMAIL_VERIFICATION = os.environ.get('ENFORCE_EMAIL_VERIFICATION', 'False') == 'True'
EMAIL_VERIFICATION_TIMEOUT_DAYS = 3  # 이메일 인증 유효기간 (일)

# Development logging (less verbose)
LOGGING['loggers'] = {
    'django': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'django.db.backends': {
        'handlers': ['console'],
        'level': 'WARNING',  # Reduce SQL query logging
        'propagate': False,
    },
    'accounts': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'ai_review': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'review': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'content': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}

# Development-specific feature flags
FEATURE_FLAGS.update({
    'ENABLE_DEBUG_TOOLBAR': False,  # Set to True if you want to add debug toolbar
    'ENABLE_DETAILED_LOGGING': True,
})

# Disable rate limiting in development
RATE_LIMIT_ENABLE = False

# Override DRF throttling rates for development
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '10000/hour',     # Much higher for development
    'user': '10000/hour',     # Much higher for development  
    'login': '100/min',       # Higher for development
    'registration': '100/min', # Higher for development
    'register': '100/min',    # Higher for development
    'email': '1000/hour',     # Higher for development
    'ai_endpoint': '1000/hour', # Higher for development
}

# Development AI settings (with fallbacks)
AI_ENABLE_MOCK_RESPONSES = os.environ.get('AI_ENABLE_MOCK_RESPONSES', 'False') == 'True'

# Development caching (shorter timeouts)
CACHE_TIMEOUT_SHORT = 60  # 1 minute
CACHE_TIMEOUT_MEDIUM = 300  # 5 minutes
CACHE_TIMEOUT_LONG = 900  # 15 minutes

# Development security settings (relaxed)
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Development-specific settings
# Monitoring disabled for simplified setup

# Frontend URL for email links
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

# Google OAuth settings for development
GOOGLE_OAUTH2_CLIENT_ID = os.environ.get('GOOGLE_OAUTH2_CLIENT_ID')
GOOGLE_OAUTH2_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH2_CLIENT_SECRET')

# Stripe settings for development (test keys)
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
STRIPE_PRICE_ID_BASIC = os.environ.get('STRIPE_PRICE_ID_BASIC')
STRIPE_PRICE_ID_PREMIUM = os.environ.get('STRIPE_PRICE_ID_PREMIUM')
STRIPE_PRICE_ID_PRO = os.environ.get('STRIPE_PRICE_ID_PRO')

# Development environment validation
if not ANTHROPIC_API_KEY and not AI_ENABLE_MOCK_RESPONSES:
    import warnings
    warnings.warn("ANTHROPIC_API_KEY not set. AI features may not work.", UserWarning)

# Development environment configuration complete
# Google OAuth: Enabled if GOOGLE_OAUTH2_CLIENT_ID is set
# Email verification: Controlled by ENFORCE_EMAIL_VERIFICATION
# AI responses: Mock mode controlled by AI_ENABLE_MOCK_RESPONSES