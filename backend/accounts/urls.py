from django.urls import include, path
from rest_framework.routers import DefaultRouter

# Authentication views
from .auth.views import GoogleOAuthView, UserViewSet
# Email views
from .email.email_views import EmailVerificationView, ResendVerificationView
# Subscription views
from .subscription.subscription_views import (
    subscription_detail, subscription_tiers,
)
# Account management views (non-auth)
from .views import (
    NotificationPreferenceView, ProfileView, WeeklyGoalUpdateView,
)

app_name = 'accounts'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    # Profile and account management
    path('profile/', ProfileView.as_view(), name='profile'),
    path('weekly-goal/', WeeklyGoalUpdateView.as_view(), name='weekly-goal-update'),
    # Notification preferences
    path('notification-preferences/', NotificationPreferenceView.as_view(), name='notification-preferences'),
    # Email verification
    path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    # Authentication
    path('google-oauth/', GoogleOAuthView.as_view(), name='google-oauth'),
    # Subscription management (read-only, payment system not implemented)
    path('subscription/', subscription_detail, name='subscription-detail'),
    path('subscription/tiers/', subscription_tiers, name='subscription-tiers'),
]
