"""
Constants for accounts app.

Centralizes all magic numbers, prices, limits, and tier configurations.
"""
from decimal import Decimal

from .models import SubscriptionTier, BillingCycle


# ==================== Subscription Tier Hierarchy ====================

TIER_HIERARCHY = {
    SubscriptionTier.FREE: 0,
    SubscriptionTier.BASIC: 1,
    SubscriptionTier.PRO: 2,
}


# ==================== Ebbinghaus-Optimized Intervals ====================

TIER_MAX_INTERVALS = {
    SubscriptionTier.FREE: 3,      # Basic spaced repetition
    SubscriptionTier.BASIC: 90,    # Medium-term memory retention
    SubscriptionTier.PRO: 180,     # Complete long-term retention (6 months)
}


# ==================== Pricing ====================

# Monthly prices
TIER_MONTHLY_PRICES = {
    SubscriptionTier.FREE: Decimal('0.00'),
    SubscriptionTier.BASIC: Decimal('10000.00'),
    SubscriptionTier.PRO: Decimal('25000.00'),
}

# Yearly discount rate (20% off)
YEARLY_DISCOUNT_RATE = Decimal('0.20')


# ==================== Content & Category Limits ====================

# Content limits per tier
CONTENT_LIMITS = {
    SubscriptionTier.FREE: 20,
    SubscriptionTier.BASIC: 999999,  # Effectively unlimited
    SubscriptionTier.PRO: 999999,    # Effectively unlimited
}

# Category limits per tier
CATEGORY_LIMITS = {
    SubscriptionTier.FREE: 1,
    SubscriptionTier.BASIC: 3,
    SubscriptionTier.PRO: 999999,  # Effectively unlimited
}


# ==================== Subscription Features ====================

TIER_FEATURES = {
    SubscriptionTier.FREE: [
        '최대 3일까지 복습 지원',
        '기본 학습 기능',
        '20개 콘텐츠 제한',
        '1개 카테고리 제한'
    ],
    SubscriptionTier.BASIC: [
        '최대 90일까지 복습 지원',
        '향상된 통계 기능',
        '무제한 콘텐츠 생성',
        '3개 카테고리',
        'AI 기능 사용 가능',
        '우선 지원'
    ],
    SubscriptionTier.PRO: [
        '최대 180일까지 복습 지원',
        '모든 고급 기능',
        '무제한 콘텐츠 생성',
        '무제한 카테고리',
        '팀 협업 기능',
        '우선 고객 지원',
        '커스텀 복습 주기'
    ]
}


# ==================== Billing Periods ====================

BILLING_CYCLE_DAYS = {
    BillingCycle.MONTHLY: 30,
    BillingCycle.YEARLY: 365,
}


# ==================== Email Verification ====================

# Rate limit for resending verification email (minutes)
EMAIL_VERIFICATION_RESEND_LIMIT_MINUTES = 5

# Default verification token expiry (days)
EMAIL_VERIFICATION_EXPIRY_DAYS = 1


# ==================== Password Requirements ====================

# Minimum password length
MIN_PASSWORD_LENGTH = 8

# Maximum password length
MAX_PASSWORD_LENGTH = 128
