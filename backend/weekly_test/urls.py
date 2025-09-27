from django.urls import path
from . import views

app_name = 'weekly_test'

urlpatterns = [
    # 주간 시험 CRUD
    path('', views.WeeklyTestListCreateView.as_view(), name='test-list-create'),
    path('<int:pk>/', views.WeeklyTestDetailView.as_view(), name='test-detail'),

    # 시험 진행 관련
    path('start/', views.start_test, name='start-test'),
    path('submit-answer/', views.submit_answer, name='submit-answer'),
    path('complete/', views.complete_test, name='complete-test'),

    # 결과 조회
    path('<int:test_id>/results/', views.test_results, name='test-results'),
]