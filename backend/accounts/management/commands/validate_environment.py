"""
Django management command to validate environment configuration.
Usage: python manage.py validate_environment [--environment ENVIRONMENT] [--fix-warnings]
"""

import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from resee.environment_validation import (get_environment_info,
                                          validate_environment)


class Command(BaseCommand):
    help = 'Validate environment configuration for deployment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--environment',
            type=str,
            default=None,
            help='Environment to validate (development, staging, production). Defaults to current ENVIRONMENT setting.'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output results in JSON format'
        )
        parser.add_argument(
            '--info',
            action='store_true',
            help='Show detailed environment information'
        )
        parser.add_argument(
            '--fix-warnings',
            action='store_true',
            help='Show suggestions for fixing warnings'
        )

    def handle(self, *args, **options):
        environment = options['environment'] or getattr(settings, 'ENVIRONMENT', 'development')
        
        self.stdout.write(
            self.style.SUCCESS(f'Validating environment configuration for: {environment.upper()}')
        )
        self.stdout.write('')

        try:
            # Run validation
            results = validate_environment(environment)
            
            if options['json']:
                # Output JSON format
                output = {
                    'environment': environment,
                    'validation_results': results,
                }
                
                if options['info']:
                    output['environment_info'] = get_environment_info()
                
                self.stdout.write(json.dumps(output, indent=2))
                return

            # Human-readable output
            self._display_results(results, options)
            
            if options['info']:
                self._display_environment_info()

            # Exit code based on validation results
            if results['errors']:
                raise CommandError(f"Environment validation failed with {len(results['errors'])} error(s)")
            
            if results['warnings']:
                self.stdout.write('')
                self.stdout.write(
                    self.style.WARNING(f'Validation completed with {len(results["warnings"])} warning(s)')
                )
            else:
                self.stdout.write('')
                self.stdout.write(
                    self.style.SUCCESS('Environment validation passed successfully!')
                )

        except Exception as e:
            raise CommandError(f"Validation failed: {str(e)}")

    def _display_results(self, results, options):
        """Display validation results in human-readable format"""
        
        # Display errors
        if results['errors']:
            self.stdout.write(self.style.ERROR('ERRORS:'))
            for error in results['errors']:
                self.stdout.write(f'  ❌ {error}')
            self.stdout.write('')

        # Display warnings
        if results['warnings']:
            self.stdout.write(self.style.WARNING('WARNINGS:'))
            for warning in results['warnings']:
                self.stdout.write(f'  ⚠️  {warning}')
            
            if options['fix_warnings']:
                self.stdout.write('')
                self._display_warning_fixes(results['warnings'])
            self.stdout.write('')

    def _display_warning_fixes(self, warnings):
        """Display suggestions for fixing warnings"""
        self.stdout.write(self.style.HTTP_INFO('SUGGESTED FIXES:'))
        
        fixes = {
            'SECRET_KEY should be at least 50 characters long': 
                'Generate a longer SECRET_KEY using: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"',
            
            'Using development SECRET_KEY': 
                'Set a production SECRET_KEY in your environment variables',
            
            'ALLOWED_HOSTS contains localhost': 
                'Remove localhost/127.0.0.1 from ALLOWED_HOSTS and add your production domain',
            
            'CORS_ALLOW_ALL_ORIGINS is True in production': 
                'Set CORS_ALLOW_ALL_ORIGINS=False and configure CORS_ALLOWED_ORIGINS with specific domains',
            
            'Email verification is not enforced': 
                'Set ENFORCE_EMAIL_VERIFICATION=True for production security',
            
            'ADMIN_IP_WHITELIST not configured': 
                'Configure ADMIN_IP_WHITELIST to restrict admin access to specific IP addresses',
            
            'Using console email backend in production': 
                'Configure EMAIL_BACKEND to use django_ses.SESBackend or SMTP backend',
            
            'No AI service API keys configured': 
                'Set OPENAI_API_KEY or ANTHROPIC_API_KEY to enable AI features',
            
            'FORCE_HTTPS not enabled': 
                'Set FORCE_HTTPS=True to enforce HTTPS in production',
            
            'FRONTEND_URL contains localhost': 
                'Set FRONTEND_URL to your production frontend domain',
            
            'FRONTEND_URL should use HTTPS': 
                'Update FRONTEND_URL to use https:// scheme',
        }
        
        for warning in warnings:
            for pattern, fix in fixes.items():
                if pattern in warning:
                    self.stdout.write(f'  💡 {fix}')
                    break

    def _display_environment_info(self):
        """Display detailed environment information"""
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('ENVIRONMENT INFORMATION:'))
        
        info = get_environment_info()
        
        # Basic info
        self.stdout.write(f'  Environment: {info["environment"]}')
        self.stdout.write(f'  Debug mode: {info["debug"]}')
        
        # Service configurations
        self.stdout.write('')
        self.stdout.write('  📊 Service Configuration:')
        self.stdout.write(f'    Database: {"✅ Configured" if info["database_configured"] else "❌ Not configured"}')
        self.stdout.write(f'    Cache (Redis): {"✅ Configured" if info["cache_configured"] else "❌ Not configured"}')
        self.stdout.write(f'    Email backend: {info["email_backend"]}')
        self.stdout.write(f'    OAuth (Google): {"✅ Configured" if info["oauth_configured"] else "❌ Not configured"}')
        self.stdout.write(f'    Monitoring: {"✅ Enabled" if info["monitoring_enabled"] else "❌ Disabled"}')
        
        # AI services
        self.stdout.write('')
        self.stdout.write('  🤖 AI Services:')
        self.stdout.write(f'    OpenAI: {"✅ Configured" if info["ai_services"]["openai"] else "❌ Not configured"}')
        self.stdout.write(f'    Anthropic: {"✅ Configured" if info["ai_services"]["anthropic"] else "❌ Not configured"}')
        
        # Environment variables summary
        self.stdout.write('')
        self.stdout.write('  🔧 Key Environment Variables:')
        
        env_vars = [
            'SECRET_KEY', 'DEBUG', 'ALLOWED_HOSTS', 'DATABASE_URL',
            'EMAIL_BACKEND', 'FRONTEND_URL', 'ENVIRONMENT'
        ]
        
        for var in env_vars:
            value = os.environ.get(var, 'Not set')
            # Mask sensitive values
            if var in ['SECRET_KEY', 'DATABASE_URL']:
                if value != 'Not set':
                    value = f"{value[:10]}...{value[-5:]}" if len(value) > 15 else "***"
            
            status = "✅" if os.environ.get(var) else "❌"
            self.stdout.write(f'    {status} {var}: {value}')

    def _get_style_for_level(self, level):
        """Get style based on log level"""
        styles = {
            'ERROR': self.style.ERROR,
            'WARNING': self.style.WARNING,
            'INFO': self.style.SUCCESS,
            'DEBUG': self.style.HTTP_INFO,
        }
        return styles.get(level, self.style.NOTICE)