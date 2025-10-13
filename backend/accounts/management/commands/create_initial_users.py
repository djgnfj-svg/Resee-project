"""
Management command to create initial users for production deployment.

Usage:
    python manage.py create_initial_users

Environment Variables:
    ADMIN_EMAIL: Admin user email (default: djgnfj8923@naver.com)
    ADMIN_PASSWORD: Admin user password (required)
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Create initial admin and test users for production deployment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-if-exists',
            action='store_true',
            help='Skip user creation if any users already exist',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        """Create initial users for production."""

        # Check if users already exist
        if options['skip_if_exists'] and User.objects.exists():
            self.stdout.write(
                self.style.WARNING('Users already exist. Skipping creation.')
            )
            return

        # Get credentials from environment variables
        admin_email = os.environ.get('ADMIN_EMAIL', 'djgnfj8923@naver.com')
        admin_password = os.environ.get('ADMIN_PASSWORD')

        if not admin_password:
            self.stdout.write(
                self.style.ERROR(
                    'ADMIN_PASSWORD environment variable is required!'
                )
            )
            return

        # 1. Create superuser (admin)
        admin_user, created = self._create_or_get_user(
            email=admin_email,
            password=admin_password,
            is_superuser=True,
            is_staff=True,
            first_name='관리자',
            last_name='Resee',
            tier='PRO'
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Superuser created: {admin_email}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Superuser already exists: {admin_email}')
            )

        # 2. Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Initial users setup complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write(f'Admin email: {admin_email}')
        self.stdout.write(f'Admin tier: PRO')
        self.stdout.write(f'Email verified: Yes')
        self.stdout.write('')
        self.stdout.write(
            self.style.WARNING('⚠️  Make sure to change the default password!')
        )

    def _create_or_get_user(self, email, password, is_superuser=False,
                           is_staff=False, first_name='', last_name='', tier='FREE'):
        """Create or get user with specified attributes."""

        # Check if user exists
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            return user, False

        # Create new user
        user = User.objects.create_user(
            email=email,
            password=password,
            is_superuser=is_superuser,
            is_staff=is_staff,
            first_name=first_name,
            last_name=last_name,
            is_email_verified=True  # Auto-verify for initial users
        )

        # Set subscription tier
        from accounts.models import Subscription

        subscription, created = Subscription.objects.get_or_create(
            user=user,
            defaults={
                'tier': tier,
                'is_active': True
            }
        )

        if not created and subscription.tier != tier:
            subscription.tier = tier
            subscription.is_active = True
            subscription.save()

        return user, True
