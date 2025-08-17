"""
URL configuration for monitoring app
"""
from django.urls import path

from . import views

app_name = 'monitoring'

urlpatterns = [
    # Public health check
    path('health/', views.health_check, name='health_check'),
    
    # Admin dashboard endpoints
    path('dashboard/', views.dashboard_overview, name='dashboard_overview'),
    path('api-performance/', views.api_performance_chart, name='api_performance_chart'),
    path('error-analysis/', views.error_analysis, name='error_analysis'),
    path('ai-analytics/', views.ai_usage_analytics, name='ai_usage_analytics'),
    path('performance-insights/', views.performance_insights, name='performance_insights'),
    
    # Admin actions
    path('cleanup/', views.cleanup_old_data, name='cleanup_old_data'),
]