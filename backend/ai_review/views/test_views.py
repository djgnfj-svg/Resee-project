"""
Test views for AI review functionality - Weekly tests and adaptive testing

This file has been refactored and split into multiple focused modules:
- weekly_test_views.py: Weekly test related views
- content_check_views.py: Content checking and quality analysis views  
- ai_tools_views.py: AI tools and analytics views

All views are now imported from their respective modules for backward compatibility.
"""

# Import the new view modules
from .weekly_test_views import (
    WeeklyTestCategoriesView,
    WeeklyTestView,
    WeeklyTestStartView,
    WeeklyTestAnswerView
)
from .content_check_views import (
    InstantContentCheckView,
    ContentQualityCheckView
)
from .ai_tools_views import (
    LearningAnalyticsView,
    AIStudyMateView,
    AISummaryNoteView
)

# Make all views available at module level for backward compatibility
__all__ = [
    'WeeklyTestCategoriesView',
    'WeeklyTestView', 
    'WeeklyTestStartView',
    'WeeklyTestAnswerView',
    'InstantContentCheckView',
    'ContentQualityCheckView',
    'LearningAnalyticsView',
    'AIStudyMateView',
    'AISummaryNoteView'
]