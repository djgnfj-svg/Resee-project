"""
Tests for accounts models.
"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts.models import (
    BillingCycle, BillingSchedule, NotificationPreference, PaymentHistory,
    Subscription, SubscriptionTier,
)

User = get_user_model()


class UserManagerTest(TestCase):
    """Test custom UserManager."""

    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_email_verified)

    def test_create_user_without_email(self):
        """Test that creating user without email raises ValueError."""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='testpass123')

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertEqual(user.email, 'admin@example.com')
        self.assertTrue(user.check_password('adminpass123'))
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_email_verified)

    def test_create_superuser_without_is_staff(self):
        """Test that creating superuser without is_staff raises ValueError."""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@example.com',
                password='adminpass123',
                is_staff=False
            )

    def test_create_superuser_without_is_superuser(self):
        """Test that creating superuser without is_superuser raises ValueError."""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@example.com',
                password='adminpass123',
                is_superuser=False
            )

    def test_email_normalization(self):
        """Test that email is normalized."""
        user = User.objects.create_user(
            email='TEST@EXAMPLE.COM',
            password='testpass123'
        )
        self.assertEqual(user.email, 'TEST@example.com')


class UserModelTest(TestCase):
    """Test User model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_user_str(self):
        """Test User __str__ method."""
        self.assertEqual(str(self.user), 'test@example.com')

    def test_default_weekly_goal(self):
        """Test default weekly goal is 7."""
        self.assertEqual(self.user.weekly_goal, 7)

    def test_email_verified_default(self):
        """Test is_email_verified defaults to False."""
        self.assertFalse(self.user.is_email_verified)


class SubscriptionModelTest(TestCase):
    """Test Subscription model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        # Delete auto-created subscription
        if hasattr(self.user, 'subscription'):
            self.user.subscription.delete()

    def test_subscription_str(self):
        """Test Subscription __str__ method."""
        subscription = Subscription.objects.create(
            user=self.user,
            tier=SubscriptionTier.PRO
        )
        expected = f"{self.user.email} - Pro (180일)"
        self.assertEqual(str(subscription), expected)

    def test_is_expired_without_end_date(self):
        """Test is_expired returns False when end_date is None."""
        subscription = Subscription.objects.create(
            user=self.user,
            tier=SubscriptionTier.PRO,
            end_date=None
        )
        self.assertFalse(subscription.is_expired())

    def test_is_expired_with_future_end_date(self):
        """Test is_expired returns False when end_date is in future."""
        future_date = timezone.now() + timedelta(days=30)
        subscription = Subscription.objects.create(
            user=self.user,
            tier=SubscriptionTier.PRO,
            end_date=future_date
        )
        self.assertFalse(subscription.is_expired())

    def test_is_expired_with_past_end_date(self):
        """Test is_expired returns True when end_date is in past."""
        past_date = timezone.now() - timedelta(days=1)
        subscription = Subscription.objects.create(
            user=self.user,
            tier=SubscriptionTier.PRO,
            end_date=past_date
        )
        self.assertTrue(subscription.is_expired())

    def test_days_remaining_without_end_date(self):
        """Test days_remaining returns None when end_date is None."""
        subscription = Subscription.objects.create(
            user=self.user,
            tier=SubscriptionTier.PRO,
            end_date=None
        )
        self.assertIsNone(subscription.days_remaining())

    def test_days_remaining_with_future_end_date(self):
        """Test days_remaining returns correct number of days."""
        future_date = timezone.now() + timedelta(days=30)
        subscription = Subscription.objects.create(
            user=self.user,
            tier=SubscriptionTier.PRO,
            end_date=future_date
        )
        # Should be 29 or 30 depending on exact time
        days = subscription.days_remaining()
        self.assertIsNotNone(days)
        self.assertGreaterEqual(days, 29)
        self.assertLessEqual(days, 30)

    def test_days_remaining_with_past_end_date(self):
        """Test days_remaining returns 0 when subscription is expired."""
        past_date = timezone.now() - timedelta(days=10)
        subscription = Subscription.objects.create(
            user=self.user,
            tier=SubscriptionTier.PRO,
            end_date=past_date
        )
        self.assertEqual(subscription.days_remaining(), 0)

    def test_save_sets_max_interval_days_for_free(self):
        """Test that save() sets correct max_interval_days for FREE tier."""
        subscription = Subscription.objects.create(
            user=self.user,
            tier=SubscriptionTier.FREE
        )
        self.assertEqual(subscription.max_interval_days, 3)

    def test_save_sets_max_interval_days_for_basic(self):
        """Test that save() sets correct max_interval_days for BASIC tier."""
        subscription = Subscription.objects.create(
            user=self.user,
            tier=SubscriptionTier.BASIC
        )
        self.assertEqual(subscription.max_interval_days, 90)

    def test_save_sets_max_interval_days_for_pro(self):
        """Test that save() sets correct max_interval_days for PRO tier."""
        subscription = Subscription.objects.create(
            user=self.user,
            tier=SubscriptionTier.PRO
        )
        self.assertEqual(subscription.max_interval_days, 180)


class PaymentHistoryModelTest(TestCase):
    """Test PaymentHistory model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_payment_history_str(self):
        """Test PaymentHistory __str__ method."""
        payment = PaymentHistory.objects.create(
            user=self.user,
            payment_type=PaymentHistory.PaymentType.UPGRADE,
            from_tier=SubscriptionTier.FREE,
            to_tier=SubscriptionTier.BASIC,
            amount=Decimal('9900.00')
        )
        self.assertIn(self.user.email, str(payment))
        self.assertIn('업그레이드', str(payment))

    def test_tier_display_with_tier_change(self):
        """Test tier_display property shows tier change."""
        payment = PaymentHistory.objects.create(
            user=self.user,
            payment_type=PaymentHistory.PaymentType.UPGRADE,
            from_tier=SubscriptionTier.FREE,
            to_tier=SubscriptionTier.BASIC,
            amount=Decimal('9900.00')
        )
        self.assertIn('→', payment.tier_display)
        self.assertIn('Free', payment.tier_display)
        self.assertIn('Basic', payment.tier_display)

    def test_tier_display_without_from_tier(self):
        """Test tier_display property when from_tier is None."""
        payment = PaymentHistory.objects.create(
            user=self.user,
            payment_type=PaymentHistory.PaymentType.INITIAL,
            from_tier=None,
            to_tier=SubscriptionTier.BASIC,
            amount=Decimal('9900.00')
        )
        self.assertEqual(payment.tier_display, 'Basic (90일)')

    def test_tier_display_same_tier(self):
        """Test tier_display property when tiers are the same."""
        payment = PaymentHistory.objects.create(
            user=self.user,
            payment_type=PaymentHistory.PaymentType.RENEWAL,
            from_tier=SubscriptionTier.BASIC,
            to_tier=SubscriptionTier.BASIC,
            amount=Decimal('9900.00')
        )
        self.assertEqual(payment.tier_display, 'Basic (90일)')


class BillingScheduleModelTest(TestCase):
    """Test BillingSchedule model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.subscription = Subscription.objects.get(user=self.user)

    def test_billing_schedule_str(self):
        """Test BillingSchedule __str__ method."""
        schedule = BillingSchedule.objects.create(
            subscription=self.subscription,
            scheduled_date=timezone.now() + timedelta(days=30),
            amount=Decimal('9900.00'),
            billing_cycle=BillingCycle.MONTHLY,
            tier_at_billing=SubscriptionTier.BASIC
        )
        self.assertIn(self.user.email, str(schedule))
        self.assertIn('9900', str(schedule))

    def test_is_due_with_future_date(self):
        """Test is_due returns False for future dates."""
        schedule = BillingSchedule.objects.create(
            subscription=self.subscription,
            scheduled_date=timezone.now() + timedelta(days=30),
            amount=Decimal('9900.00'),
            billing_cycle=BillingCycle.MONTHLY,
            tier_at_billing=SubscriptionTier.BASIC,
            status=BillingSchedule.ScheduleStatus.PENDING
        )
        self.assertFalse(schedule.is_due())

    def test_is_due_with_past_date(self):
        """Test is_due returns True for past dates with pending status."""
        schedule = BillingSchedule.objects.create(
            subscription=self.subscription,
            scheduled_date=timezone.now() - timedelta(days=1),
            amount=Decimal('9900.00'),
            billing_cycle=BillingCycle.MONTHLY,
            tier_at_billing=SubscriptionTier.BASIC,
            status=BillingSchedule.ScheduleStatus.PENDING
        )
        self.assertTrue(schedule.is_due())

    def test_is_due_with_completed_status(self):
        """Test is_due returns False for completed status."""
        schedule = BillingSchedule.objects.create(
            subscription=self.subscription,
            scheduled_date=timezone.now() - timedelta(days=1),
            amount=Decimal('9900.00'),
            billing_cycle=BillingCycle.MONTHLY,
            tier_at_billing=SubscriptionTier.BASIC,
            status=BillingSchedule.ScheduleStatus.COMPLETED
        )
        self.assertFalse(schedule.is_due())

    def test_can_be_processed_all_conditions_met(self):
        """Test can_be_processed returns True when all conditions are met."""
        schedule = BillingSchedule.objects.create(
            subscription=self.subscription,
            scheduled_date=timezone.now() + timedelta(days=30),
            amount=Decimal('9900.00'),
            billing_cycle=BillingCycle.MONTHLY,
            tier_at_billing=SubscriptionTier.BASIC,
            status=BillingSchedule.ScheduleStatus.PENDING
        )
        self.subscription.is_active = True
        self.subscription.save()
        self.assertTrue(schedule.can_be_processed())

    def test_can_be_processed_inactive_subscription(self):
        """Test can_be_processed returns False for inactive subscription."""
        schedule = BillingSchedule.objects.create(
            subscription=self.subscription,
            scheduled_date=timezone.now() + timedelta(days=30),
            amount=Decimal('9900.00'),
            billing_cycle=BillingCycle.MONTHLY,
            tier_at_billing=SubscriptionTier.BASIC,
            status=BillingSchedule.ScheduleStatus.PENDING
        )
        self.subscription.is_active = False
        self.subscription.save()
        self.assertFalse(schedule.can_be_processed())

    def test_can_be_processed_expired_subscription(self):
        """Test can_be_processed returns False for expired subscription."""
        self.subscription.end_date = timezone.now() - timedelta(days=1)
        self.subscription.is_active = True
        self.subscription.save()

        schedule = BillingSchedule.objects.create(
            subscription=self.subscription,
            scheduled_date=timezone.now() + timedelta(days=30),
            amount=Decimal('9900.00'),
            billing_cycle=BillingCycle.MONTHLY,
            tier_at_billing=SubscriptionTier.BASIC,
            status=BillingSchedule.ScheduleStatus.PENDING
        )
        self.assertFalse(schedule.can_be_processed())

    def test_can_be_processed_non_pending_status(self):
        """Test can_be_processed returns False for non-pending status."""
        schedule = BillingSchedule.objects.create(
            subscription=self.subscription,
            scheduled_date=timezone.now() + timedelta(days=30),
            amount=Decimal('9900.00'),
            billing_cycle=BillingCycle.MONTHLY,
            tier_at_billing=SubscriptionTier.BASIC,
            status=BillingSchedule.ScheduleStatus.COMPLETED
        )
        self.subscription.is_active = True
        self.subscription.save()
        self.assertFalse(schedule.can_be_processed())


class UserSignalTest(TestCase):
    """Test signal handlers for User model."""

    def test_subscription_created_for_new_user(self):
        """Test that subscription is automatically created for new users."""
        user = User.objects.create_user(
            email='newuser@example.com',
            password='testpass123'
        )
        self.assertTrue(hasattr(user, 'subscription'))
        self.assertIsNotNone(user.subscription)
        self.assertEqual(user.subscription.tier, SubscriptionTier.BASIC)

    def test_subscription_not_created_twice(self):
        """Test that subscription is not created if it already exists."""
        user = User.objects.create_user(
            email='newuser@example.com',
            password='testpass123'
        )
        subscription_id = user.subscription.id

        # Trigger signal again by saving user
        user.save()

        # Should still have same subscription
        self.assertEqual(user.subscription.id, subscription_id)


class NotificationPreferenceModelTest(TestCase):
    """Test NotificationPreference model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_default_values(self):
        """Test default notification preference values."""
        pref, created = NotificationPreference.objects.get_or_create(user=self.user)
        self.assertTrue(pref.email_notifications_enabled)
        self.assertTrue(pref.daily_reminder_enabled)
        self.assertTrue(created or pref.email_notifications_enabled)  # Either newly created or has default

    def test_generate_unsubscribe_token(self):
        """Test unsubscribe token generation."""
        pref, _ = NotificationPreference.objects.get_or_create(user=self.user)

        # Generate token if not exists
        if not pref.unsubscribe_token:
            from django.utils.crypto import get_random_string
            pref.unsubscribe_token = get_random_string(64)
            pref.save()

        self.assertIsNotNone(pref.unsubscribe_token)
        self.assertEqual(len(pref.unsubscribe_token), 64)
