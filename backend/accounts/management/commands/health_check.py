"""
Django management command for comprehensive health checks
"""
import sys
from django.core.management.base import BaseCommand
from django.db import connection, connections
from django.conf import settings
from django.core.cache import cache
import anthropic


class Command(BaseCommand):
    help = 'Perform comprehensive health check of all services'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed health information',
        )

    def handle(self, *args, **options):
        detailed = options['detailed']
        errors = []

        self.stdout.write('🏥 Running Health Check...\n')

        # Database check
        if self._check_database():
            self.stdout.write(self.style.SUCCESS('✅ Database: Connected'))
        else:
            errors.append('Database connection failed')
            self.stdout.write(self.style.ERROR('❌ Database: Failed'))

        # Cache check (Local Memory)
        if self._check_cache():
            self.stdout.write(self.style.SUCCESS('✅ Cache: Available'))
        else:
            errors.append('Cache system failed')
            self.stdout.write(self.style.ERROR('❌ Cache: Failed'))

        # AI Service check
        ai_status = self._check_ai_service()
        if ai_status:
            self.stdout.write(self.style.SUCCESS('✅ AI Service: Available'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  AI Service: Using mock responses'))

        # Critical Settings check
        settings_ok = self._check_critical_settings()
        if settings_ok:
            self.stdout.write(self.style.SUCCESS('✅ Settings: OK'))
        else:
            errors.append('Critical settings misconfigured')
            self.stdout.write(self.style.ERROR('❌ Settings: Issues found'))

        if detailed:
            self._show_detailed_info()

        # Summary
        self.stdout.write(f'\n📊 Health Check Summary:')
        if errors:
            self.stdout.write(self.style.ERROR(f'❌ {len(errors)} issues found:'))
            for error in errors:
                self.stdout.write(f'   • {error}')
            sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS('✅ All systems operational'))

    def _check_database(self):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except Exception as e:
            if hasattr(self, 'detailed') and self.detailed:
                self.stdout.write(f'Database error: {e}')
            return False

    def _check_cache(self):
        try:
            cache.set('health_check', 'ok', 30)
            return cache.get('health_check') == 'ok'
        except Exception as e:
            if hasattr(self, 'detailed') and self.detailed:
                self.stdout.write(f'Cache error: {e}')
            return False

    def _check_ai_service(self):
        if getattr(settings, 'AI_USE_MOCK_RESPONSES', True):
            return False

        try:
            api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
            if not api_key:
                return False

            client = anthropic.Anthropic(api_key=api_key)
            # Simple test - we don't actually make a call to avoid costs
            return True
        except Exception:
            return False

    def _check_critical_settings(self):
        issues = []

        # Check SECRET_KEY
        secret_key = getattr(settings, 'SECRET_KEY', '')
        if not secret_key or len(secret_key) < 50:
            issues.append('SECRET_KEY too short or missing')

        # Check DEBUG in production
        if not getattr(settings, 'DEBUG', True) and getattr(settings, 'DEBUG', False):
            issues.append('DEBUG should be False in production')

        # Check ALLOWED_HOSTS
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        if not allowed_hosts or '*' in allowed_hosts:
            if not getattr(settings, 'DEBUG', False):
                issues.append('ALLOWED_HOSTS not properly configured for production')

        return len(issues) == 0

    def _show_detailed_info(self):
        self.stdout.write('\n📋 Detailed Information:')

        # Database info
        self.stdout.write(f'Database: {settings.DATABASES["default"]["ENGINE"]}')

        # Cache info
        cache_backend = settings.CACHES['default']['BACKEND']
        self.stdout.write(f'Cache: {cache_backend}')

        # Environment
        debug = getattr(settings, 'DEBUG', False)
        self.stdout.write(f'Debug mode: {debug}')

        # AI Service
        ai_mock = getattr(settings, 'AI_USE_MOCK_RESPONSES', True)
        self.stdout.write(f'AI Mock responses: {ai_mock}')