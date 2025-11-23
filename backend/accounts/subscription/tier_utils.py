"""
구독 티어 작업을 위한 유틸리티 함수

제공 기능:
- 티어 계층 구조 및 비교
- 가격 계산
- 기능 및 제한 조회
- 티어 검증
"""

from decimal import Decimal
from typing import Dict, List

from ..constants import (
    BILLING_CYCLE_DAYS,
    CATEGORY_LIMITS,
    CONTENT_LIMITS,
    TIER_FEATURES,
    TIER_HIERARCHY,
    TIER_MAX_INTERVALS,
    TIER_MONTHLY_PRICES,
    YEARLY_DISCOUNT_RATE,
)
from ..models import BillingCycle, SubscriptionTier


def get_tier_level(tier: str) -> int:
    """
    티어의 숫자 레벨을 반환합니다.

    Args:
        tier: 구독 티어 (FREE, BASIC, PRO)

    Returns:
        숫자 레벨 (0=FREE, 1=BASIC, 2=PRO)
    """
    return TIER_HIERARCHY.get(tier, 0)


def is_upgrade(from_tier: str, to_tier: str) -> bool:
    """
    티어 변경이 업그레이드인지 확인합니다.

    Args:
        from_tier: 현재 티어
        to_tier: 목표 티어

    Returns:
        업그레이드이면 True, 아니면 False
    """
    from_level = get_tier_level(from_tier)
    to_level = get_tier_level(to_tier)
    return to_level > from_level


def is_downgrade(from_tier: str, to_tier: str) -> bool:
    """
    티어 변경이 다운그레이드인지 확인합니다.

    Args:
        from_tier: 현재 티어
        to_tier: 목표 티어

    Returns:
        다운그레이드이면 True, 아니면 False
    """
    from_level = get_tier_level(from_tier)
    to_level = get_tier_level(to_tier)
    return to_level < from_level


def can_change_tier(from_tier: str, to_tier: str) -> bool:
    """
    티어 변경이 유효한지 확인합니다 (동일 티어가 아닌지).

    Args:
        from_tier: 현재 티어
        to_tier: 목표 티어

    Returns:
        유효한 변경이면 True, 동일 티어이면 False
    """
    return from_tier != to_tier


def get_max_interval(tier: str) -> int:
    """
    티어의 최대 복습 간격을 반환합니다.

    Args:
        tier: 구독 티어

    Returns:
        최대 간격 (일 단위)
    """
    return TIER_MAX_INTERVALS.get(tier, 3)


def get_monthly_price(tier: str) -> Decimal:
    """
    티어의 월간 가격을 반환합니다.

    Args:
        tier: 구독 티어

    Returns:
        월간 가격 (Decimal)
    """
    return TIER_MONTHLY_PRICES.get(tier, Decimal("0.00"))


def calculate_price(tier: str, billing_cycle: str = BillingCycle.MONTHLY) -> Decimal:
    """
    티어와 결제 주기를 기반으로 가격을 계산합니다.

    Args:
        tier: 구독 티어
        billing_cycle: MONTHLY 또는 YEARLY

    Returns:
        총 가격 (Decimal)
    """
    monthly_price = get_monthly_price(tier)

    if billing_cycle == BillingCycle.YEARLY:
        # 연간: 12개월 + 할인
        yearly_price = monthly_price * 12
        discount = yearly_price * YEARLY_DISCOUNT_RATE
        return yearly_price - discount

    return monthly_price


def get_content_limit(tier: str) -> int:
    """
    티어의 콘텐츠 생성 제한을 반환합니다.

    Args:
        tier: 구독 티어

    Returns:
        콘텐츠 제한 개수
    """
    return CONTENT_LIMITS.get(tier, 20)


def get_category_limit(tier: str) -> int:
    """
    티어의 카테고리 생성 제한을 반환합니다.

    Args:
        tier: 구독 티어

    Returns:
        카테고리 제한 개수
    """
    return CATEGORY_LIMITS.get(tier, 1)


def get_features(tier: str) -> List[str]:
    """
    티어의 기능 목록을 반환합니다.

    Args:
        tier: 구독 티어

    Returns:
        기능 설명 리스트
    """
    return TIER_FEATURES.get(tier, [])


def get_billing_cycle_days(billing_cycle: str) -> int:
    """
    결제 주기의 일수를 반환합니다.

    Args:
        billing_cycle: MONTHLY 또는 YEARLY

    Returns:
        일수
    """
    return BILLING_CYCLE_DAYS.get(billing_cycle, 30)


def get_tier_info(tier: str, billing_cycle: str = BillingCycle.MONTHLY) -> Dict:
    """
    티어에 대한 종합 정보를 반환합니다.

    Args:
        tier: 구독 티어
        billing_cycle: MONTHLY 또는 YEARLY

    Returns:
        티어 정보가 담긴 딕셔너리
    """
    return {
        "tier": tier,
        "tier_display": dict(SubscriptionTier.choices).get(tier, tier),
        "level": get_tier_level(tier),
        "max_interval_days": get_max_interval(tier),
        "monthly_price": float(get_monthly_price(tier)),
        "price": float(calculate_price(tier, billing_cycle)),
        "billing_cycle": billing_cycle,
        "content_limit": get_content_limit(tier),
        "category_limit": get_category_limit(tier),
        "features": get_features(tier),
    }


def get_all_tiers_info(billing_cycle: str = BillingCycle.MONTHLY) -> List[Dict]:
    """
    모든 사용 가능한 티어의 정보를 반환합니다.

    Args:
        billing_cycle: MONTHLY 또는 YEARLY

    Returns:
        티어 정보 딕셔너리 리스트
    """
    return [get_tier_info(tier, billing_cycle) for tier, _ in SubscriptionTier.choices]


def calculate_prorated_refund(
    current_price: Decimal, days_remaining: int, total_days: int
) -> Decimal:
    """
    다운그레이드/해지에 대한 일할 환불 금액을 계산합니다.

    Args:
        current_price: 현재 기간에 지불한 가격
        days_remaining: 현재 기간의 남은 일수
        total_days: 결제 기간의 총 일수

    Returns:
        환불 금액 (Decimal)
    """
    if days_remaining <= 0 or total_days <= 0:
        return Decimal("0.00")

    refund = current_price * (Decimal(days_remaining) / Decimal(total_days))
    return refund.quantize(Decimal("0.01"))
