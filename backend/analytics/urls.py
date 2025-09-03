from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Basic analytics (existing)
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('review-stats/', views.ReviewStatsView.as_view(), name='review-stats'),
    path('advanced/', views.AdvancedAnalyticsView.as_view(), name='advanced-analytics'),
    path('calendar/', views.LearningCalendarView.as_view(), name='learning-calendar'),
    
    # Business Intelligence views (from BI app)
    path('learning-insights/', views.LearningInsightsView.as_view(), name='learning-insights'),
    # path('content-analytics/', views.ContentAnalyticsView.as_view(), name='content-analytics'),  # temporarily disabled
    path('performance-trends/', views.PerformanceTrendView.as_view(), name='performance-trends'),
    path('recommendations/', views.LearningRecommendationsView.as_view(), name='recommendations'),
    path('subscription-insights/', views.SubscriptionInsightsView.as_view(), name='subscription-insights'),
    
    # Data management
    path('update-pattern/', views.update_learning_pattern, name='update-pattern'),
    
    # Admin-only business metrics
    path('business-dashboard/', views.BusinessDashboardView.as_view(), name='business-dashboard'),
    path('subscription-analysis/', views.SubscriptionAnalysisView.as_view(), name='subscription-analysis'),
    path('conversion-probability/', views.ConversionProbabilityView.as_view(), name='conversion-probability'),
]