"""
Django testing settings for resee project.
Settings specific to testing environment.
"""

import logging

from .base import *

logger = logging.getLogger(__name__)

# Use a fast secret key for testing
SECRET_KEY = 'test-secret-key-not-for-production'

# Always use debug mode in tests
DEBUG = True

# Simple allowed hosts for testing
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

# Use in-memory SQLite database for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'OPTIONS': {
            'timeout': 20,
        },
        'TEST': {
            'NAME': ':memory:',
        },
    }
}

# JWT Settings for testing
SIMPLE_JWT['SIGNING_KEY'] = SECRET_KEY
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(minutes=30)  # Longer for tests

# Disable CORS restrictions in tests
CORS_ALLOW_ALL_ORIGINS = True

# Use console email backend for testing
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Disable email verification in tests
ENFORCE_EMAIL_VERIFICATION = False

# Use dummy cache for testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Email service runs synchronously (Celery removed)

# Testing-specific logging (minimal)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',  # Only show errors in tests
        },
        'django.db.backends': {
            'handlers': [],  # Disable SQL logging in tests
            'level': 'ERROR',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'ERROR',
    },
}

# Disable security features for testing
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Testing feature flags
FEATURE_FLAGS.update({
    'ENABLE_EXAMS': True,
    'ENABLE_ANALYTICS': True,
    'ENABLE_PAYMENT_SYSTEM': False,  # Disable payments in tests
    'ENABLE_DEBUG_TOOLBAR': False,
    'ENABLE_DETAILED_LOGGING': False,
})

# Mock OAuth settings for testing
GOOGLE_OAUTH2_CLIENT_ID = 'test-google-client-id'
GOOGLE_OAUTH2_CLIENT_SECRET = 'test-google-client-secret'

# Testing-specific monitoring (disabled)
# Note: MONITORING system was removed with monitoring app cleanup

# Faster password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Static files configuration for testing
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Disable migrations for faster tests


class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


# Disable problematic migrations in tests
MIGRATION_MODULES = {
    'content': None,
    'accounts': None,
    'review': None,
    'exams': None,
}

# Test-specific cache timeouts (very short)
CACHE_TIMEOUT_SHORT = 1
CACHE_TIMEOUT_MEDIUM = 1
CACHE_TIMEOUT_LONG = 1

# Subscription limits for testing (smaller numbers)
SUBSCRIPTION_SETTINGS = {
    'FREE_TIER_LIMITS': {
        'max_content': 5,
        'review_interval_days': 7,
    },
    'BASIC_TIER_LIMITS': {
        'max_content': 10,
        'review_interval_days': 30,
    },
    'PRO_TIER_LIMITS': {
        'max_content': -1,  # Unlimited
        'review_interval_days': 180,
    },
}

logger.info("Testing environment loaded.")
