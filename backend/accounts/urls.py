from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .subscription_views import subscription_detail, subscription_tiers, subscription_upgrade
from .views import (
    UserViewSet, 
    ProfileView, 
    PasswordChangeView, 
    AccountDeleteView,
    EmailVerificationView, 
    ResendVerificationView, 
    GoogleOAuthView,
    WeeklyGoalUpdateView,
    AIUsageView
)

app_name = 'accounts'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),
    path('account/delete/', AccountDeleteView.as_view(), name='account-delete'),
    path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    path('google-oauth/', GoogleOAuthView.as_view(), name='google-oauth'),
    path('weekly-goal/', WeeklyGoalUpdateView.as_view(), name='weekly-goal-update'),
    path('ai-usage/', AIUsageView.as_view(), name='ai-usage'),
    # Subscription endpoints
    path('subscription/', subscription_detail, name='subscription-detail'),
    path('subscription/tiers/', subscription_tiers, name='subscription-tiers'),
    path('subscription/upgrade/', subscription_upgrade, name='subscription-upgrade'),
]