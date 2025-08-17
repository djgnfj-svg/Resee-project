from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CategoryReviewStatsView, CompleteReviewView,
                    ReviewHistoryViewSet, ReviewScheduleViewSet,
                    TodayReviewView)

app_name = 'review'

router = DefaultRouter()
router.register(r'schedules', ReviewScheduleViewSet, basename='schedules')
router.register(r'history', ReviewHistoryViewSet, basename='history')

urlpatterns = [
    path('', include(router.urls)),
    path('today/', TodayReviewView.as_view(), name='today'),
    path('complete/', CompleteReviewView.as_view(), name='complete'),
    path('category-stats/', CategoryReviewStatsView.as_view(), name='category-stats'),
]