"""
URL configuration for monitoring app
"""
from django.urls import path

from . import views
from .health import health_check_basic, health_check_detailed, readiness_check, liveness_check

app_name = 'monitoring'

urlpatterns = [
    # Health check endpoints
    path('health/', health_check_basic, name='health_check_basic'),
    path('health/detailed/', health_check_detailed, name='health_check_detailed'),
    path('ready/', readiness_check, name='readiness_check'),
    path('alive/', liveness_check, name='liveness_check'),
    
    # Legacy health check
    path('health-legacy/', views.health_check, name='health_check_legacy'),
    
    # Admin dashboard endpoints
    path('dashboard/', views.dashboard_overview, name='dashboard_overview'),
    path('api-performance/', views.api_performance_chart, name='api_performance_chart'),
    path('error-analysis/', views.error_analysis, name='error_analysis'),
    path('ai-analytics/', views.ai_usage_analytics, name='ai_usage_analytics'),
    path('performance-insights/', views.performance_insights, name='performance_insights'),
    
    # Admin actions
    path('cleanup/', views.cleanup_old_data, name='cleanup_old_data'),
]