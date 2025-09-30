"""
Development-only URLs for monitoring (no authentication required).
Only works when DEBUG=True.
"""
from django.urls import path
from .dev_monitoring_views import (
    dev_monitoring_dashboard,
    dev_dashboard_data,
    dev_log_viewer,
    dev_log_summary,
    dev_log_file_content
)

urlpatterns = [
    # Development monitoring dashboard
    path('', dev_monitoring_dashboard, name='dev-monitoring-dashboard'),
    path('dashboard-data/', dev_dashboard_data, name='dev-dashboard-data'),

    # Development log viewer
    path('logs/', dev_log_viewer, name='dev-log-viewer'),
    path('logs/summary/', dev_log_summary, name='dev-log-summary'),
    path('logs/file/<str:filename>/', dev_log_file_content, name='dev-log-file-content'),
]