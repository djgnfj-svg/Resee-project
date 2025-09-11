"""
WSGI config for resee project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Determine settings module based on environment
# Production deployment should set DJANGO_SETTINGS_MODULE explicitly
settings_module = os.environ.get('DJANGO_SETTINGS_MODULE')
if not settings_module:
    # Fallback based on other environment indicators
    if os.environ.get('ENVIRONMENT') == 'production':
        settings_module = 'resee.settings.production'
    else:
        settings_module = 'resee.settings.development'
    
    os.environ['DJANGO_SETTINGS_MODULE'] = settings_module

application = get_wsgi_application()