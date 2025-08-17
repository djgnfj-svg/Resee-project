#!/usr/bin/env python3
"""
Management command to update subscription tiers from 4-tier to 3-tier system
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Subscription, SubscriptionTier


class Command(BaseCommand):
    help = 'Update subscription tiers from 4-tier to 3-tier system'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Update any PREMIUM subscriptions to BASIC
            # Since PREMIUM had max 60 days, BASIC now has max 90 days (upgrade)
            premium_subscriptions = Subscription.objects.filter(tier='premium')
            premium_count = premium_subscriptions.count()
            
            if premium_count > 0:
                self.stdout.write(f"Found {premium_count} PREMIUM subscriptions to update...")
                premium_subscriptions.update(
                    tier=SubscriptionTier.BASIC,
                    max_interval_days=90
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Updated {premium_count} PREMIUM subscriptions to BASIC")
                )
            else:
                self.stdout.write("No PREMIUM subscriptions found.")
            
            # Update FREE subscriptions to have max_interval_days=3
            free_subscriptions = Subscription.objects.filter(
                tier=SubscriptionTier.FREE
            ).exclude(max_interval_days=3)
            free_count = free_subscriptions.count()
            
            if free_count > 0:
                self.stdout.write(f"Found {free_count} FREE subscriptions with incorrect max_interval_days...")
                free_subscriptions.update(max_interval_days=3)
                self.stdout.write(
                    self.style.SUCCESS(f"Updated {free_count} FREE subscriptions to max_interval_days=3")
                )
            else:
                self.stdout.write("All FREE subscriptions already have correct max_interval_days.")
            
            # Verify current state
            tier_counts = {}
            for tier_choice in SubscriptionTier.choices:
                tier_code = tier_choice[0]
                count = Subscription.objects.filter(tier=tier_code).count()
                tier_counts[tier_code] = count
            
            self.stdout.write("\nCurrent subscription distribution:")
            for tier_code, count in tier_counts.items():
                tier_display = dict(SubscriptionTier.choices)[tier_code]
                self.stdout.write(f"  {tier_display}: {count}")
            
            self.stdout.write(
                self.style.SUCCESS("\nSubscription tier update completed successfully!")
            )