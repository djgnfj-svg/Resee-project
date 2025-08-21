"""
Custom permission classes for the Resee application.
"""
from rest_framework.permissions import BasePermission


class EmailVerifiedRequired(BasePermission):
    """
    Permission class that requires email verification.
    """
    message = "이메일 인증이 필요합니다."
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.is_email_verified
        )


class SubscriptionRequired(BasePermission):
    """
    Permission class that requires an active subscription.
    """
    message = "구독이 필요한 기능입니다."
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'subscription') and
            request.user.subscription.is_active
        )


class AIFeaturesRequired(BasePermission):
    """
    Permission class that requires AI features access.
    """
    message = "AI 기능을 사용할 수 없습니다. 구독을 확인해주세요."
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.can_use_ai_features()
        )