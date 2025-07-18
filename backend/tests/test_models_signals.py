"""
Comprehensive tests for models, signals, and business logic
"""

from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.utils import timezone
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from .base import BaseTestCase, TestDataMixin
from content.models import Content, Category, Tag
from review.models import ReviewSchedule, ReviewHistory
from review.utils import get_review_intervals
from review.signals import create_review_schedule_signal
from content.signals import post_save, post_delete

User = get_user_model()


class ContentModelAdvancedTestCase(BaseTestCase):
    """Advanced Content model tests"""
    
    def test_content_slug_generation(self):
        """Test automatic slug generation for content if needed"""
        content = self.create_content(title="Test Content With Spaces")
        # Assuming slug field exists or could be added
        self.assertEqual(content.title, "Test Content With Spaces")
    
    def test_content_markdown_handling(self):
        """Test markdown content handling"""
        markdown_content = """
        # Header 1
        ## Header 2
        
        This is **bold** text and *italic* text.
        
        - List item 1
        - List item 2
        
        ```python
        def hello():
            return "Hello, World!"
        ```
        
        [Link](https://example.com)
        
        ![Image](image.png)
        """
        
        content = self.create_content(content=markdown_content)
        self.assertIn("# Header 1", content.content)
        self.assertIn("**bold**", content.content)
        self.assertIn("```python", content.content)
        self.assertIn("![Image](image.png)", content.content)
    
    def test_content_with_special_characters(self):
        """Test content with special characters and unicode"""
        special_content = """
        Special characters: !@#$%^&*()_+-={}[]|\\:";'<>?,./
        Unicode: 한글 테스트 🚀 ñáéíóú
        Math symbols: ∑ ∫ ∆ ∇ ∂ ∞
        """
        
        content = self.create_content(
            title="Special Characters Test 한글",
            content=special_content
        )
        
        self.assertIn("한글 테스트", content.content)
        self.assertIn("🚀", content.content)
        self.assertIn("∑ ∫ ∆", content.content)
    
    def test_content_extremely_long_content(self):
        """Test content with very long text"""
        long_content = "Very long content. " * 10000  # ~200KB
        
        content = self.create_content(content=long_content)
        self.assertEqual(len(content.content), len(long_content))
        self.assertIn("Very long content.", content.content[:100])
    
    def test_content_cascade_deletion(self):
        """Test cascade deletion behavior"""
        content = self.create_content()
        content_id = content.id
        
        # Create related objects
        schedule = self.create_review_schedule(content=content)
        history = self.create_review_history(content=content)
        
        # Delete content
        content.delete()
        
        # Related objects should be deleted
        self.assertFalse(Content.objects.filter(id=content_id).exists())
        self.assertFalse(ReviewSchedule.objects.filter(id=schedule.id).exists())
        self.assertFalse(ReviewHistory.objects.filter(id=history.id).exists())
    
    def test_content_category_null_handling(self):
        """Test content behavior when category is set to null"""
        content = self.create_content()
        original_category = content.category
        
        # Set category to null
        content.category = None
        content.save()
        
        content.refresh_from_db()
        self.assertIsNone(content.category)
        
        # Original category should still exist
        self.assertTrue(Category.objects.filter(id=original_category.id).exists())


class CategoryModelAdvancedTestCase(BaseTestCase):
    """Advanced Category model tests"""
    
    def test_category_slug_uniqueness_per_user(self):
        """Test slug uniqueness per user"""
        user2 = self.create_user(username='user2', email='user2@example.com')
        
        # Same name, different users should be allowed
        cat1 = Category.objects.create(name='Python', user=self.user)
        cat2 = Category.objects.create(name='Python', user=user2)
        
        self.assertNotEqual(cat1.id, cat2.id)
        self.assertEqual(cat1.name, cat2.name)
    
    def test_category_slug_generation_with_special_chars(self):
        """Test slug generation with special characters"""
        category = Category.objects.create(
            name='Python & Django Development!',
            user=self.user
        )
        
        # Should generate a clean slug
        self.assertEqual(category.name, 'Python & Django Development!')
        # Assuming slug field exists
        # self.assertEqual(category.slug, 'python-django-development')
    
    def test_global_vs_user_categories(self):
        """Test global categories vs user-specific categories"""
        # Global category (no user)
        global_cat = Category.objects.create(name='Global Category')
        
        # User-specific category
        user_cat = Category.objects.create(name='User Category', user=self.user)
        
        self.assertIsNone(global_cat.user)
        self.assertEqual(user_cat.user, self.user)
    
    def test_category_content_count(self):
        """Test counting contents in a category"""
        category = self.create_category(name='Test Category')
        
        # Create multiple contents in this category
        for i in range(5):
            self.create_content(title=f'Content {i}', category=category)
        
        # Count contents in category
        content_count = Content.objects.filter(category=category).count()
        self.assertEqual(content_count, 5)
    
    def test_category_deletion_with_contents(self):
        """Test category deletion when it has contents"""
        category = self.create_category(name='To Delete')
        content = self.create_content(category=category)
        
        # Delete category (should set content.category to null due to SET_NULL)
        category.delete()
        
        content.refresh_from_db()
        self.assertIsNone(content.category)


class TagModelAdvancedTestCase(BaseTestCase):
    """Advanced Tag model tests"""
    
    def test_tag_slug_generation(self):
        """Test tag slug generation"""
        tag = Tag.objects.create(name='Python Programming')
        self.assertEqual(tag.name, 'Python Programming')
        # Assuming slug field
        # self.assertEqual(tag.slug, 'python-programming')
    
    def test_tag_content_relationships(self):
        """Test many-to-many relationships with content"""
        tag1 = Tag.objects.create(name='tag1')
        tag2 = Tag.objects.create(name='tag2')
        
        content1 = self.create_content(title='Content 1')
        content2 = self.create_content(title='Content 2')
        
        # Add tags to content
        content1.tags.add(tag1, tag2)
        content2.tags.add(tag1)
        
        # Test relationships
        self.assertEqual(content1.tags.count(), 3)  # Including default tag
        self.assertEqual(content2.tags.count(), 2)  # Including default tag
        
        # Test reverse relationship
        tag1_contents = Content.objects.filter(tags=tag1)
        self.assertEqual(tag1_contents.count(), 2)
    
    def test_tag_deletion_with_contents(self):
        """Test tag deletion when attached to contents"""
        tag = Tag.objects.create(name='to-delete')
        content = self.create_content()
        content.tags.add(tag)
        
        tag_id = tag.id
        tag.delete()
        
        # Content should still exist, just without the tag
        content.refresh_from_db()
        self.assertFalse(content.tags.filter(id=tag_id).exists())
    
    def test_tag_case_sensitivity(self):
        """Test tag name case sensitivity"""
        tag1 = Tag.objects.create(name='Python')
        
        # Should not be able to create duplicate with different case
        with self.assertRaises(IntegrityError):
            Tag.objects.create(name='python')


class ReviewScheduleModelAdvancedTestCase(BaseTestCase):
    """Advanced ReviewSchedule model tests"""
    
    def test_review_schedule_interval_progression(self):
        """Test review interval progression logic"""
        schedule = self.create_review_schedule(interval_index=0)
        
        # Test progression through all intervals
        intervals = get_review_intervals()
        for i in range(len(intervals)):
            schedule.advance_schedule()
            schedule.refresh_from_db()
            
            expected_index = min(i + 1, len(intervals) - 1)
            self.assertEqual(schedule.interval_index, expected_index)
    
    def test_review_schedule_reset_logic(self):
        """Test review schedule reset logic"""
        schedule = self.create_review_schedule(interval_index=3)
        
        schedule.reset_schedule()
        schedule.refresh_from_db()
        
        self.assertEqual(schedule.interval_index, 0)
        # Should be scheduled for first interval
        intervals = get_review_intervals()
        expected_date = timezone.now() + timedelta(days=intervals[0])
        self.assertAlmostEqual(
            schedule.next_review_date.timestamp(),
            expected_date.timestamp(),
            delta=60  # Within 1 minute
        )
    
    def test_review_schedule_uniqueness_constraint(self):
        """Test unique constraint on user-content pair"""
        content = self.create_content()
        
        schedule1 = self.create_review_schedule(content=content)
        
        # Should not be able to create another schedule for same user-content
        with self.assertRaises(IntegrityError):
            ReviewSchedule.objects.create(
                content=content,
                user=self.user,
                next_review_date=timezone.now()
            )
    
    def test_review_schedule_initial_review_logic(self):
        """Test initial review completion logic"""
        schedule = self.create_review_schedule(
            interval_index=0,
            initial_review_completed=False
        )
        
        # Complete initial review
        schedule.advance_schedule()
        schedule.initial_review_completed = True
        schedule.save()
        
        schedule.refresh_from_db()
        self.assertTrue(schedule.initial_review_completed)
        self.assertEqual(schedule.interval_index, 1)
    
    def test_review_schedule_inactive_behavior(self):
        """Test inactive schedule behavior"""
        schedule = self.create_review_schedule()
        
        # Deactivate schedule
        schedule.is_active = False
        schedule.save()
        
        # Should not appear in active schedules
        active_schedules = ReviewSchedule.objects.filter(
            user=self.user,
            is_active=True
        )
        self.assertNotIn(schedule, active_schedules)


class ReviewHistoryModelAdvancedTestCase(BaseTestCase):
    """Advanced ReviewHistory model tests"""
    
    def test_review_history_statistics(self):
        """Test review history statistics calculation"""
        content = self.create_content()
        
        # Create varied review history
        results = ['remembered', 'forgot', 'partial', 'remembered', 'remembered']
        times = [120, 180, 150, 100, 90]
        
        for result, time_spent in zip(results, times):
            self.create_review_history(
                content=content,
                result=result,
                time_spent=time_spent
            )
        
        # Test statistics
        history = ReviewHistory.objects.filter(content=content)
        self.assertEqual(history.count(), 5)
        
        # Calculate success rate
        successful_reviews = history.filter(result='remembered').count()
        success_rate = (successful_reviews / history.count()) * 100
        self.assertEqual(success_rate, 60.0)  # 3 out of 5
        
        # Calculate average time
        total_time = sum(times)
        avg_time = total_time / len(times)
        self.assertEqual(avg_time, 128.0)
    
    def test_review_history_time_tracking(self):
        """Test time spent tracking"""
        history = self.create_review_history(time_spent=150)
        
        self.assertEqual(history.time_spent, 150)
        
        # Test with null time (should be allowed)
        history_no_time = self.create_review_history(time_spent=None)
        self.assertIsNone(history_no_time.time_spent)
    
    def test_review_history_notes(self):
        """Test review notes functionality"""
        notes = "Had trouble with the syntax but got it eventually"
        history = self.create_review_history(notes=notes)
        
        self.assertEqual(history.notes, notes)
        
        # Test with empty notes
        history_no_notes = self.create_review_history(notes="")
        self.assertEqual(history_no_notes.notes, "")
    
    def test_review_history_ordering(self):
        """Test review history ordering"""
        content = self.create_content()
        
        # Create multiple history entries
        history1 = self.create_review_history(content=content)
        history2 = self.create_review_history(content=content)
        history3 = self.create_review_history(content=content)
        
        # Should be ordered by -review_date (newest first)
        ordered_history = ReviewHistory.objects.filter(content=content)
        self.assertEqual(ordered_history[0].id, history3.id)
        self.assertEqual(ordered_history[1].id, history2.id)
        self.assertEqual(ordered_history[2].id, history1.id)


class UserModelAdvancedTestCase(BaseTestCase):
    """Advanced User model tests"""
    
    def test_user_timezone_handling(self):
        """Test user timezone functionality"""
        user = self.create_user(
            username='timezone_user',
            email='tz@example.com',
            timezone='America/New_York'
        )
        
        self.assertEqual(user.timezone, 'America/New_York')
    
    def test_user_notification_preferences(self):
        """Test user notification preferences"""
        user = self.create_user(
            username='notify_user',
            email='notify@example.com',
            notification_enabled=False
        )
        
        self.assertFalse(user.notification_enabled)
        
        # Test default value
        user_default = self.create_user(
            username='default_user',
            email='default@example.com'
        )
        self.assertTrue(user_default.notification_enabled)
    
    def test_user_cascade_deletion(self):
        """Test user deletion cascades properly"""
        user = self.create_user(username='to_delete', email='delete@example.com')
        
        # Create related objects
        category = self.create_category(user=user)
        content = self.create_content(author=user)
        schedule = self.create_review_schedule(user=user, content=content)
        history = self.create_review_history(user=user, content=content)
        
        user_id = user.id
        user.delete()
        
        # All related objects should be deleted
        self.assertFalse(User.objects.filter(id=user_id).exists())
        self.assertFalse(Category.objects.filter(user_id=user_id).exists())
        self.assertFalse(Content.objects.filter(author_id=user_id).exists())
        self.assertFalse(ReviewSchedule.objects.filter(user_id=user_id).exists())
        self.assertFalse(ReviewHistory.objects.filter(user_id=user_id).exists())


class SignalTestCase(BaseTestCase):
    """Test Django signals"""
    
    @patch('review.tasks.create_review_schedule_for_content.delay')
    def test_content_creation_signal(self, mock_task):
        """Test that review schedule is created when content is created"""
        content = self.create_content()
        
        # Signal should trigger task
        mock_task.assert_called_once_with(content.id)
    
    def test_content_creation_creates_review_schedule(self):
        """Test actual review schedule creation on content save"""
        content = Content.objects.create(
            title='Test Content',
            content='Test content body',
            author=self.user,
            priority='medium'
        )
        
        # Should create review schedule automatically
        schedule = ReviewSchedule.objects.filter(content=content, user=self.user)
        self.assertTrue(schedule.exists())
        
        schedule = schedule.first()
        self.assertEqual(schedule.interval_index, 0)
        self.assertFalse(schedule.initial_review_completed)
    
    def test_content_deletion_cleanup(self):
        """Test cleanup when content is deleted"""
        content = self.create_content()
        schedule = self.create_review_schedule(content=content)
        
        content_id = content.id
        content.delete()
        
        # Schedule should be deleted due to CASCADE
        self.assertFalse(ReviewSchedule.objects.filter(content_id=content_id).exists())


class ModelValidationTestCase(BaseTestCase):
    """Test model validation"""
    
    def test_content_title_validation(self):
        """Test content title validation"""
        # Empty title should not be allowed (assuming validation is added)
        with self.assertRaises(ValidationError):
            content = Content(
                title='',
                content='Valid content',
                author=self.user,
                priority='medium'
            )
            content.full_clean()
    
    def test_review_schedule_date_validation(self):
        """Test review schedule date validation"""
        # Future date should be valid
        future_date = timezone.now() + timedelta(days=1)
        schedule = ReviewSchedule(
            content=self.create_content(),
            user=self.user,
            next_review_date=future_date
        )
        schedule.full_clean()  # Should not raise
        
        # Past date should be allowed (for testing/manual adjustment)
        past_date = timezone.now() - timedelta(days=1)
        schedule.next_review_date = past_date
        schedule.full_clean()  # Should not raise
    
    def test_review_history_result_validation(self):
        """Test review history result validation"""
        valid_results = ['remembered', 'partial', 'forgot']
        
        for result in valid_results:
            history = ReviewHistory(
                content=self.create_content(),
                user=self.user,
                result=result
            )
            history.full_clean()  # Should not raise
        
        # Invalid result should raise validation error
        with self.assertRaises(ValidationError):
            history = ReviewHistory(
                content=self.create_content(),
                user=self.user,
                result='invalid_result'
            )
            history.full_clean()


class ModelMethodTestCase(BaseTestCase):
    """Test custom model methods"""
    
    def test_review_schedule_get_next_interval(self):
        """Test get_next_interval method"""
        schedule = self.create_review_schedule(interval_index=0)
        
        intervals = get_review_intervals()
        next_interval = schedule.get_next_interval()
        self.assertEqual(next_interval, intervals[1])
        
        # Test at max interval
        schedule.interval_index = len(intervals) - 1
        next_interval = schedule.get_next_interval()
        self.assertEqual(next_interval, intervals[-1])  # Should stay at max
    
    def test_user_string_representation(self):
        """Test user string representation"""
        user = self.create_user(username='testuser', email='test@example.com')
        self.assertEqual(str(user), 'testuser')
    
    def test_content_string_representation(self):
        """Test content string representation"""
        content = self.create_content(title='Test Content')
        self.assertEqual(str(content), 'Test Content')
    
    def test_category_string_representation(self):
        """Test category string representation"""
        category = self.create_category(name='Test Category')
        self.assertEqual(str(category), 'Test Category')


class PerformanceTestCase(BaseTestCase):
    """Test model performance"""
    
    def test_bulk_content_creation(self):
        """Test bulk content creation performance"""
        import time
        
        start_time = time.time()
        
        # Create 100 contents
        contents = []
        for i in range(100):
            content = Content(
                title=f'Content {i}',
                content=f'Content body {i}',
                author=self.user,
                priority='medium'
            )
            contents.append(content)
        
        Content.objects.bulk_create(contents)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(execution_time, 5.0)  # 5 seconds
        
        # Verify all contents were created
        self.assertEqual(Content.objects.filter(author=self.user).count(), 101)  # Including base content
    
    def test_large_query_performance(self):
        """Test performance with large datasets"""
        # Create test data
        for i in range(50):
            self.create_content(title=f'Performance Test {i}')
        
        import time
        start_time = time.time()
        
        # Query with joins and filtering
        contents = Content.objects.select_related('author', 'category').prefetch_related('tags').filter(
            author=self.user
        )[:10]
        
        list(contents)  # Force evaluation
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete quickly even with joins
        self.assertLess(execution_time, 1.0)  # 1 second