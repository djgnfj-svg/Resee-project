"""
Test settings for Resee backend
"""

import os
import tempfile

from resee.settings import *

# Test database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Test email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Test media storage
MEDIA_ROOT = tempfile.mkdtemp()

# Test static files
STATIC_ROOT = tempfile.mkdtemp()

# Disable caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Test Celery settings
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

# Speed up password hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable logging during tests
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
            'level': 'WARNING',
        },
    },
}

# Test timezone
TIME_ZONE = 'UTC'
USE_TZ = True

# Review intervals for testing
REVIEW_INTERVALS = [1, 3, 7, 14, 30]

# Test secret key
SECRET_KEY = 'test-secret-key-for-testing-only'

# Debug mode for tests
DEBUG = True

# Test allowed hosts
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']