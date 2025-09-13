#!/usr/bin/env python
"""
Create Django migrations for data integrity constraints
"""
import os
import sys
from pathlib import Path

# Add Django project to Python path
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resee.settings.production')

import django
django.setup()

from django.core.management import execute_from_command_line


def create_migrations():
    """Create migrations for the enhanced constraints"""
    print("Creating migrations for data integrity constraints...")

    # Create migrations for each app
    apps_to_migrate = ['accounts', 'content', 'review']

    for app in apps_to_migrate:
        print(f"\nCreating migrations for {app}...")
        try:
            execute_from_command_line([
                'manage.py',
                'makemigrations',
                app,
                '--name=add_data_integrity_constraints'
            ])
            print(f"✅ Migration created for {app}")
        except Exception as e:
            print(f"❌ Failed to create migration for {app}: {e}")

    # Show migration status
    print("\nMigration status:")
    try:
        execute_from_command_line(['manage.py', 'showmigrations'])
    except Exception as e:
        print(f"Error showing migrations: {e}")


if __name__ == '__main__':
    create_migrations()