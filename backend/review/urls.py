from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryReviewStatsView, DashboardStatsView, ReviewHistoryViewSet,
    ReviewScheduleViewSet,
)

app_name = 'review'

router = DefaultRouter()
router.register(r'schedules', ReviewScheduleViewSet, basename='schedules')
router.register(r'history', ReviewHistoryViewSet, basename='history')

urlpatterns = [
    path('', include(router.urls)),
    path('category-stats/', CategoryReviewStatsView.as_view(), name='category-stats'),
    path('dashboard/', DashboardStatsView.as_view(), name='dashboard-stats'),
]
