from django.urls import include, path
from rest_framework.routers import DefaultRouter

# Subscription views
from .subscription.subscription_views import (subscription_cancel, subscription_detail,
                                             subscription_tiers, subscription_upgrade, subscription_downgrade,
                                             toggle_auto_renewal,
                                             SubscriptionViewSet)

# Account management views (non-auth)
from .views import (AccountDeleteView, ProfileView, WeeklyGoalUpdateView, NotificationPreferenceView)

# Authentication views
from .auth.views import (GoogleOAuthView, PasswordChangeView, UserViewSet)

# Email views
from .email.email_views import EmailVerificationView, ResendVerificationView

app_name = 'accounts'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscriptions')

urlpatterns = [
    path('', include(router.urls)),
    # Profile and account management
    path('profile/', ProfileView.as_view(), name='profile'),
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),
    path('account/delete/', AccountDeleteView.as_view(), name='account-delete'),
    path('weekly-goal/', WeeklyGoalUpdateView.as_view(), name='weekly-goal-update'),
    # Notification preferences
    path('notification-preferences/', NotificationPreferenceView.as_view(), name='notification-preferences'),
    # Email verification
    path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    # Authentication
    path('google-oauth/', GoogleOAuthView.as_view(), name='google-oauth'),
    # Subscription management
    path('subscription/', subscription_detail, name='subscription-detail'),
    path('subscription/tiers/', subscription_tiers, name='subscription-tiers'),
    path('subscription/upgrade/', subscription_upgrade, name='subscription-upgrade'),
    path('subscription/downgrade/', subscription_downgrade, name='subscription-downgrade'),
    path('subscription/cancel/', subscription_cancel, name='subscription-cancel'),
    path('subscription/toggle-auto-renewal/', toggle_auto_renewal, name='toggle-auto-renewal'),
]