"""
Django management command to set up logging infrastructure.
"""
import os
import logging
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Set up logging infrastructure for monitoring system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-dirs',
            action='store_true',
            help='Create log directories',
        )
        parser.add_argument(
            '--test-logging',
            action='store_true',
            help='Test logging configuration',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up old log files',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up logging infrastructure...'))

        if options['create_dirs']:
            self.create_log_directories()

        if options['test_logging']:
            self.test_logging_system()

        if options['cleanup']:
            self.cleanup_old_logs()

        if not any([options['create_dirs'], options['test_logging'], options['cleanup']]):
            self.create_log_directories()
            self.test_logging_system()

        self.stdout.write(self.style.SUCCESS('Logging infrastructure setup complete!'))

    def create_log_directories(self):
        """Create necessary log directories"""
        log_dir = Path(settings.BASE_DIR) / 'logs'

        try:
            log_dir.mkdir(exist_ok=True)
            self.stdout.write(f'✅ Created log directory: {log_dir}')

            # Set proper permissions
            os.chmod(log_dir, 0o755)

            # Create initial log files if they don't exist
            log_files = [
                'django.log',
                'django_error.log',
                'celery.log',
                'security.log'
            ]

            for log_file in log_files:
                log_path = log_dir / log_file
                if not log_path.exists():
                    log_path.touch()
                    os.chmod(log_path, 0o644)
                    self.stdout.write(f'📝 Created log file: {log_file}')

        except PermissionError:
            self.stdout.write(
                self.style.ERROR(f'❌ Permission denied creating log directory: {log_dir}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating log directory: {e}')
            )

    def test_logging_system(self):
        """Test the logging system"""
        self.stdout.write('🧪 Testing logging system...')

        try:
            # Test different loggers
            loggers_to_test = [
                ('django', logging.INFO, 'Django logger test'),
                ('django.request', logging.ERROR, 'Django request error test'),
                ('django.security', logging.WARNING, 'Django security warning test'),
                ('celery', logging.INFO, 'Celery logger test'),
                ('accounts', logging.INFO, 'Accounts app logger test'),
                ('content', logging.INFO, 'Content app logger test'),
                ('review', logging.INFO, 'Review app logger test'),
                ('analytics', logging.INFO, 'Analytics app logger test'),
            ]

            for logger_name, level, message in loggers_to_test:
                logger = logging.getLogger(logger_name)
                logger.log(level, f'[TEST] {message} - {self.__class__.__name__}')
                self.stdout.write(f'✅ Tested logger: {logger_name}')

            self.stdout.write(self.style.SUCCESS('🎉 All loggers tested successfully!'))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error testing logging system: {e}')
            )

    def cleanup_old_logs(self):
        """Clean up old rotated log files"""
        log_dir = Path(settings.BASE_DIR) / 'logs'

        if not log_dir.exists():
            self.stdout.write(self.style.WARNING('⚠️ Log directory does not exist'))
            return

        try:
            # Find rotated log files (*.log.1, *.log.2, etc.)
            rotated_files = list(log_dir.glob('*.log.*'))

            if not rotated_files:
                self.stdout.write('ℹ️ No rotated log files found')
                return

            self.stdout.write(f'🗑️ Found {len(rotated_files)} rotated log files')

            total_size = 0
            for log_file in rotated_files:
                file_size = log_file.stat().st_size
                total_size += file_size
                self.stdout.write(f'  📄 {log_file.name} ({file_size / 1024 / 1024:.2f} MB)')

            self.stdout.write(f'📊 Total size: {total_size / 1024 / 1024:.2f} MB')

            # Optionally delete old files (uncomment if needed)
            # for log_file in rotated_files:
            #     log_file.unlink()
            #     self.stdout.write(f'🗑️ Deleted: {log_file.name}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during cleanup: {e}')
            )