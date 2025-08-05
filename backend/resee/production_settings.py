"""
Production security settings for Resee
"""

import os
from .settings import *

# Security Settings for Production
DEBUG = False

# Strong security headers
SECURE_BROWSER_XSS_FILTER = os.environ.get('SECURE_BROWSER_XSS_FILTER', 'True').lower() == 'true'
SECURE_CONTENT_TYPE_NOSNIFF = os.environ.get('SECURE_CONTENT_TYPE_NOSNIFF', 'True').lower() == 'true'
# SSL/HTTPS settings removed - handled by AWS ALB/CloudFront
# SECURE_HSTS_* and SECURE_SSL_* settings managed by AWS
SECURE_REDIRECT_EXEMPT = []

# Session Security
# SESSION_COOKIE_SECURE handled by AWS - cookies secure by default
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 3600  # 1 hour

# CSRF Protection
# CSRF_COOKIE_SECURE handled by AWS - cookies secure by default
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
csrf_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [origin for origin in csrf_origins.split(',') if origin.strip()]

# Admin security
ADMIN_IP_WHITELIST = os.environ.get('ADMIN_IP_WHITELIST', '').split(',')

# Password requirements
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # Stronger minimum length
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'resee.validators.ComplexPasswordValidator',  # Custom validator
    },
]

# JWT Security
SIMPLE_JWT.update({
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),  # Shorter access token lifetime
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),     # Shorter refresh token lifetime
    'ROTATE_REFRESH_TOKENS': True,                   # Rotate refresh tokens
    'BLACKLIST_AFTER_ROTATION': True,               # Blacklist old refresh tokens
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': 'resee-api',
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
})

# CORS Security
CORS_ALLOW_ALL_ORIGINS = False
cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '')
CORS_ALLOWED_ORIGINS = [origin for origin in cors_origins.split(',') if origin.strip()]
CORS_ALLOW_CREDENTIALS = True
CORS_PREFLIGHT_MAX_AGE = 86400

# File Upload Security
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Database Security
DATABASES['default'].update({
    'CONN_MAX_AGE': 60,
    'OPTIONS': {
        'connect_timeout': 10,
        'application_name': 'resee-backend',
        # SSL managed by AWS RDS
    }
})

# Logging Configuration
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
        'json': {
            'format': '{asctime} {name} {levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'filters': ['require_debug_false'],
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'resee.log'),
            'maxBytes': 1024*1024*50,  # 50MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'security.log'),
            'maxBytes': 1024*1024*50,  # 50MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'errors.log'),
            'maxBytes': 1024*1024*50,  # 50MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file'],
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file', 'mail_admins'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'resee': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'resee.middleware': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    }
}

# Email Security (for error reporting)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@resee.com')
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', 'server@resee.com')

# Admin notification emails
ADMINS = [
    ('Admin', os.environ.get('ADMIN_EMAIL', 'admin@resee.com')),
]
MANAGERS = ADMINS

# Cache Security
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        }
    }
}

# Celery Security
# SSL certificates managed by AWS - simplified broker config

# Static files security
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files security
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Additional security settings
X_FRAME_OPTIONS = 'DENY'
SILENCED_SYSTEM_CHECKS = ['security.W019']  # Only if you know what you're doing

# API throttling
REST_FRAMEWORK.update({
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '5/min',
        'upload': '10/hour',
    }
})

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'",)
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_BASE_URI = ("'self'",)

# Monitoring and Health Checks
HEALTH_CHECK_ENDPOINTS = [
    'health/',
    'health/db/',
    'health/cache/',
    'health/celery/',
]

# Feature flags for security
SECURITY_FEATURES = {
    'RATE_LIMITING': True,
    'SQL_INJECTION_DETECTION': True,
    'LOGIN_ATTEMPT_TRACKING': True,
    'FILE_UPLOAD_SCANNING': True,
    'REQUEST_LOGGING': True,
    'IP_WHITELIST': bool(ADMIN_IP_WHITELIST),
}

# Environment-specific overrides
if os.environ.get('ENVIRONMENT') == 'staging':
    DEBUG = False
    ALLOWED_HOSTS = ['staging.resee.com']
    
elif os.environ.get('ENVIRONMENT') == 'production':
    DEBUG = False
    ALLOWED_HOSTS = ['resee.com', 'www.resee.com']
    
    # Stricter settings for production
    SESSION_COOKIE_AGE = 1800  # 30 minutes
    SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(minutes=10)
    
    # Enable all security features
    SECURITY_FEATURES.update({
        'ADVANCED_THREAT_DETECTION': True,
        'ANOMALY_DETECTION': True,
    })