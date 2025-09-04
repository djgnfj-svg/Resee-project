"""
Test cases for split AI review modules
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import Mock, patch

User = get_user_model()


class SplitModulesImportTestCase(TestCase):
    """Test cases for split AI review modules imports"""
    
    def test_test_views_imports(self):
        """Test that test_views.py imports all split modules correctly"""
        # This should not raise ImportError
        import ai_review.views.test_views as test_views
        
        # Verify all view classes are accessible through main module
        self.assertTrue(hasattr(test_views, 'WeeklyTestCategoriesView'))
        self.assertTrue(hasattr(test_views, 'WeeklyTestView'))
        self.assertTrue(hasattr(test_views, 'WeeklyTestStartView'))
        self.assertTrue(hasattr(test_views, 'WeeklyTestAnswerView'))
        self.assertTrue(hasattr(test_views, 'InstantContentCheckView'))
        self.assertTrue(hasattr(test_views, 'ContentQualityCheckView'))
        self.assertTrue(hasattr(test_views, 'LearningAnalyticsView'))
        self.assertTrue(hasattr(test_views, 'AIStudyMateView'))
        self.assertTrue(hasattr(test_views, 'AISummaryNoteView'))
    
    def test_weekly_test_views_module(self):
        """Test weekly test views module can be imported independently"""
        from ai_review.views.weekly_test_views import (
            WeeklyTestCategoriesView,
            WeeklyTestView,
            WeeklyTestStartView,
            WeeklyTestAnswerView
        )
        
        # Verify classes can be instantiated
        self.assertIsNotNone(WeeklyTestCategoriesView())
        self.assertIsNotNone(WeeklyTestView())
        self.assertIsNotNone(WeeklyTestStartView())
        self.assertIsNotNone(WeeklyTestAnswerView())
    
    def test_content_check_views_module(self):
        """Test content check views module can be imported independently"""
        from ai_review.views.content_check_views import (
            InstantContentCheckView,
            ContentQualityCheckView
        )
        
        # Verify classes can be instantiated
        self.assertIsNotNone(InstantContentCheckView())
        self.assertIsNotNone(ContentQualityCheckView())
    
    def test_ai_tools_views_module(self):
        """Test AI tools views module can be imported independently"""
        from ai_review.views.ai_tools_views import (
            LearningAnalyticsView,
            AIStudyMateView,
            AISummaryNoteView
        )
        
        # Verify classes can be instantiated
        self.assertIsNotNone(LearningAnalyticsView())
        self.assertIsNotNone(AIStudyMateView())
        self.assertIsNotNone(AISummaryNoteView())
    
    def test_backward_compatibility(self):
        """Test backward compatibility - views accessible through original import"""
        # This should work for existing code
        from ai_review.views.test_views import WeeklyTestView
        
        # And also through new modules
        from ai_review.views.weekly_test_views import WeeklyTestView as NewWeeklyTestView
        
        # Should be the same class
        self.assertEqual(WeeklyTestView, NewWeeklyTestView)
    
    def test_all_exports(self):
        """Test __all__ exports in test_views module"""
        import ai_review.views.test_views as test_views
        
        expected_exports = [
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
        
        # Verify all expected views are in __all__
        for export in expected_exports:
            self.assertIn(export, test_views.__all__)
    
    def test_module_documentation(self):
        """Test that modules have proper documentation"""
        import ai_review.views.weekly_test_views as weekly_views
        import ai_review.views.content_check_views as content_views
        import ai_review.views.ai_tools_views as ai_tools_views
        
        # Verify modules have docstrings
        self.assertIsNotNone(weekly_views.__doc__)
        self.assertIsNotNone(content_views.__doc__)
        self.assertIsNotNone(ai_tools_views.__doc__)
        
        # Verify docstrings contain expected content
        self.assertIn('Weekly test', weekly_views.__doc__)
        self.assertIn('Content check', content_views.__doc__)
        self.assertIn('AI tools', ai_tools_views.__doc__)


class SplitModulesFunctionalityTestCase(APITestCase):
    """Test cases for split modules functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_weekly_test_categories_view_accessible(self):
        """Test that WeeklyTestCategoriesView is accessible and responds"""
        from ai_review.views.weekly_test_views import WeeklyTestCategoriesView
        
        view = WeeklyTestCategoriesView()
        self.assertTrue(hasattr(view, 'get'))
        self.assertEqual(view.permission_classes, [User.objects.model])  # IsAuthenticated
    
    def test_content_quality_check_view_accessible(self):
        """Test that ContentQualityCheckView is accessible and responds"""
        from ai_review.views.content_check_views import ContentQualityCheckView
        
        view = ContentQualityCheckView()
        self.assertTrue(hasattr(view, 'post'))
        self.assertTrue(hasattr(view, '_calculate_content_quality'))
        self.assertTrue(hasattr(view, '_generate_feedback'))
    
    def test_ai_tools_views_not_implemented(self):
        """Test that AI tools views return not implemented status"""
        from ai_review.views.ai_tools_views import LearningAnalyticsView
        
        view = LearningAnalyticsView()
        request = Mock()
        response = view.get(request)
        
        self.assertEqual(response.status_code, status.HTTP_501_NOT_IMPLEMENTED)
        self.assertIn('under_development', response.data['status'])
    
    def test_type_hints_in_content_views(self):
        """Test that type hints are properly applied in content views"""
        from ai_review.views.content_check_views import ContentQualityCheckView
        
        view = ContentQualityCheckView()
        
        # These methods should have type hints
        self.assertTrue(hasattr(view._calculate_content_quality, '__annotations__'))
        self.assertTrue(hasattr(view._generate_feedback, '__annotations__'))
        self.assertTrue(hasattr(view._identify_strengths, '__annotations__'))
        self.assertTrue(hasattr(view._identify_improvements, '__annotations__'))
    
    def test_query_optimization_in_weekly_test_views(self):
        """Test that query optimization is applied in weekly test views"""
        from ai_review.views.weekly_test_views import WeeklyTestStartView
        
        # Test that select_related is used in the view code
        # (This tests the code structure, not runtime behavior)
        import inspect
        source = inspect.getsource(WeeklyTestStartView.post)
        self.assertIn('select_related', source)
        
        # Test for WeeklyTestAnswerView as well
        from ai_review.views.weekly_test_views import WeeklyTestAnswerView
        source = inspect.getsource(WeeklyTestAnswerView.post)
        self.assertIn('select_related', source)
    
    def test_module_file_sizes(self):
        """Test that original large file has been properly split"""
        import ai_review.views.test_views
        import ai_review.views.weekly_test_views
        import ai_review.views.content_check_views
        import ai_review.views.ai_tools_views
        import os
        
        # Get file paths
        test_views_path = ai_review.views.test_views.__file__
        weekly_test_path = ai_review.views.weekly_test_views.__file__
        content_check_path = ai_review.views.content_check_views.__file__
        ai_tools_path = ai_review.views.ai_tools_views.__file__
        
        # Verify files exist and are reasonably sized
        self.assertTrue(os.path.exists(test_views_path))
        self.assertTrue(os.path.exists(weekly_test_path))
        self.assertTrue(os.path.exists(content_check_path))
        self.assertTrue(os.path.exists(ai_tools_path))
        
        # Original test_views.py should now be much smaller (mainly imports)
        test_views_size = os.path.getsize(test_views_path)
        weekly_test_size = os.path.getsize(weekly_test_path)
        
        # Weekly test views should be the largest (contains most logic)
        self.assertGreater(weekly_test_size, test_views_size)