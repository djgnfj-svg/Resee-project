"""
Subscription tier service for handling tier-related business logic.

DEPRECATED: This class is maintained for backward compatibility.
New code should use tier_utils module functions directly.
"""
import warnings
from decimal import Decimal
from typing import Dict, List

from . import tier_utils
from ..models import BillingCycle


class SubscriptionTierService:
    """
    DEPRECATED: Service class for subscription tier operations.

    This class is maintained for backward compatibility. New code should use
    the tier_utils module functions directly.

    All methods delegate to tier_utils module functions.
    """

    @staticmethod
    def get_tier_level(tier: str) -> int:
        """DEPRECATED: Use tier_utils.get_tier_level() instead"""
        return tier_utils.get_tier_level(tier)

    @staticmethod
    def is_upgrade(from_tier: str, to_tier: str) -> bool:
        """DEPRECATED: Use tier_utils.is_upgrade() instead"""
        return tier_utils.is_upgrade(from_tier, to_tier)

    @staticmethod
    def is_downgrade(from_tier: str, to_tier: str) -> bool:
        """DEPRECATED: Use tier_utils.is_downgrade() instead"""
        return tier_utils.is_downgrade(from_tier, to_tier)

    @staticmethod
    def can_change_tier(from_tier: str, to_tier: str) -> bool:
        """DEPRECATED: Use tier_utils.can_change_tier() instead"""
        return tier_utils.can_change_tier(from_tier, to_tier)

    @staticmethod
    def get_max_interval(tier: str) -> int:
        """DEPRECATED: Use tier_utils.get_max_interval() instead"""
        return tier_utils.get_max_interval(tier)

    @staticmethod
    def get_monthly_price(tier: str) -> Decimal:
        """DEPRECATED: Use tier_utils.get_monthly_price() instead"""
        return tier_utils.get_monthly_price(tier)

    @staticmethod
    def calculate_price(tier: str, billing_cycle: str = BillingCycle.MONTHLY) -> Decimal:
        """DEPRECATED: Use tier_utils.calculate_price() instead"""
        return tier_utils.calculate_price(tier, billing_cycle)

    @staticmethod
    def get_content_limit(tier: str) -> int:
        """DEPRECATED: Use tier_utils.get_content_limit() instead"""
        return tier_utils.get_content_limit(tier)

    @staticmethod
    def get_category_limit(tier: str) -> int:
        """DEPRECATED: Use tier_utils.get_category_limit() instead"""
        return tier_utils.get_category_limit(tier)

    @staticmethod
    def get_features(tier: str) -> List[str]:
        """DEPRECATED: Use tier_utils.get_features() instead"""
        return tier_utils.get_features(tier)

    @staticmethod
    def get_billing_cycle_days(billing_cycle: str) -> int:
        """DEPRECATED: Use tier_utils.get_billing_cycle_days() instead"""
        return tier_utils.get_billing_cycle_days(billing_cycle)

    @staticmethod
    def get_tier_info(tier: str, billing_cycle: str = BillingCycle.MONTHLY) -> Dict:
        """DEPRECATED: Use tier_utils.get_tier_info() instead"""
        return tier_utils.get_tier_info(tier, billing_cycle)

    @staticmethod
    def get_all_tiers_info(billing_cycle: str = BillingCycle.MONTHLY) -> List[Dict]:
        """DEPRECATED: Use tier_utils.get_all_tiers_info() instead"""
        return tier_utils.get_all_tiers_info(billing_cycle)

    @staticmethod
    def calculate_prorated_refund(
        current_price: Decimal,
        days_remaining: int,
        total_days: int
    ) -> Decimal:
        """DEPRECATED: Use tier_utils.calculate_prorated_refund() instead"""
        return tier_utils.calculate_prorated_refund(current_price, days_remaining, total_days)
