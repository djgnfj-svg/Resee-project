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

# Health check views
from .health.health_views import health_check, health_detailed, readiness_check, liveness_check
from .health.log_views import log_summary, recent_errors, log_file_content, cleanup_old_logs, log_analytics
from .health.monitoring_views import dashboard_data

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
    # Health checks
    path('health/', health_check, name='health-check'),
    path('health/detailed/', health_detailed, name='health-detailed'),
    path('health/ready/', readiness_check, name='readiness-check'),
    path('health/live/', liveness_check, name='liveness-check'),
    # Log management (admin only)
    path('logs/summary/', log_summary, name='log-summary'),
    path('logs/errors/', recent_errors, name='recent-errors'),
    path('logs/file/<str:filename>/', log_file_content, name='log-file-content'),
    path('logs/cleanup/', cleanup_old_logs, name='cleanup-old-logs'),
    path('logs/analytics/', log_analytics, name='log-analytics'),
    # Monitoring dashboard API (개발 환경에서는 인증 불필요, 운영 환경에서는 관리자 권한 필요)
    path('dashboard-data/', dashboard_data, name='dashboard-data'),
]