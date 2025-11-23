"""
Resee 애플리케이션을 위한 커스텀 권한 클래스
"""

from rest_framework.permissions import BasePermission


class EmailVerifiedRequired(BasePermission):
    """
    이메일 인증이 필요한 권한 클래스
    """

    message = "이메일 인증이 필요합니다."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_email_verified


class SubscriptionRequired(BasePermission):
    """
    활성 구독이 필요한 권한 클래스
    """

    message = "구독이 필요한 기능입니다."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and hasattr(request.user, "subscription")
            and request.user.subscription.is_active
        )


class AIFeaturesRequired(BasePermission):
    """
    AI 기능 접근이 필요한 권한 클래스
    """

    message = "AI 기능을 사용할 수 없습니다. 구독을 확인해주세요."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_use_ai_features()
