"""
Billing schedule management service
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from django.db import transaction
from django.utils import timezone

from ..models import Subscription, BillingSchedule, PaymentHistory, SubscriptionTier, BillingCycle


class BillingScheduleService:
    """Service for managing billing schedules and future payments"""
    
    @staticmethod
    def create_billing_schedule(subscription: Subscription) -> Optional[BillingSchedule]:
        """Create a billing schedule entry for the next payment"""
        if not subscription.is_active or subscription.is_expired:
            return None
            
        # Calculate next billing date based on billing cycle
        if subscription.billing_cycle == BillingCycle.YEARLY:
            next_billing_date = subscription.end_date or (timezone.now() + timedelta(days=365))
        else:  # Monthly
            next_billing_date = subscription.end_date or (timezone.now() + timedelta(days=30))
        
        # Get pricing based on tier and billing cycle
        amount = BillingScheduleService.get_tier_price(subscription.tier, subscription.billing_cycle)
        
        # Check if schedule already exists
        existing_schedule = BillingSchedule.objects.filter(
            subscription=subscription,
            status=BillingSchedule.ScheduleStatus.PENDING
        ).first()
        
        if existing_schedule:
            # Update existing schedule
            existing_schedule.scheduled_date = next_billing_date
            existing_schedule.amount = amount
            existing_schedule.billing_cycle = subscription.billing_cycle
            existing_schedule.save()
            return existing_schedule
        
        # Create new schedule
        return BillingSchedule.objects.create(
            subscription=subscription,
            scheduled_date=next_billing_date,
            amount=amount,
            billing_cycle=subscription.billing_cycle,
            status=BillingSchedule.ScheduleStatus.PENDING
        )
    
    @staticmethod
    def get_tier_price(tier: str, billing_cycle: str) -> Decimal:
        """Get price for a tier with billing cycle discount"""
        base_prices = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.BASIC: 5000,
            SubscriptionTier.PRO: 20000,
        }
        
        base_price = base_prices.get(tier, 0)
        
        if billing_cycle == BillingCycle.YEARLY and base_price > 0:
            # 20% discount for yearly billing
            return Decimal(str(base_price * 12 * 0.8))
        
        return Decimal(str(base_price))
    
    @staticmethod
    def get_upcoming_payments(subscription: Subscription) -> List[BillingSchedule]:
        """Get upcoming payments for a subscription"""
        return BillingSchedule.objects.filter(
            subscription=subscription,
            status=BillingSchedule.ScheduleStatus.PENDING,
            scheduled_date__gte=timezone.now()
        ).order_by('scheduled_date')
    
    @staticmethod
    def process_scheduled_payment(schedule: BillingSchedule) -> bool:
        """
        Process a scheduled payment (simulation for now)
        In a real implementation, this would integrate with payment gateway
        """
        with transaction.atomic():
            try:
                # Create payment history record
                PaymentHistory.objects.create(
                    user=schedule.subscription.user,
                    payment_type=PaymentHistory.PaymentType.RENEWAL,
                    to_tier=schedule.subscription.tier,
                    amount=schedule.amount,
                    description=f"{schedule.subscription.get_tier_display()} 구독 갱신 ({schedule.get_billing_cycle_display()})",
                    billing_cycle=schedule.billing_cycle
                )
                
                # Update subscription
                subscription = schedule.subscription
                if schedule.billing_cycle == BillingCycle.YEARLY:
                    subscription.end_date = subscription.end_date + timedelta(days=365)
                else:
                    subscription.end_date = subscription.end_date + timedelta(days=30)
                
                subscription.amount_paid = schedule.amount
                subscription.save()
                
                # Mark schedule as processed
                schedule.status = BillingSchedule.ScheduleStatus.PROCESSED
                schedule.processed_at = timezone.now()
                schedule.save()
                
                # Create next billing schedule
                BillingScheduleService.create_billing_schedule(subscription)
                
                return True
                
            except Exception:
                # Mark schedule as failed
                schedule.status = BillingSchedule.ScheduleStatus.FAILED
                schedule.save()
                return False
    
    @staticmethod
    def cancel_pending_schedules(subscription: Subscription) -> int:
        """Cancel all pending billing schedules for a subscription"""
        pending_schedules = BillingSchedule.objects.filter(
            subscription=subscription,
            status=BillingSchedule.ScheduleStatus.PENDING
        )
        
        count = pending_schedules.count()
        pending_schedules.update(
            status=BillingSchedule.ScheduleStatus.CANCELLED,
            processed_at=timezone.now()
        )
        
        return count
    
    @staticmethod
    def update_billing_schedules_on_change(subscription: Subscription, old_tier: str = None):
        """Update billing schedules when subscription changes"""
        # Cancel existing pending schedules
        BillingScheduleService.cancel_pending_schedules(subscription)
        
        # Create new schedule if subscription is still active
        if subscription.is_active and not subscription.is_expired:
            BillingScheduleService.create_billing_schedule(subscription)