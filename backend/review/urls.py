from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReviewScheduleViewSet, ReviewHistoryViewSet, 
    TodayReviewView, CompleteReviewView, CategoryReviewStatsView
)

router = DefaultRouter()
router.register(r'schedules', ReviewScheduleViewSet)
router.register(r'history', ReviewHistoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('today/', TodayReviewView.as_view(), name='today-review'),
    path('complete/', CompleteReviewView.as_view(), name='complete-review'),
    path('category-stats/', CategoryReviewStatsView.as_view(), name='category-review-stats'),
]