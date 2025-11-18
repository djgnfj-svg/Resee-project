"""
Django base settings for resee project.
Common settings that apply to all environments.
"""

import os
from datetime import timedelta
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # JWT token blacklist support
    'corsheaders',
    'django_filters',
    'drf_yasg',
    'django_celery_beat',

    # Local apps
    'accounts',  # includes legal functionality
    'content',
    'review',  # includes review scheduling and dashboard analytics
    'exams',  # exam functionality (previously weekly_test)
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'resee.middleware.SecurityHeadersMiddleware',  # Security headers
    'resee.middleware.RequestLoggingMiddleware',  # Request logging
]

ROOT_URLCONF = 'resee.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'resee.wsgi.application'


# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'accounts.auth.authentication.EmailOrUsernameModelBackend',  # Custom email/username backend
    'django.contrib.auth.backends.ModelBackend',  # Default backend
]


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Static files configuration for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'resee.throttling.RedisAnonRateThrottle',
        'resee.throttling.RedisUserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '5/min',
        'registration': '3/min',
        'register': '3/min',
        'email': '10/hour',
    },
    'EXCEPTION_HANDLER': 'resee.exception_handlers.custom_exception_handler',
}


# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    # Security: Check if token is blacklisted on each request
    'CHECK_REVOKE_TOKEN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': None,  # Will be set in environment-specific settings
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}


# Email Configuration (base settings)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@localhost')

# Email content settings (used by EmailService)
COMPANY_NAME = os.environ.get('COMPANY_NAME', 'Resee')
SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'support@localhost')

# Email verification settings
try:
    EMAIL_VERIFICATION_TIMEOUT_DAYS = int(os.environ.get('EMAIL_VERIFICATION_TIMEOUT_DAYS', 1))
except (ValueError, TypeError):
    EMAIL_VERIFICATION_TIMEOUT_DAYS = 1

# Subscription settings
SUBSCRIPTION_ADMIN_PASSWORD = os.environ.get('SUBSCRIPTION_ADMIN_PASSWORD')


# Alert System Configuration
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')
SLACK_DEFAULT_CHANNEL = os.environ.get('SLACK_DEFAULT_CHANNEL', '#alerts')
SLACK_BOT_NAME = os.environ.get('SLACK_BOT_NAME', 'Resee Alert Bot')
ALERT_SUMMARY_RECIPIENTS = os.environ.get('ALERT_SUMMARY_RECIPIENTS', '').split(
    ',') if os.environ.get('ALERT_SUMMARY_RECIPIENTS') else []


# AI Services Configuration
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')


# Toss Payments Configuration
TOSS_CLIENT_KEY = os.environ.get('TOSS_CLIENT_KEY')
TOSS_SECRET_KEY = os.environ.get('TOSS_SECRET_KEY')
TOSS_API_URL = os.environ.get('TOSS_API_URL', 'https://api.tosspayments.com')
TOSS_SUCCESS_URL = os.environ.get('TOSS_SUCCESS_URL', 'http://localhost/payment/success')
TOSS_FAIL_URL = os.environ.get('TOSS_FAIL_URL', 'http://localhost/payment/fail')


# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'resee-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 5000,
            'CULL_FREQUENCY': 4,
        }
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
    }
}


# Session Configuration - Database Backend (Redis removed)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 1 day


# CORS Configuration (base settings)
CORS_ALLOWED_ORIGINS = []  # Will be set in environment-specific settings
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Will be overridden in development


# File Upload Configuration
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644


# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {process:d} {thread:d} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '[{levelname}] {asctime} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'file_format': {
            'format': '[{levelname}] {asctime} {name} {funcName}:{lineno} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file_django': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'file_format',
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django_error.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'file_celery': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'celery.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'file_format',
        },
        'file_security': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'security.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_django'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file_error'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'file_security'],
            'level': 'WARNING',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file_celery'],
            'level': 'INFO',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console', 'file_django'],
            'level': 'INFO',
            'propagate': False,
        },
        'content': {
            'handlers': ['console', 'file_django'],
            'level': 'INFO',
            'propagate': False,
        },
        'review': {
            'handlers': ['console', 'file_django'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file_django'],
        'level': 'INFO',
    },
}


# Health Check Configuration
HEALTH_CHECK = {
    'DATABASE_TIMEOUT': 5,
    'CACHE_TIMEOUT': 3,  # Redis removed - Local Memory Cache
}


# Basic Logging Configuration (simplified)
# Complex monitoring removed - using Django's built-in logging


# Feature Flags
FEATURE_FLAGS = {
    'ENABLE_EXAMS': True,
    'ENABLE_ANALYTICS': True,
    'ENABLE_PAYMENT_SYSTEM': True,
}


# Subscription Configuration
SUBSCRIPTION_SETTINGS = {
    'FREE_TIER_LIMITS': {
        'max_content': 50,
        'review_interval_days': 7,
        'max_exams_per_week': 1,
    },
    'BASIC_TIER_LIMITS': {
        'max_content': 200,
        'review_interval_days': 30,
        'max_exams_per_week': 1,
    },
    'PRO_TIER_LIMITS': {
        'max_content': -1,  # Unlimited
        'review_interval_days': 180,
        'max_exams_per_week': 1,
    },
}


# Google OAuth Configuration
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('GOOGLE_OAUTH2_CLIENT_ID', ''),
            'secret': os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET', ''),
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'offline',
        }
    }
}

# Security Headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'

# Content Security Policy (기본 설정)
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https:")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_SRC = ("'none'",)

# Session Security
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# CSRF Security
CSRF_COOKIE_SECURE = True  # HTTPS only
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'


# Celery Configuration
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Seoul'
CELERY_ENABLE_UTC = True

# Celery Beat Configuration
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Task retry configuration
CELERY_TASK_ALWAYS_EAGER = False  # Set to True for testing
CELERY_TASK_EAGER_PROPAGATES = False
CELERY_TASK_ROUTES = {
    'review.tasks.*': {'queue': 'review_queue'},
    'accounts.tasks.*': {'queue': 'email_queue'},
}

# Email task configuration
CELERY_EMAIL_TASK_CONFIG = {
    'rate_limit': '100/m',  # 100 emails per minute
    'max_retries': 3,
    'default_retry_delay': 60,  # 1 minute
}
