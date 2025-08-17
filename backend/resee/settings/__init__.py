"""
Django settings package for resee project.
Automatically loads the appropriate settings based on the DJANGO_SETTINGS_MODULE environment variable.
"""

import os
import sys

# Get the environment from DJANGO_SETTINGS_MODULE or ENVIRONMENT variable
settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', '')
environment = os.environ.get('ENVIRONMENT', 'development')

# Determine which settings to load
if 'testing' in settings_module or 'test' in sys.argv:
    from .testing import *
elif environment == 'production' or 'production' in settings_module:
    from .production import *
elif environment == 'staging' or 'staging' in settings_module:
    # For staging environment, use production settings with some modifications
    from .production import *
    
    # Staging-specific overrides
    DEBUG = os.environ.get('DEBUG', 'False') == 'True'
    ALLOWED_HOSTS.extend(['staging.resee.com', 'resee-staging.herokuapp.com'])
    
    # Less strict security in staging
    SECURE_HSTS_SECONDS = 0
    
    print("Staging environment loaded (based on production settings).")
else:
    # Default to development
    from .development import *

# Environment validation warnings
def validate_environment():
    """Validate critical environment variables"""
    warnings = []
    
    if not SECRET_KEY or SECRET_KEY == 'django-insecure-development-key-change-this-in-production':
        if environment == 'production':
            warnings.append("CRITICAL: SECRET_KEY not set or using default in production!")
        elif len(SECRET_KEY) < 50:
            warnings.append("WARNING: SECRET_KEY should be at least 50 characters long")
    
    if environment == 'production':
        if DEBUG:
            warnings.append("CRITICAL: DEBUG=True in production environment!")
        
        if not DATABASES.get('default', {}).get('NAME'):
            warnings.append("CRITICAL: Database not configured in production!")
        
        if CORS_ALLOW_ALL_ORIGINS:
            warnings.append("CRITICAL: CORS_ALLOW_ALL_ORIGINS=True in production!")
    
    if ANTHROPIC_API_KEY == 'test-api-key' and environment == 'production':
        warnings.append("CRITICAL: Using test AI API key in production!")
    
    return warnings

# Run validation
validation_warnings = validate_environment()
for warning in validation_warnings:
    print(f"⚠️  {warning}")

# Export current environment info
CURRENT_ENVIRONMENT = environment
SETTINGS_MODULE_LOADED = settings_module or f"resee.settings.{environment}"