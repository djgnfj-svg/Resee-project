#!/usr/bin/env python
"""
User Data Backup Script for Resee Project
Exports critical user data to JSON format for additional safety
"""

import os
import sys
import json
import gzip
from datetime import datetime, timezone
from pathlib import Path

# Add Django project to Python path
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resee.settings.production')

import django
django.setup()

from django.contrib.auth import get_user_model
from django.core import serializers
from content.models import Content, Category
from review.models import ReviewSchedule, ReviewHistory
from accounts.models import Subscription

User = get_user_model()

class UserDataBackup:
    """Handles user data backup operations"""

    def __init__(self, backup_dir="/backups/user_data"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    def log(self, message):
        """Log message with timestamp"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

    def backup_users(self):
        """Backup user accounts and subscriptions"""
        self.log("Backing up users and subscriptions...")

        users_data = []
        for user in User.objects.all().prefetch_related('subscription'):
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'date_joined': user.date_joined.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'is_email_verified': getattr(user, 'is_email_verified', False),
                'subscription': {
                    'tier': user.subscription.tier,
                    'start_date': user.subscription.start_date.isoformat(),
                    'end_date': user.subscription.end_date.isoformat() if user.subscription.end_date else None,
                    'is_active': user.subscription.is_active,
                } if hasattr(user, 'subscription') else None
            }
            users_data.append(user_data)

        return users_data

    def backup_content(self):
        """Backup user content and categories"""
        self.log("Backing up content and categories...")

        # Backup categories
        categories_data = []
        for category in Category.objects.all().select_related('user'):
            category_data = {
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'description': category.description,
                'user_id': category.user_id,
                'created_at': category.created_at.isoformat(),
                'updated_at': category.updated_at.isoformat(),
            }
            categories_data.append(category_data)

        # Backup content
        content_data = []
        for content in Content.objects.all().select_related('author', 'category'):
            content_item = {
                'id': content.id,
                'title': content.title,
                'content': content.content,
                'author_id': content.author_id,
                'category_id': content.category_id,
                'priority': content.priority,
                'created_at': content.created_at.isoformat(),
                'updated_at': content.updated_at.isoformat(),
            }
            content_data.append(content_item)

        return {
            'categories': categories_data,
            'content': content_data
        }

    def backup_reviews(self):
        """Backup review schedules and history"""
        self.log("Backing up review schedules and history...")

        # Backup review schedules
        schedules_data = []
        for schedule in ReviewSchedule.objects.all().select_related('user', 'content'):
            schedule_data = {
                'id': schedule.id,
                'user_id': schedule.user_id,
                'content_id': schedule.content_id,
                'interval_index': schedule.interval_index,
                'next_review_date': schedule.next_review_date.isoformat(),
                'initial_review_completed': schedule.initial_review_completed,
                'is_active': schedule.is_active,
                'created_at': schedule.created_at.isoformat(),
                'updated_at': schedule.updated_at.isoformat(),
            }
            schedules_data.append(schedule_data)

        # Backup review history
        history_data = []
        for history in ReviewHistory.objects.all().select_related('user', 'content'):
            history_item = {
                'id': history.id,
                'user_id': history.user_id,
                'content_id': history.content_id,
                'result': history.result,
                'review_date': history.review_date.isoformat(),
                'time_spent': history.time_spent,
                'notes': history.notes,
                'created_at': history.created_at.isoformat(),
            }
            history_data.append(history_item)

        return {
            'schedules': schedules_data,
            'history': history_data
        }

    def get_statistics(self):
        """Get backup statistics"""
        stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'total_content': Content.objects.count(),
            'total_categories': Category.objects.count(),
            'total_schedules': ReviewSchedule.objects.count(),
            'active_schedules': ReviewSchedule.objects.filter(is_active=True).count(),
            'total_review_history': ReviewHistory.objects.count(),
            'subscriptions_by_tier': {
                tier: Subscription.objects.filter(tier=tier).count()
                for tier in ['FREE', 'BASIC', 'PREMIUM', 'PRO']
            }
        }
        return stats

    def create_backup(self, compress=True):
        """Create complete user data backup"""
        self.log("Starting user data backup...")

        # Collect all data
        backup_data = {
            'backup_info': {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'backup_type': 'user_data',
                'version': '1.0',
                'django_version': django.get_version(),
            },
            'statistics': self.get_statistics(),
            'users': self.backup_users(),
            'content': self.backup_content(),
            'reviews': self.backup_reviews(),
        }

        # Save to file
        filename = f"user_data_backup_{self.timestamp}.json"
        if compress:
            filename += ".gz"

        filepath = self.backup_dir / filename

        try:
            if compress:
                with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)

            # Create metadata file
            metadata = {
                'backup_timestamp': backup_data['backup_info']['timestamp'],
                'backup_file': filename,
                'backup_size_bytes': filepath.stat().st_size,
                'backup_compressed': compress,
                'statistics': backup_data['statistics']
            }

            metadata_file = filepath.with_suffix(filepath.suffix + '.meta')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            self.log(f"SUCCESS: User data backup completed - {filename}")
            self.log(f"Backup size: {self.format_size(filepath.stat().st_size)}")
            self.log(f"Total users: {backup_data['statistics']['total_users']}")
            self.log(f"Total content: {backup_data['statistics']['total_content']}")
            self.log(f"Total reviews: {backup_data['statistics']['total_review_history']}")

            return filepath

        except Exception as e:
            self.log(f"ERROR: Failed to create backup - {str(e)}")
            raise

    def format_size(self, bytes_size):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"

    def cleanup_old_backups(self, retention_days=30):
        """Clean up old backup files"""
        self.log(f"Cleaning up backups older than {retention_days} days...")

        cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
        cleaned_count = 0

        for file in self.backup_dir.glob("user_data_backup_*.json*"):
            if file.stat().st_mtime < cutoff_time:
                file.unlink()
                cleaned_count += 1

                # Also remove metadata file if exists
                meta_file = file.with_suffix(file.suffix + '.meta')
                if meta_file.exists():
                    meta_file.unlink()

        self.log(f"Cleaned up {cleaned_count} old backup files")


def main():
    """Main backup execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Backup Resee user data')
    parser.add_argument('--no-compress', action='store_true', help='Don\'t compress backup files')
    parser.add_argument('--retention-days', type=int, default=30, help='Retention period for old backups')
    parser.add_argument('--backup-dir', default='/backups/user_data', help='Backup directory')

    args = parser.parse_args()

    try:
        backup = UserDataBackup(args.backup_dir)
        backup.create_backup(compress=not args.no_compress)
        backup.cleanup_old_backups(args.retention_days)

        print("\n=== USER DATA BACKUP COMPLETE ===")
        return 0

    except Exception as e:
        print(f"\n=== BACKUP FAILED: {str(e)} ===")
        return 1


if __name__ == '__main__':
    sys.exit(main())