"""
URL patterns for AI Review app
"""
from django.urls import path

from . import views

app_name = 'ai_review'

urlpatterns = [
    # Health check
    path('health/', views.ai_review_health, name='health'),
    
    # Question types
    path('question-types/', views.AIQuestionTypeListView.as_view(), name='question-types'),
    
    # Question generation
    path('generate-questions/', views.GenerateQuestionsView.as_view(), name='generate-questions'),
    path('content/<int:content_id>/questions/', views.ContentQuestionsView.as_view(), name='content-questions'),
    
    # Answer evaluation
    path('evaluate-answer/', views.AIAnswerEvaluationView.as_view(), name='evaluate-answer'),
    
    # Review sessions - commented out (view not found)
    # path('sessions/', views.AIReviewSessionListView.as_view(), name='review-sessions'),
    
    # Fill-in-the-blank generation
    path('generate-fill-blanks/', views.GenerateFillBlanksView.as_view(), name='generate-fill-blanks'),
    
    # Blur regions identification
    path('identify-blur-regions/', views.IdentifyBlurRegionsView.as_view(), name='identify-blur-regions'),
    
    
    # Explanation evaluation
    path('evaluate-explanation/', views.ExplanationEvaluationView.as_view(), name='evaluate-explanation'),
    
    # Weekly test (newly implemented with adaptive features)
    path('weekly-test/categories/', views.WeeklyTestCategoriesView.as_view(), name='weekly-test-categories'),
    path('weekly-test/', views.WeeklyTestView.as_view(), name='weekly-test'),
    path('weekly-test/start/', views.WeeklyTestStartView.as_view(), name='weekly-test-start'),
    path('weekly-test/answer/', views.WeeklyTestAnswerView.as_view(), name='weekly-test-answer'),
    
    # Content quality check (newly implemented)
    path('content-check/', views.ContentQualityCheckView.as_view(), name='content-check'),
    path('instant-check/', views.InstantContentCheckView.as_view(), name='instant-content-check'),
    
]