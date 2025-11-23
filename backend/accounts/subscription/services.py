"""
사용자 계정에 대한 권한 및 구독 서비스
"""

from django.conf import settings

from ..constants import CATEGORY_LIMITS, CONTENT_LIMITS
from ..models import SubscriptionTier


class PermissionService:
    """
    사용자 권한 검사 및 구독 로직을 처리하는 서비스 클래스

    이전에 User 모델 메서드에 분산되어 있던
    권한 관련 비즈니스 로직을 중앙화합니다.
    """

    def __init__(self, user):
        self.user = user

    def can_upgrade_subscription(self):
        """사용자가 구독을 업그레이드할 수 있는지 확인합니다"""
        if (
            getattr(settings, "ENFORCE_EMAIL_VERIFICATION", True)
            and not self.user.is_email_verified
        ):
            return False

        if (
            hasattr(self.user, "subscription")
            and self.user.subscription.tier == SubscriptionTier.PRO
        ):
            return False

        return True

    def can_create_content(self):
        """구독 제한을 기반으로 사용자가 콘텐츠를 더 생성할 수 있는지 확인합니다"""
        from content.models import Content

        current_count = Content.objects.filter(author=self.user).count()
        return current_count < self.get_content_limit()

    def can_create_category(self):
        """구독 제한을 기반으로 사용자가 카테고리를 더 생성할 수 있는지 확인합니다"""
        from content.models import Category

        current_count = Category.objects.filter(user=self.user).count()
        return current_count < self.get_category_limit()

    def get_content_limit(self):
        """구독 티어에 따른 콘텐츠 생성 제한을 반환합니다"""
        tier = self._get_user_tier()
        return CONTENT_LIMITS.get(tier, 20)

    def get_category_limit(self):
        """구독 티어에 따른 카테고리 생성 제한을 반환합니다"""
        tier = self._get_user_tier()
        return CATEGORY_LIMITS.get(tier, 1)

    def get_content_usage(self):
        """사용자의 콘텐츠 사용 통계를 반환합니다"""
        from content.models import Content

        current_count = Content.objects.filter(author=self.user).count()
        limit = self.get_content_limit()

        return {
            "current": current_count,
            "limit": limit,
            "remaining": max(0, limit - current_count),
            "percentage": (current_count / limit * 100) if limit > 0 else 0,
            "can_create": current_count < limit,
            "tier": self._get_user_tier(),
        }

    def get_category_usage(self):
        """사용자의 카테고리 사용 통계를 반환합니다"""
        from content.models import Category

        current_count = Category.objects.filter(user=self.user).count()
        limit = self.get_category_limit()

        return {
            "current": current_count,
            "limit": limit,
            "remaining": max(0, limit - current_count),
            "percentage": (current_count / limit * 100) if limit > 0 else 0,
            "can_create": current_count < limit,
            "tier": self._get_user_tier(),
        }

    def _get_user_tier(self):
        """사용자의 현재 구독 티어를 반환합니다"""
        try:
            if (
                self.user.subscription.is_active
                and not self.user.subscription.is_expired()
            ):
                return self.user.subscription.tier
        except (AttributeError, Exception):
            pass
        return "free"


class SubscriptionService:
    """
    구독 관련 작업을 처리하는 서비스 클래스
    """

    def __init__(self, user):
        self.user = user

    def has_active_subscription(self):
        """사용자가 활성 구독을 가지고 있는지 확인합니다"""
        try:
            return (
                self.user.subscription.is_active
                and not self.user.subscription.is_expired()
            )
        except (AttributeError, Exception):
            # 사용자가 구독이 없거나 접근할 수 없음
            return False

    def get_max_review_interval(self):
        """구독을 기반으로 최대 복습 간격을 반환합니다"""
        if self.has_active_subscription():
            return self.user.subscription.max_interval_days
        return 3  # Default FREE tier
