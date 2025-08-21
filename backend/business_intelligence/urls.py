"""
URL configuration for business intelligence app
"""
from django.urls import path
from . import views

app_name = 'business_intelligence'

urlpatterns = [
    # User-specific analytics
    path('learning-insights/', views.LearningInsightsView.as_view(), name='learning-insights'),
    path('content-analytics/', views.ContentAnalyticsView.as_view(), name='content-analytics'),
    path('performance-trends/', views.PerformanceTrendView.as_view(), name='performance-trends'),
    path('recommendations/', views.LearningRecommendationsView.as_view(), name='recommendations'),
    path('subscription-insights/', views.SubscriptionInsightsView.as_view(), name='subscription-insights'),
    
    # Data management
    path('update-pattern/', views.update_learning_pattern, name='update-pattern'),
    
    # Admin-only business metrics
    path('business-dashboard/', views.BusinessDashboardView.as_view(), name='business-dashboard'),
    
    # Admin-only subscription analytics
    path('subscription-analysis/', views.SubscriptionAnalysisView.as_view(), name='subscription-analysis'),
    path('conversion-probability/', views.ConversionProbabilityView.as_view(), name='conversion-probability'),
]