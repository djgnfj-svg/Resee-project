"""
Simple analytics URLs for basic statistics
"""
from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
]