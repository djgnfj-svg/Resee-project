from django.urls import path
from .views import DashboardView, ReviewStatsView

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('review-stats/', ReviewStatsView.as_view(), name='review-stats'),
]