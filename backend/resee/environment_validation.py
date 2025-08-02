"""
Environment variable validation for Resee Django application.
Ensures all required environment variables are properly configured for different environments.
"""

import os
import logging
import re
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class EnvironmentValidationError(Exception):
    """Custom exception for environment validation errors"""
    pass


class EnvironmentValidator:
    """Validates environment variables for different deployment environments"""
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.environ.get('ENVIRONMENT', 'development')
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all validations and return results"""
        self.errors = []
        self.warnings = []
        
        # Core validations for all environments
        self._validate_core_settings()
        
        # Environment-specific validations
        if self.environment in ['staging', 'production']:
            self._validate_production_settings()
            self._validate_security_settings()
            self._validate_external_services()
        
        if self.environment == 'production':
            self._validate_production_only_settings()
        
        # Log results
        self._log_validation_results()
        
        return {
            'environment': self.environment,
            'errors': self.errors,
            'warnings': self.warnings,
            'is_valid': len(self.errors) == 0
        }
    
    def _validate_core_settings(self):
        """Validate core Django settings that apply to all environments"""
        
        # SECRET_KEY validation
        secret_key = os.environ.get('SECRET_KEY', '')
        if not secret_key:
            self.errors.append("SECRET_KEY environment variable is required")
        elif len(secret_key) < 50:
            self.warnings.append("SECRET_KEY should be at least 50 characters long")
        elif 'django-insecure' in secret_key or secret_key == 'your-secret-key-for-development':
            if self.environment in ['staging', 'production']:
                self.errors.append("Cannot use development SECRET_KEY in production environment")
            else:
                self.warnings.append("Using development SECRET_KEY (OK for development)")
        
        # Database URL validation
        database_url = os.environ.get('DATABASE_URL', '')
        if not database_url:
            self.errors.append("DATABASE_URL environment variable is required")
        else:
            if not self._validate_database_url(database_url):
                self.errors.append("DATABASE_URL format is invalid")
        
        # Debug mode validation
        debug = os.environ.get('DEBUG', 'False')
        if self.environment in ['staging', 'production'] and debug.lower() == 'true':
            self.errors.append("DEBUG should be False in production environments")
    
    def _validate_production_settings(self):
        """Validate settings specific to staging/production environments"""
        
        required_vars = [
            'ALLOWED_HOSTS',
            'CELERY_BROKER_URL', 
            'REDIS_URL',
            'EMAIL_BACKEND'
        ]
        
        for var in required_vars:
            if not os.environ.get(var):
                self.errors.append(f"{var} environment variable is required in {self.environment}")
        
        # ALLOWED_HOSTS validation
        allowed_hosts = os.environ.get('ALLOWED_HOSTS', '')
        if allowed_hosts:
            hosts = [host.strip() for host in allowed_hosts.split(',')]
            if 'localhost' in hosts or '127.0.0.1' in hosts:
                self.warnings.append("ALLOWED_HOSTS contains localhost/127.0.0.1 in production environment")
        
        # Celery broker URL validation
        celery_url = os.environ.get('CELERY_BROKER_URL', '')
        if celery_url and not self._validate_celery_url(celery_url):
            self.errors.append("CELERY_BROKER_URL format is invalid")
        
        # Redis URL validation
        redis_url = os.environ.get('REDIS_URL', '')
        if redis_url and not self._validate_redis_url(redis_url):
            self.errors.append("REDIS_URL format is invalid")
    
    def _validate_security_settings(self):
        """Validate security-related environment variables"""
        
        # CORS settings
        cors_allow_all = os.environ.get('CORS_ALLOW_ALL_ORIGINS', 'False')
        if cors_allow_all.lower() == 'true' and self.environment == 'production':
            self.warnings.append("CORS_ALLOW_ALL_ORIGINS is True in production (potential security risk)")
        
        # Email verification enforcement
        enforce_email = os.environ.get('ENFORCE_EMAIL_VERIFICATION', 'True')
        if enforce_email.lower() != 'true' and self.environment == 'production':
            self.warnings.append("Email verification is not enforced in production")
        
        # Admin IP whitelist
        admin_whitelist = os.environ.get('ADMIN_IP_WHITELIST', '')
        if not admin_whitelist and self.environment == 'production':
            self.warnings.append("ADMIN_IP_WHITELIST not configured (admin access not restricted)")
    
    def _validate_external_services(self):
        """Validate external service configurations"""
        
        # Email service validation
        email_backend = os.environ.get('EMAIL_BACKEND', '')
        
        if email_backend == 'django_ses.SESBackend':
            aws_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SES_REGION_NAME']
            for var in aws_vars:
                if not os.environ.get(var):
                    self.errors.append(f"{var} required for AWS SES email backend")
        
        elif email_backend == 'django.core.mail.backends.smtp.EmailBackend':
            smtp_vars = ['EMAIL_HOST', 'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD']
            for var in smtp_vars:
                if not os.environ.get(var):
                    self.errors.append(f"{var} required for SMTP email backend")
        
        elif email_backend == 'django.core.mail.backends.console.EmailBackend' and self.environment == 'production':
            self.warnings.append("Using console email backend in production (emails won't be sent)")
        
        # AI service validation
        openai_key = os.environ.get('OPENAI_API_KEY', '')
        anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '')
        
        if not openai_key and not anthropic_key:
            self.warnings.append("No AI service API keys configured (AI features will be disabled)")
        
        if openai_key and not self._validate_api_key_format(openai_key, 'sk-'):
            self.warnings.append("OPENAI_API_KEY format appears invalid")
        
        if anthropic_key and not self._validate_api_key_format(anthropic_key, 'sk-ant-'):
            self.warnings.append("ANTHROPIC_API_KEY format appears invalid")
        
        # Google OAuth validation
        google_client_id = os.environ.get('GOOGLE_OAUTH2_CLIENT_ID', '')
        google_client_secret = os.environ.get('GOOGLE_OAUTH2_CLIENT_SECRET', '')
        
        if google_client_id and not google_client_secret:
            self.errors.append("GOOGLE_OAUTH2_CLIENT_SECRET required when GOOGLE_OAUTH2_CLIENT_ID is set")
        elif google_client_secret and not google_client_id:
            self.errors.append("GOOGLE_OAUTH2_CLIENT_ID required when GOOGLE_OAUTH2_CLIENT_SECRET is set")
    
    def _validate_production_only_settings(self):
        """Validate settings specific to production environment only"""
        
        # HTTPS enforcement
        force_https = os.environ.get('FORCE_HTTPS', 'False')
        if force_https.lower() != 'true':
            self.warnings.append("FORCE_HTTPS not enabled in production (consider enabling for security)")
        
        # Frontend URL validation
        frontend_url = os.environ.get('FRONTEND_URL', '')
        if frontend_url:
            if 'localhost' in frontend_url or '127.0.0.1' in frontend_url:
                self.warnings.append("FRONTEND_URL contains localhost in production")
            elif not frontend_url.startswith('https://'):
                self.warnings.append("FRONTEND_URL should use HTTPS in production")
    
    def _validate_database_url(self, url: str) -> bool:
        """Validate database URL format"""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ['postgresql', 'postgres', 'mysql', 'sqlite'] and bool(parsed.netloc or parsed.path)
        except Exception:
            return False
    
    def _validate_celery_url(self, url: str) -> bool:
        """Validate Celery broker URL format"""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ['amqp', 'redis', 'sqla+postgresql'] and bool(parsed.netloc)
        except Exception:
            return False
    
    def _validate_redis_url(self, url: str) -> bool:
        """Validate Redis URL format"""
        try:
            parsed = urlparse(url)
            return parsed.scheme == 'redis' and bool(parsed.netloc)
        except Exception:
            return False
    
    def _validate_api_key_format(self, key: str, prefix: str) -> bool:
        """Validate API key format"""
        if not key.startswith(prefix):
            return False
        return len(key) > len(prefix) + 10  # Reasonable minimum length
    
    def _log_validation_results(self):
        """Log validation results"""
        if self.errors:
            logger.error(f"Environment validation failed for {self.environment}:")
            for error in self.errors:
                logger.error(f"  ERROR: {error}")
        
        if self.warnings:
            logger.warning(f"Environment validation warnings for {self.environment}:")
            for warning in self.warnings:
                logger.warning(f"  WARNING: {warning}")
        
        if not self.errors and not self.warnings:
            logger.info(f"Environment validation passed for {self.environment}")


def validate_environment(environment: str = None) -> Dict[str, Any]:
    """
    Validate environment variables for the given environment.
    
    Args:
        environment: Environment name ('development', 'staging', 'production')
    
    Returns:
        Dict containing validation results
    
    Raises:
        EnvironmentValidationError: If critical validation errors are found
    """
    validator = EnvironmentValidator(environment)
    results = validator.validate_all()
    
    if results['errors']:
        error_msg = f"Environment validation failed: {'; '.join(results['errors'])}"
        raise EnvironmentValidationError(error_msg)
    
    return results


def check_required_environment_variables() -> bool:
    """
    Quick check for absolutely critical environment variables.
    Used during Django startup.
    
    Returns:
        True if all critical variables are present, False otherwise
    """
    environment = os.environ.get('ENVIRONMENT', 'development')
    
    if environment in ['staging', 'production']:
        critical_vars = ['SECRET_KEY', 'DATABASE_URL', 'ALLOWED_HOSTS']
        missing = [var for var in critical_vars if not os.environ.get(var)]
        
        if missing:
            logger.critical(f"Critical environment variables missing: {', '.join(missing)}")
            return False
    
    return True


def get_environment_info() -> Dict[str, Any]:
    """
    Get information about the current environment configuration.
    
    Returns:
        Dict containing environment information
    """
    environment = os.environ.get('ENVIRONMENT', 'development')
    
    info = {
        'environment': environment,
        'debug': os.environ.get('DEBUG', 'False') == 'True',
        'database_configured': bool(os.environ.get('DATABASE_URL')),
        'cache_configured': bool(os.environ.get('REDIS_URL')),
        'email_backend': os.environ.get('EMAIL_BACKEND', 'console'),
        'ai_services': {
            'openai': bool(os.environ.get('OPENAI_API_KEY')),
            'anthropic': bool(os.environ.get('ANTHROPIC_API_KEY')),
        },
        'oauth_configured': bool(os.environ.get('GOOGLE_OAUTH2_CLIENT_ID')),
        'monitoring_enabled': environment in ['staging', 'production'],
    }
    
    return info