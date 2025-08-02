"""
Django settings for resee project.
"""

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from celery.schedules import crontab

from .logging_config import LOGGING
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-development-key-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,backend').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
    'django_filters',
    'drf_yasg',
    
    # Social authentication
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    
    # Local apps
    'accounts',
    'content',
    'review',
    'analytics',
    'ai_review',
    'monitoring',
]

# Environment-based configuration
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')

# Base middleware for all environments
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Add allauth middleware
    'accounts.middleware.EmailVerificationMiddleware',  # Add email verification middleware after auth
    'monitoring.middleware.MetricsCollectionMiddleware',  # Add metrics collection
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Add security middleware for production environments
if ENVIRONMENT in ['staging', 'production']:
    SECURITY_MIDDLEWARE = [
        'resee.middleware.SecurityHeadersMiddleware',
        'resee.middleware.RateLimitMiddleware',
        'resee.middleware.RequestLoggingMiddleware',
        'resee.middleware.SQLInjectionDetectionMiddleware',
        'resee.middleware.LoginAttemptTrackingMiddleware',
        'resee.middleware.ContentTypeValidationMiddleware',
        'resee.middleware.FileUploadSecurityMiddleware',
    ]
    
    # Insert security middleware after SecurityMiddleware
    MIDDLEWARE = MIDDLEWARE[:1] + SECURITY_MIDDLEWARE + MIDDLEWARE[1:]
    
    # Add IP whitelist middleware if configured
    if os.environ.get('ADMIN_IP_WHITELIST'):
        MIDDLEWARE.insert(-1, 'resee.middleware.IPWhitelistMiddleware')

ROOT_URLCONF = 'resee.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', 'postgresql://resee_user:resee_password@localhost:5432/resee_db')
    )
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'ko-kr'

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',  # Anonymous users
        'user': '1000/hour',  # Authenticated users
        'login': '5/min',  # Login attempts
        'ai': '50/hour',  # AI-related endpoints
        'upload': '10/hour',  # File uploads
        'register': '3/hour',  # User registration
    }
}

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}

# CORS settings
if os.environ.get('CORS_ALLOW_ALL_ORIGINS', 'False') == 'True':
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Add custom origins from environment
    custom_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '')
    if custom_origins:
        CORS_ALLOWED_ORIGINS.extend(custom_origins.split(','))

# Redis settings
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session engine
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Celery settings
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'amqp://resee:resee_password@localhost:5672//')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', REDIS_URL)
CELERY_CACHE_BACKEND = 'default'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'accounts.authentication.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Email settings - AWS SES
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

# AWS SES Configuration
if EMAIL_BACKEND == 'django_ses.SESBackend':
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
    AWS_SES_REGION_NAME = os.environ.get('AWS_SES_REGION_NAME', 'us-east-1')
    AWS_SES_REGION_ENDPOINT = os.environ.get('AWS_SES_REGION_ENDPOINT', f'email.{AWS_SES_REGION_NAME}.amazonaws.com')
    AWS_SES_AUTO_THROTTLE = 0.5  # 초당 전송률 제한
    
# SMTP Configuration (backup)
elif EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@resee.com')
    SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Review intervals (in days) - 에빙하우스 망각곡선 기반
REVIEW_INTERVALS = [1, 3, 7, 14, 30]

# Celery Beat periodic tasks
CELERY_BEAT_SCHEDULE = {
    'send-daily-review-notifications': {
        'task': 'review.tasks.send_daily_review_notifications',
        'schedule': crontab(hour=9, minute=0),  # 매일 오전 9시
    },
    'cleanup-old-review-history': {
        'task': 'review.tasks.cleanup_old_review_history',
        'schedule': crontab(hour=2, minute=0, day_of_week=1),  # 매주 월요일 새벽 2시
    },
    'update-review-schedules': {
        'task': 'review.tasks.update_review_schedules',
        'schedule': crontab(hour=3, minute=0),  # 매일 새벽 3시
    },
    # Monitoring tasks
    'collect-system-health': {
        'task': 'monitoring.collect_system_health',
        'schedule': 60.0,  # 매 1분마다
    },
    'process-batched-metrics': {
        'task': 'monitoring.process_batched_metrics',
        'schedule': 300.0,  # 매 5분마다
    },
    'cleanup-old-monitoring-data': {
        'task': 'monitoring.cleanup_old_monitoring_data',
        'schedule': crontab(hour=1, minute=0),  # 매일 새벽 1시
    },
    'generate-performance-report': {
        'task': 'monitoring.generate_performance_report',
        'schedule': crontab(hour=8, minute=0),  # 매일 오전 8시
    },
    'alert-on-errors': {
        'task': 'monitoring.alert_on_errors',
        'schedule': 600.0,  # 매 10분마다
    },
}

# Swagger settings
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': False,
    'JSON_EDITOR': True,
    'SUPPORTED_SUBMIT_METHODS': [
        'get',
        'post',
        'put',
        'delete',
        'patch'
    ],
    'OPERATIONS_SORTER': 'alpha',
    'TAGS_SORTER': 'alpha',
    'DOC_EXPANSION': 'none',
    'DEEP_LINKING': True,
    'SHOW_EXTENSIONS': True,
    'DEFAULT_MODEL_RENDERING': 'model',
}

REDOC_SETTINGS = {
    'LAZY_RENDERING': False,
}

# Email configuration (moved to avoid duplication)
# Configuration is handled above in AWS SES and SMTP sections

# Email verification settings
EMAIL_VERIFICATION_TIMEOUT_DAYS = 1  # 24시간
EMAIL_VERIFICATION_RESEND_MINUTES = 5  # 5분 간격 제한
ENFORCE_EMAIL_VERIFICATION = os.environ.get('ENFORCE_EMAIL_VERIFICATION', 'True').lower() == 'true'

# Frontend URL for email links
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

# Django Sites Framework (required for allauth)
SITE_ID = 1

# Allauth configuration
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'  # 우리가 자체 이메일 인증 사용
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_AUTHENTICATION_METHOD = 'email'
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_AUTO_SIGNUP = True

# Google OAuth2 Settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'APP': {
            'client_id': os.environ.get('GOOGLE_OAUTH2_CLIENT_ID', ''),
            'secret': os.environ.get('GOOGLE_OAUTH2_CLIENT_SECRET', ''),
            'key': ''
        }
    }
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'resee.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'errors.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
            'level': 'ERROR',
        },
        'celery_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'celery.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'content': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'review': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'analytics': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'celery_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Environment-specific configuration overrides
if ENVIRONMENT == 'development':
    # Development-specific settings (keep current defaults)
    pass

elif ENVIRONMENT == 'staging':
    # Staging environment settings
    DEBUG = False
    ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
    
    # Use production settings but with less strict JWT tokens
    from .production_settings import *
    
    # Staging-specific overrides
    SIMPLE_JWT.update({
        'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
        'REFRESH_TOKEN_LIFETIME': timedelta(days=3),
    })
    
    # Less aggressive rate limiting for testing
    REST_FRAMEWORK.update({
        'DEFAULT_THROTTLE_RATES': {
            'anon': '200/hour',
            'user': '2000/hour',
            'login': '10/min',
            'upload': '20/hour',
        }
    })

elif ENVIRONMENT == 'production':
    # Production environment settings
    DEBUG = False
    ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
    
    # Import all production settings
    from .production_settings import *
    
    # Ensure logs directory exists with proper permissions
    LOGS_DIR.chmod(0o755)
    
    # Additional production-only settings
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = os.environ.get('FORCE_HTTPS', 'False') == 'True'
    
    # Production cache settings with longer timeouts
    CACHES['default'].update({
        'TIMEOUT': 300,  # 5 minutes default timeout
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 100,
                'retry_on_timeout': True,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        }
    })

# AI Service Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', None)
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4')
AI_MAX_RETRIES = int(os.environ.get('AI_MAX_RETRIES', '3'))
AI_CACHE_TIMEOUT = int(os.environ.get('AI_CACHE_TIMEOUT', '3600'))  # 1 hour

# Comprehensive environment validation
from .environment_validation import validate_environment, check_required_environment_variables, get_environment_info
import logging

# Quick check for critical variables during startup
if not check_required_environment_variables():
    raise ValueError("Critical environment variables are missing. Check logs for details.")

# Perform comprehensive validation
try:
    validation_results = validate_environment(ENVIRONMENT)
    
    # Log environment info for debugging
    env_info = get_environment_info()
    logger = logging.getLogger(__name__)
    logger.info(f"Environment configuration loaded: {env_info}")
    
    # Log validation warnings if any
    if validation_results.get('warnings'):
        for warning in validation_results['warnings']:
            logger.warning(f"Environment validation warning: {warning}")
            
except Exception as e:
    # In development, log the error but don't fail
    if ENVIRONMENT == 'development':
        print(f"Environment validation warning (development): {e}")
    else:
        # In staging/production, validation failures should stop startup
        raise ValueError(f"Environment validation failed: {e}")