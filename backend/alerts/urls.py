from django.urls import path
from . import views

app_name = 'alerts'

urlpatterns = [
    # Alert rules management
    path('rules/', views.AlertRuleListCreateView.as_view(), name='alert-rules-list'),
    path('rules/<int:pk>/', views.AlertRuleDetailView.as_view(), name='alert-rule-detail'),
    
    # Alert history
    path('history/', views.AlertHistoryListView.as_view(), name='alert-history-list'),
    path('history/<int:pk>/', views.AlertHistoryDetailView.as_view(), name='alert-history-detail'),
    path('history/<int:pk>/resolve/', views.resolve_alert, name='resolve-alert'),
    
    # Alert statistics
    path('stats/', views.alert_statistics, name='alert-statistics'),
    
    # Test endpoints
    path('test/slack/', views.test_slack_notification, name='test-slack'),
    path('test/email/', views.test_email_notification, name='test-email'),
    
    # Manual trigger
    path('trigger/', views.manual_trigger_check, name='manual-trigger'),
]