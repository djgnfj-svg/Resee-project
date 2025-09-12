from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .subscription_views import (subscription_cancel, subscription_detail,
                                 subscription_tiers, subscription_upgrade, subscription_downgrade, 
                                 payment_history, toggle_auto_renewal, billing_schedule)
from .views import (AccountDeleteView, AIUsageView, EmailVerificationView,
                    EmailSubscriptionView, GoogleOAuthView, PasswordChangeView, ProfileView,
                    ResendVerificationView, UserViewSet, WeeklyGoalUpdateView)

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
    path('email-signup/', EmailSubscriptionView.as_view(), name='email-signup'),
    # Subscription endpoints
    path('subscription/', subscription_detail, name='subscription-detail'),
    path('subscription/tiers/', subscription_tiers, name='subscription-tiers'),
    path('subscription/upgrade/', subscription_upgrade, name='subscription-upgrade'),
    path('subscription/downgrade/', subscription_downgrade, name='subscription-downgrade'),
    path('subscription/cancel/', subscription_cancel, name='subscription-cancel'),
    path('subscription/toggle-auto-renewal/', toggle_auto_renewal, name='toggle-auto-renewal'),
    path('payment-history/', payment_history, name='payment-history'),
    path('billing-schedule/', billing_schedule, name='billing-schedule'),
]