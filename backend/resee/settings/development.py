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

# CORS Configuration for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://frontend:3000",
]

# Email Configuration for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

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

# Development-specific monitoring
MONITORING.update({
    'ENABLE_PERFORMANCE_TRACKING': True,
    'ENABLE_ERROR_TRACKING': True,
    'SLOW_QUERY_THRESHOLD': 2.0,  # More lenient in development
})

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
    print("WARNING: ANTHROPIC_API_KEY not set. AI features may not work.")

if not GOOGLE_OAUTH2_CLIENT_ID:
    print("WARNING: GOOGLE_OAUTH2_CLIENT_ID not set. Google OAuth will not work.")

print(f"Development environment loaded. DEBUG={DEBUG}")
print(f"Database: {DATABASES['default']['NAME']}@{DATABASES['default']['HOST']}")
print(f"Email verification enforced: {ENFORCE_EMAIL_VERIFICATION}")
print(f"AI mock responses: {AI_ENABLE_MOCK_RESPONSES}")