"""
Utility functions for subscription tier operations.

Provides functions for:
- Tier hierarchy and comparison
- Pricing calculations
- Feature and limit lookups
- Tier validation
"""
from decimal import Decimal
from typing import Dict, List

from ..constants import (
    BILLING_CYCLE_DAYS, CATEGORY_LIMITS, CONTENT_LIMITS, TIER_FEATURES,
    TIER_HIERARCHY, TIER_MAX_INTERVALS, TIER_MONTHLY_PRICES,
    YEARLY_DISCOUNT_RATE,
)
from ..models import BillingCycle, SubscriptionTier


def get_tier_level(tier: str) -> int:
    """
    Get numeric level for a tier.

    Args:
        tier: Subscription tier (FREE, BASIC, PRO)

    Returns:
        Numeric level (0=FREE, 1=BASIC, 2=PRO)
    """
    return TIER_HIERARCHY.get(tier, 0)


def is_upgrade(from_tier: str, to_tier: str) -> bool:
    """
    Check if tier change is an upgrade.

    Args:
        from_tier: Current tier
        to_tier: Target tier

    Returns:
        True if upgrade, False otherwise
    """
    from_level = get_tier_level(from_tier)
    to_level = get_tier_level(to_tier)
    return to_level > from_level


def is_downgrade(from_tier: str, to_tier: str) -> bool:
    """
    Check if tier change is a downgrade.

    Args:
        from_tier: Current tier
        to_tier: Target tier

    Returns:
        True if downgrade, False otherwise
    """
    from_level = get_tier_level(from_tier)
    to_level = get_tier_level(to_tier)
    return to_level < from_level


def can_change_tier(from_tier: str, to_tier: str) -> bool:
    """
    Check if tier change is valid (not same tier).

    Args:
        from_tier: Current tier
        to_tier: Target tier

    Returns:
        True if valid change, False if same tier
    """
    return from_tier != to_tier


def get_max_interval(tier: str) -> int:
    """
    Get maximum review interval for a tier.

    Args:
        tier: Subscription tier

    Returns:
        Maximum interval in days
    """
    return TIER_MAX_INTERVALS.get(tier, 3)


def get_monthly_price(tier: str) -> Decimal:
    """
    Get monthly price for a tier.

    Args:
        tier: Subscription tier

    Returns:
        Monthly price as Decimal
    """
    return TIER_MONTHLY_PRICES.get(tier, Decimal('0.00'))


def calculate_price(
    tier: str,
    billing_cycle: str = BillingCycle.MONTHLY
) -> Decimal:
    """
    Calculate price based on tier and billing cycle.

    Args:
        tier: Subscription tier
        billing_cycle: MONTHLY or YEARLY

    Returns:
        Total price as Decimal
    """
    monthly_price = get_monthly_price(tier)

    if billing_cycle == BillingCycle.YEARLY:
        # Yearly: 12 months with discount
        yearly_price = monthly_price * 12
        discount = yearly_price * YEARLY_DISCOUNT_RATE
        return yearly_price - discount

    return monthly_price


def get_content_limit(tier: str) -> int:
    """
    Get content creation limit for a tier.

    Args:
        tier: Subscription tier

    Returns:
        Content limit
    """
    return CONTENT_LIMITS.get(tier, 20)


def get_category_limit(tier: str) -> int:
    """
    Get category creation limit for a tier.

    Args:
        tier: Subscription tier

    Returns:
        Category limit
    """
    return CATEGORY_LIMITS.get(tier, 1)


def get_features(tier: str) -> List[str]:
    """
    Get list of features for a tier.

    Args:
        tier: Subscription tier

    Returns:
        List of feature descriptions
    """
    return TIER_FEATURES.get(tier, [])


def get_billing_cycle_days(billing_cycle: str) -> int:
    """
    Get number of days for a billing cycle.

    Args:
        billing_cycle: MONTHLY or YEARLY

    Returns:
        Number of days
    """
    return BILLING_CYCLE_DAYS.get(billing_cycle, 30)


def get_tier_info(tier: str, billing_cycle: str = BillingCycle.MONTHLY) -> Dict:
    """
    Get comprehensive information about a tier.

    Args:
        tier: Subscription tier
        billing_cycle: MONTHLY or YEARLY

    Returns:
        Dictionary with tier information
    """
    return {
        'tier': tier,
        'tier_display': dict(SubscriptionTier.choices).get(tier, tier),
        'level': get_tier_level(tier),
        'max_interval_days': get_max_interval(tier),
        'monthly_price': float(get_monthly_price(tier)),
        'price': float(calculate_price(tier, billing_cycle)),
        'billing_cycle': billing_cycle,
        'content_limit': get_content_limit(tier),
        'category_limit': get_category_limit(tier),
        'features': get_features(tier),
    }


def get_all_tiers_info(billing_cycle: str = BillingCycle.MONTHLY) -> List[Dict]:
    """
    Get information for all available tiers.

    Args:
        billing_cycle: MONTHLY or YEARLY

    Returns:
        List of tier information dictionaries
    """
    return [
        get_tier_info(tier, billing_cycle)
        for tier, _ in SubscriptionTier.choices
    ]


def calculate_prorated_refund(
    current_price: Decimal,
    days_remaining: int,
    total_days: int
) -> Decimal:
    """
    Calculate prorated refund for downgrade/cancellation.

    Args:
        current_price: Price paid for current period
        days_remaining: Days left in current period
        total_days: Total days in billing period

    Returns:
        Refund amount as Decimal
    """
    if days_remaining <= 0 or total_days <= 0:
        return Decimal('0.00')

    refund = current_price * (Decimal(days_remaining) / Decimal(total_days))
    return refund.quantize(Decimal('0.01'))
