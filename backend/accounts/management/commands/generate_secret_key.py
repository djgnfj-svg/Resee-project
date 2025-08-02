"""
Django management command to generate a secure SECRET_KEY.
Usage: python manage.py generate_secret_key [--length LENGTH]
"""

from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key


class Command(BaseCommand):
    help = 'Generate a secure SECRET_KEY for Django settings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--length',
            type=int,
            default=50,
            help='Length of the secret key (default: 50, minimum: 50)'
        )
        parser.add_argument(
            '--export',
            action='store_true',
            help='Output in export format for easy copying to environment files'
        )

    def handle(self, *args, **options):
        length = max(options['length'], 50)  # Ensure minimum length of 50
        
        # Generate the secret key
        secret_key = get_random_secret_key()
        
        # If a specific length is requested, adjust the key
        if length != 50:
            # Django's get_random_secret_key() returns a 50-character key
            # For longer keys, we'll generate multiple and concatenate
            while len(secret_key) < length:
                secret_key += get_random_secret_key()
            secret_key = secret_key[:length]
        
        if options['export']:
            self.stdout.write(f'export SECRET_KEY="{secret_key}"')
        else:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('Generated SECRET_KEY:'))
            self.stdout.write('')
            self.stdout.write(secret_key)
            self.stdout.write('')
            self.stdout.write(self.style.HTTP_INFO('Add this to your environment variables:'))
            self.stdout.write(f'SECRET_KEY={secret_key}')
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Keep this key secure and never commit it to version control!'))