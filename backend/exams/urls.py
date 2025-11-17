from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'weekly_test'

# Router for RESTful endpoints
router = DefaultRouter()
router.register(r'', views.TestSessionViewSet, basename='test-sessions')

urlpatterns = [
    # 주간 시험 CRUD (기존)
    path('', views.WeeklyTestListCreateView.as_view(), name='test-list-create'),
    path('<int:pk>/', views.WeeklyTestDetailView.as_view(), name='test-detail'),

    # RESTful test session endpoints
    path('test-sessions/', include(router.urls)),

    # 시험 진행 관련 (기존 - 하위 호환성)
    path('start/', views.start_test, name='start-test'),
    path('submit-answer/', views.submit_answer, name='submit-answer'),
    path('complete/', views.complete_test, name='complete-test'),

    # 결과 조회 (기존 - 하위 호환성)
    path('<int:test_id>/results/', views.test_results, name='test-results'),
]
