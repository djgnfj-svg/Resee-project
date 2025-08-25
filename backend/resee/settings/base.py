"""
Django base settings for resee project.
Common settings that apply to all environments.
"""

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from celery.schedules import crontab

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
    'corsheaders',
    'django_filters',
    'drf_yasg',
    'celery',
    'django_celery_beat',
    'django_celery_results',
    
    # Local apps
    'accounts',  # includes legal functionality
    'content',
    'review',
    'analytics',  # includes business intelligence
    'ai_review',
    'monitoring',  # includes alerts system
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
    'monitoring.middleware.MetricsCollectionMiddleware',
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
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '5/min',
        'registration': '3/min',
        'register': '3/min',
        'email': '10/hour',
        'ai_endpoint': '50/hour',
    },
}


# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
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


# Celery Configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Celery Beat Configuration
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-reviews': {
        'task': 'review.tasks.cleanup_expired_reviews',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'update-review-streaks': {
        'task': 'analytics.tasks.update_review_streaks',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    'generate-daily-analytics': {
        'task': 'analytics.tasks.generate_daily_analytics',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    # Alert system tasks
    'check-alert-rules': {
        'task': 'alerts.tasks.check_alert_rules',
        'schedule': crontab(minute='*'),  # Every minute
    },
    'send-daily-alert-summary': {
        'task': 'alerts.tasks.send_daily_alert_summary',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    'cleanup-old-alert-history': {
        'task': 'alerts.tasks.cleanup_old_alert_history',
        'schedule': crontab(hour=4, minute=0),  # Daily at 4 AM
    },
    'update-alert-metrics-cache': {
        'task': 'alerts.tasks.update_alert_metrics_cache',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    # Business Intelligence tasks
    'collect-daily-learning-patterns': {
        'task': 'bi.collect_daily_learning_patterns',
        'schedule': crontab(hour=0, minute=30),  # Daily at 12:30 AM
    },
    'update-content-effectiveness': {
        'task': 'bi.update_content_effectiveness',
        'schedule': crontab(hour=1, minute=30),  # Daily at 1:30 AM
    },
    'update-subscription-analytics': {
        'task': 'bi.update_subscription_analytics',
        'schedule': crontab(hour=2, minute=30),  # Daily at 2:30 AM
    },
    'collect-system-metrics': {
        'task': 'bi.collect_system_metrics',
        'schedule': crontab(hour=0, minute=15),  # Daily at 12:15 AM
    },
    'cleanup-old-analytics-data': {
        'task': 'bi.cleanup_old_analytics_data',
        'schedule': crontab(hour=5, minute=0, day_of_month=1),  # Monthly on 1st day at 5 AM
    },
}


# Email Configuration (base settings)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@resee.com'


# Alert System Configuration
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')
SLACK_DEFAULT_CHANNEL = os.environ.get('SLACK_DEFAULT_CHANNEL', '#alerts')
SLACK_BOT_NAME = os.environ.get('SLACK_BOT_NAME', 'Resee Alert Bot')
ALERT_SUMMARY_RECIPIENTS = os.environ.get('ALERT_SUMMARY_RECIPIENTS', '').split(',') if os.environ.get('ALERT_SUMMARY_RECIPIENTS') else []


# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}


# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 1 day


# CORS Configuration (base settings)
CORS_ALLOWED_ORIGINS = []  # Will be set in environment-specific settings
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Will be overridden in development


# AI Service Configuration
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
AI_MODEL_NAME = 'claude-3-haiku-20240307'
AI_MAX_TOKENS = 4000
AI_TEMPERATURE = 0.7


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
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}


# Health Check Configuration
HEALTH_CHECK = {
    'DATABASE_TIMEOUT': 5,
    'REDIS_TIMEOUT': 3,
    'AI_SERVICE_TIMEOUT': 10,
}


# Monitoring Configuration
MONITORING = {
    'ENABLE_PERFORMANCE_TRACKING': True,
    'ENABLE_ERROR_TRACKING': True,
    'SLOW_QUERY_THRESHOLD': 1.0,  # seconds
    'MEMORY_USAGE_THRESHOLD': 500,  # MB
}


# Feature Flags
FEATURE_FLAGS = {
    'ENABLE_AI_FEATURES': True,
    'ENABLE_WEEKLY_TESTS': True,
    'ENABLE_ANALYTICS': True,
    'ENABLE_PAYMENT_SYSTEM': True,
}


# Subscription Configuration
SUBSCRIPTION_SETTINGS = {
    'FREE_TIER_LIMITS': {
        'max_content': 50,
        'max_ai_questions': 10,
        'review_interval_days': 7,
    },
    'BASIC_TIER_LIMITS': {
        'max_content': 200,
        'max_ai_questions': 50,
        'review_interval_days': 30,
    },
    'PREMIUM_TIER_LIMITS': {
        'max_content': 1000,
        'max_ai_questions': 200,
        'review_interval_days': 60,
    },
    'PRO_TIER_LIMITS': {
        'max_content': -1,  # Unlimited
        'max_ai_questions': -1,  # Unlimited
        'review_interval_days': 180,
    },
}


# Security Headers (base settings)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'