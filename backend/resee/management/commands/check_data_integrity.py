"""
Django management command to check and repair data integrity issues
"""
import logging
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.db import transaction, models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from accounts.models import Subscription, PaymentHistory, AIUsageTracking, EmailSubscription
from content.models import Content, Category
from review.models import ReviewSchedule, ReviewHistory
from resee.validators import DataIntegrityValidator

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check and repair data integrity issues in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix issues automatically (use with caution)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )
        parser.add_argument(
            '--check',
            choices=['users', 'subscriptions', 'content', 'reviews', 'all'],
            default='all',
            help='Which data to check (default: all)'
        )
        parser.add_argument(
            '--orphaned',
            action='store_true',
            help='Check for orphaned records'
        )

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']
        self.fix_issues = options['fix']
        self.check_orphaned = options['orphaned']
        self.check_type = options['check']

        self.stdout.write(self.style.SUCCESS('Starting data integrity check...'))

        if self.fix_issues:
            self.stdout.write(self.style.WARNING('⚠️  FIX MODE ENABLED - Changes will be made to the database'))

        total_issues = 0

        if self.check_type in ['users', 'all']:
            total_issues += self.check_users()

        if self.check_type in ['subscriptions', 'all']:
            total_issues += self.check_subscriptions()

        if self.check_type in ['content', 'all']:
            total_issues += self.check_content()

        if self.check_type in ['reviews', 'all']:
            total_issues += self.check_reviews()

        if self.check_orphaned:
            total_issues += self.check_orphaned_records()

        # Summary
        if total_issues == 0:
            self.stdout.write(self.style.SUCCESS('✅ No data integrity issues found!'))
        else:
            status_style = self.style.WARNING if self.fix_issues else self.style.ERROR
            action_text = "fixed" if self.fix_issues else "found"
            self.stdout.write(status_style(f'📊 Total issues {action_text}: {total_issues}'))

    def check_users(self):
        """Check user data integrity"""
        self.stdout.write('Checking users...')
        issues_found = 0

        for user in User.objects.all():
            errors = DataIntegrityValidator.validate_user_subscription_consistency(user)

            if errors:
                issues_found += len(errors)
                self.stdout.write(
                    self.style.ERROR(f'❌ User {user.email} has {len(errors)} issues:')
                )

                for error in errors:
                    self.stdout.write(f'   - {error.message} (code: {error.code})')

                    if self.fix_issues:
                        self.fix_user_issue(user, error)

            # Check for users without subscriptions
            if not hasattr(user, 'subscription'):
                issues_found += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ User {user.email} has no subscription')
                )

                if self.fix_issues:
                    self.create_default_subscription(user)

        return issues_found

    def check_subscriptions(self):
        """Check subscription data integrity"""
        self.stdout.write('Checking subscriptions...')
        issues_found = 0

        # Check for expired subscriptions that are still active
        expired_active = Subscription.objects.filter(
            is_active=True,
            end_date__lt=timezone.now()
        )

        for subscription in expired_active:
            issues_found += 1
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Subscription {subscription.id} for {subscription.user.email} '
                    f'is active but expired ({subscription.end_date})'
                )
            )

            if self.fix_issues:
                subscription.is_active = False
                subscription.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Deactivated expired subscription for {subscription.user.email}')
                )

        # Check for missing billing schedules for auto-renewal
        auto_renewal_missing_billing = Subscription.objects.filter(
            is_active=True,
            auto_renewal=True,
            next_billing_date__isnull=True
        ).exclude(tier='free')

        for subscription in auto_renewal_missing_billing:
            issues_found += 1
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Subscription {subscription.id} for {subscription.user.email} '
                    f'has auto-renewal but no next billing date'
                )
            )

            if self.fix_issues:
                # Set next billing date to 30 days from now for monthly, 365 for yearly
                days = 30 if subscription.billing_cycle == 'monthly' else 365
                subscription.next_billing_date = timezone.now() + timedelta(days=days)
                subscription.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Set next billing date for {subscription.user.email}')
                )

        return issues_found

    def check_content(self):
        """Check content data integrity"""
        self.stdout.write('Checking content...')
        issues_found = 0

        # Check for content without review schedules
        content_without_schedules = Content.objects.filter(
            reviewschedule__isnull=True
        )

        for content in content_without_schedules:
            issues_found += 1
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Content {content.id} "{content.title}" has no review schedule'
                )
            )

            if self.fix_issues:
                self.create_review_schedule(content)

        # Check for empty content
        empty_content = Content.objects.filter(
            models.Q(content='') | models.Q(content__isnull=True) |
            models.Q(title='') | models.Q(title__isnull=True)
        )

        for content in empty_content:
            issues_found += 1
            self.stdout.write(
                self.style.ERROR(f'❌ Content {content.id} has empty title or content')
            )

            if self.fix_issues:
                # Mark as inactive or delete if really empty
                if not content.title and not content.content:
                    content.delete()
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Deleted empty content {content.id}')
                    )

        return issues_found

    def check_reviews(self):
        """Check review data integrity"""
        self.stdout.write('Checking reviews...')
        issues_found = 0

        # Check review schedules
        for schedule in ReviewSchedule.objects.select_related('user', 'content').all():
            errors = DataIntegrityValidator.validate_review_schedule_consistency(schedule)

            if errors:
                issues_found += len(errors)
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Review schedule {schedule.id} for content "{schedule.content.title}" '
                        f'has {len(errors)} issues:'
                    )
                )

                for error in errors:
                    self.stdout.write(f'   - {error.message} (code: {error.code})')

                    if self.fix_issues:
                        self.fix_review_schedule_issue(schedule, error)

        # Check for review schedules with invalid intervals
        invalid_intervals = ReviewSchedule.objects.filter(
            interval_index__lt=0
        )

        for schedule in invalid_intervals:
            issues_found += 1
            self.stdout.write(
                self.style.ERROR(f'❌ Review schedule {schedule.id} has negative interval index')
            )

            if self.fix_issues:
                schedule.interval_index = 0
                schedule.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Fixed interval index for schedule {schedule.id}')
                )

        return issues_found

    def check_orphaned_records(self):
        """Check for orphaned records"""
        self.stdout.write('Checking for orphaned records...')
        issues_found = 0

        # Check for AI usage records without users
        orphaned_ai_usage = AIUsageTracking.objects.filter(user__isnull=True)
        if orphaned_ai_usage.exists():
            count = orphaned_ai_usage.count()
            issues_found += count
            self.stdout.write(
                self.style.ERROR(f'❌ Found {count} orphaned AI usage records')
            )

            if self.fix_issues:
                orphaned_ai_usage.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Deleted {count} orphaned AI usage records')
                )

        # Check for payment history without users
        orphaned_payments = PaymentHistory.objects.filter(user__isnull=True)
        if orphaned_payments.exists():
            count = orphaned_payments.count()
            issues_found += count
            self.stdout.write(
                self.style.ERROR(f'❌ Found {count} orphaned payment history records')
            )

            if self.fix_issues:
                orphaned_payments.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Deleted {count} orphaned payment history records')
                )

        # Check for review schedules without content
        orphaned_schedules = ReviewSchedule.objects.filter(content__isnull=True)
        if orphaned_schedules.exists():
            count = orphaned_schedules.count()
            issues_found += count
            self.stdout.write(
                self.style.ERROR(f'❌ Found {count} orphaned review schedules')
            )

            if self.fix_issues:
                orphaned_schedules.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Deleted {count} orphaned review schedules')
                )

        return issues_found

    def fix_user_issue(self, user, error):
        """Fix user-related issues"""
        if error.code == 'missing_subscription':
            self.create_default_subscription(user)

    def fix_review_schedule_issue(self, schedule, error):
        """Fix review schedule issues"""
        if error.code == 'interval_exceeds_subscription':
            # Reset to valid interval
            from review.utils import get_review_intervals
            intervals = get_review_intervals(schedule.user)
            schedule.interval_index = min(schedule.interval_index, len(intervals) - 1)
            schedule.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Fixed interval index for schedule {schedule.id}')
            )

        elif error.code == 'review_date_before_creation':
            # Reset next review date
            schedule.next_review_date = timezone.now() + timedelta(days=1)
            schedule.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Fixed review date for schedule {schedule.id}')
            )

    def create_default_subscription(self, user):
        """Create default free subscription for user"""
        try:
            with transaction.atomic():
                subscription = Subscription.objects.create(
                    user=user,
                    tier='free',
                    max_interval_days=3
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created default subscription for {user.email}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to create subscription for {user.email}: {str(e)}')
            )

    def create_review_schedule(self, content):
        """Create missing review schedule for content"""
        try:
            from review.models import ReviewSchedule
            from review.utils import get_review_intervals
            from django.utils import timezone

            with transaction.atomic():
                ReviewSchedule.objects.create(
                    user=content.author,
                    content=content,
                    interval_index=0,
                    next_review_date=timezone.now() + timedelta(days=1),
                    initial_review_completed=False,
                    is_active=True
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created review schedule for content "{content.title}"')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Failed to create review schedule for content "{content.title}": {str(e)}'
                )
            )