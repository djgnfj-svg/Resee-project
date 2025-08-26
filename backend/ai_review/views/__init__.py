"""
AI Review Views Package

This package contains all AI review related views, organized by functionality:
- question_views: Question generation and management
- evaluation_views: Answer evaluation and feedback
- chat_views: AI chat functionality
- test_views: Weekly tests and adaptive testing
- analytics_views: Learning analytics and insights
- health_views: Health check endpoints
"""

# Import all view classes for backward compatibility
from .question_views import (
    AIQuestionTypeListView,
    GenerateQuestionsView, 
    ContentQuestionsView,
    GenerateFillBlanksView,
    IdentifyBlurRegionsView
)
from .evaluation_views import (
    AIAnswerEvaluationView,
    ExplanationEvaluationView
)
from .chat_views import AIChatView
from .test_views import (
    WeeklyTestView,
    WeeklyTestStartView,
    WeeklyTestAnswerView,
    InstantContentCheckView,
    AdaptiveTestStartView,
    AdaptiveTestAnswerView
)
# analytics_views module not found - commented out for now
# from .analytics_views import (
#     AIReviewSessionListView,
#     InstantContentCheckView,
#     LearningAnalyticsView,
#     AIStudyMateView,
#     AISummaryNoteView
# )
from .health_views import ai_review_health

__all__ = [
    # Question views
    'AIQuestionTypeListView',
    'GenerateQuestionsView',
    'ContentQuestionsView', 
    'GenerateFillBlanksView',
    'IdentifyBlurRegionsView',
    
    # Evaluation views
    'AIAnswerEvaluationView',
    'ExplanationEvaluationView',
    
    # Chat views
    'AIChatView',
    
    # Test views
    'WeeklyTestView',
    'WeeklyTestStartView',
    'WeeklyTestAnswerView',
    'InstantContentCheckView',
    'AdaptiveTestStartView',
    'AdaptiveTestAnswerView',
    
    # Analytics views - commented out (module not found)
    # 'AIReviewSessionListView',
    # 'InstantContentCheckView', 
    # 'LearningAnalyticsView',
    # 'AIStudyMateView',
    # 'AISummaryNoteView',
    
    # Health views
    'ai_review_health'
]