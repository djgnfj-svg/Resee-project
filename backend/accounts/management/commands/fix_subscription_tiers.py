#!/usr/bin/env python3
"""
Management command to fix subscription tier data inconsistencies
Infers tier from max_interval_days when tier is empty or invalid
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Subscription, SubscriptionTier


class Command(BaseCommand):
    help = 'Fix subscription tiers by inferring from max_interval_days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Map max_interval_days to tier
        interval_to_tier = {
            3: SubscriptionTier.FREE,
            90: SubscriptionTier.BASIC,
            180: SubscriptionTier.PRO,
        }

        # Find subscriptions with invalid or empty tiers
        valid_tiers = [choice[0] for choice in SubscriptionTier.choices]
        invalid_subscriptions = Subscription.objects.exclude(tier__in=valid_tiers)

        total_count = invalid_subscriptions.count()

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No invalid subscription tiers found!'))
            return

        self.stdout.write(f'Found {total_count} subscriptions with invalid tiers:')

        # Group by current tier value and max_interval_days
        updates_to_make = []

        for subscription in invalid_subscriptions.select_related('user'):
            current_tier = subscription.tier or '(empty)'
            max_days = subscription.max_interval_days

            # Infer correct tier from max_interval_days
            inferred_tier = interval_to_tier.get(max_days)

            if inferred_tier:
                self.stdout.write(
                    f'  - {subscription.user.email}: '
                    f'tier="{current_tier}" → "{inferred_tier}" '
                    f'(max_interval_days={max_days})'
                )
                updates_to_make.append((subscription, inferred_tier))
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  - {subscription.user.email}: '
                        f'tier="{current_tier}", max_interval_days={max_days} '
                        f'(NO MATCHING TIER - skipping)'
                    )
                )

        if not updates_to_make:
            self.stdout.write(self.style.WARNING('No valid updates to make'))
            return

        # Confirm before making changes (unless dry-run)
        if not dry_run:
            self.stdout.write('')
            confirm = input(f'Update {len(updates_to_make)} subscriptions? (yes/no): ')

            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Update cancelled'))
                return

            # Perform updates in transaction
            with transaction.atomic():
                updated_count = 0
                for subscription, new_tier in updates_to_make:
                    subscription.tier = new_tier
                    subscription.save()
                    updated_count += 1

                self.stdout.write(
                    self.style.SUCCESS(f'\nSuccessfully updated {updated_count} subscriptions!')
                )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\nDRY RUN: Would update {len(updates_to_make)} subscriptions')
            )

        # Show final distribution
        self.stdout.write('\nCurrent subscription distribution:')
        for tier_choice in SubscriptionTier.choices:
            tier_code = tier_choice[0]
            count = Subscription.objects.filter(tier=tier_code).count()
            tier_display = dict(SubscriptionTier.choices)[tier_code]
            self.stdout.write(f'  {tier_display}: {count}')
