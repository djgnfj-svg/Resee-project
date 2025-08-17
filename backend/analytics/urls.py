from django.urls import path

from .views import (AdvancedAnalyticsView, DashboardView, LearningCalendarView,
                    ReviewStatsView)

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('review-stats/', ReviewStatsView.as_view(), name='review-stats'),
    path('advanced/', AdvancedAnalyticsView.as_view(), name='advanced-analytics'),
    path('calendar/', LearningCalendarView.as_view(), name='learning-calendar'),
]