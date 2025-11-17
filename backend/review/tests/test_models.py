"""
Tests for review models (ReviewSchedule and ReviewHistory).
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from content.models import Category, Content
from review.models import ReviewHistory, ReviewSchedule

User = get_user_model()


class ReviewScheduleModelTest(TestCase):
    """Test ReviewSchedule model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.category = Category.objects.create(name='Test', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='Test body',
            author=self.user,
            category=self.category
        )

    def test_review_schedule_creation(self):
        """Test basic review schedule creation."""
        # Signal auto-creates ReviewSchedule when Content is created
        schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)

        self.assertEqual(schedule.content, self.content)
        self.assertEqual(schedule.user, self.user)
        self.assertEqual(schedule.interval_index, 0)
        self.assertTrue(schedule.is_active)
        self.assertFalse(schedule.initial_review_completed)

    def test_review_schedule_default_values(self):
        """Test default field values."""
        # Use auto-created schedule from setUp
        schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)

        self.assertEqual(schedule.interval_index, 0)
        self.assertTrue(schedule.is_active)
        self.assertFalse(schedule.initial_review_completed)

    def test_review_schedule_str(self):
        """Test string representation."""
        # Use auto-created schedule and update interval_index
        schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)
        schedule.interval_index = 2
        schedule.save()

        expected = f"{self.content.title} - {self.user.email} (interval: 2)"
        self.assertEqual(str(schedule), expected)

    def test_review_schedule_unique_together(self):
        """Test unique_together constraint for content and user."""
        # Signal already created one ReviewSchedule for this content/user
        # Try to create duplicate (should fail)
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            ReviewSchedule.objects.create(
                content=self.content,
                user=self.user,
                next_review_date=timezone.now() + timedelta(days=2)
            )

    def test_review_schedule_ordering(self):
        """Test ordering by next_review_date."""
        now = timezone.now()

        # Get schedule auto-created for self.content
        schedule1 = ReviewSchedule.objects.get(content=self.content, user=self.user)
        schedule1.next_review_date = now + timedelta(days=3)
        schedule1.save()

        # Create second content (auto-creates its schedule)
        content2 = Content.objects.create(
            title='Content 2',
            content='Body',
            author=self.user
        )
        schedule2 = ReviewSchedule.objects.get(content=content2, user=self.user)
        schedule2.next_review_date = now + timedelta(days=1)
        schedule2.save()

        schedules = list(ReviewSchedule.objects.all())
        self.assertEqual(schedules[0].id, schedule2.id)  # Earlier date first
        self.assertEqual(schedules[1].id, schedule1.id)

    def test_review_schedule_validation_content_user_mismatch(self):
        """Test validation when content belongs to different user."""
        user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )

        schedule = ReviewSchedule(
            content=self.content,  # belongs to self.user
            user=user2,  # different user
            next_review_date=timezone.now() + timedelta(days=1)
        )

        with self.assertRaises(ValidationError) as context:
            schedule.save()

        self.assertIn('content', context.exception.message_dict)

    def test_review_schedule_interval_index_non_negative(self):
        """Test interval_index must be non-negative."""
        # This is enforced by database constraint
        schedule = ReviewSchedule(
            content=self.content,
            user=self.user,
            next_review_date=timezone.now() + timedelta(days=1),
            interval_index=-1
        )

        with self.assertRaises(ValidationError):
            schedule.save()

    def test_get_next_interval(self):
        """Test get_next_interval method."""
        # Use auto-created schedule
        schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)

        next_interval = schedule.get_next_interval()
        self.assertIsInstance(next_interval, int)
        self.assertGreater(next_interval, 0)

    def test_advance_schedule(self):
        """Test advance_schedule method."""
        # Use auto-created schedule
        schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)

        original_index = schedule.interval_index
        schedule.advance_schedule()

        self.assertEqual(schedule.interval_index, original_index + 1)
        self.assertIsNotNone(schedule.next_review_date)

    def test_reset_schedule(self):
        """Test reset_schedule method."""
        # Use auto-created schedule and advance it first
        schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)
        schedule.interval_index = 5
        schedule.next_review_date = timezone.now() + timedelta(days=30)
        schedule.save()

        schedule.reset_schedule()

        self.assertEqual(schedule.interval_index, 0)
        # Next review date should be soon (1-3 days typically)


class ReviewHistoryModelTest(TestCase):
    """Test ReviewHistory model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.category = Category.objects.create(name='Test', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='Test body',
            author=self.user,
            category=self.category
        )

    def test_review_history_creation(self):
        """Test basic review history creation."""
        history = ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='remembered',
            time_spent=120,
            notes='Good review'
        )

        self.assertEqual(history.content, self.content)
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.result, 'remembered')
        self.assertEqual(history.time_spent, 120)
        self.assertEqual(history.notes, 'Good review')

    def test_review_history_result_choices(self):
        """Test all result choices."""
        results = ['remembered', 'partial', 'forgot']

        for result in results:
            history = ReviewHistory.objects.create(
                content=self.content,
                user=self.user,
                result=result
            )
            self.assertEqual(history.result, result)

    def test_review_history_str(self):
        """Test string representation."""
        history = ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='remembered'
        )

        expected = f"{self.content.title} - remembered"
        self.assertEqual(str(history), expected)

    def test_review_history_ordering(self):
        """Test ordering by review_date descending."""
        history1 = ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='remembered'
        )

        # Small delay to ensure different timestamps
        import time
        time.sleep(0.01)

        history2 = ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='forgot'
        )

        histories = list(ReviewHistory.objects.all())
        self.assertEqual(histories[0].id, history2.id)  # Most recent first
        self.assertEqual(histories[1].id, history1.id)

    def test_review_history_with_ai_fields(self):
        """Test with AI evaluation fields."""
        history = ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='remembered',
            descriptive_answer='User answer here',
            ai_score=85.5,
            ai_feedback='Good answer'
        )

        history.refresh_from_db()
        self.assertEqual(history.descriptive_answer, 'User answer here')
        self.assertEqual(history.ai_score, 85.5)
        self.assertEqual(history.ai_feedback, 'Good answer')

    def test_review_history_with_selected_choice(self):
        """Test with multiple choice selected_choice field."""
        history = ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='remembered',
            selected_choice='Option A'
        )

        history.refresh_from_db()
        self.assertEqual(history.selected_choice, 'Option A')

    def test_review_history_with_user_title(self):
        """Test with subjective mode user_title field."""
        history = ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='remembered',
            user_title='My Guess'
        )

        history.refresh_from_db()
        self.assertEqual(history.user_title, 'My Guess')

    def test_review_history_validation_content_user_mismatch(self):
        """Test validation when content belongs to different user."""
        user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )

        history = ReviewHistory(
            content=self.content,  # belongs to self.user
            user=user2,  # different user
            result='remembered'
        )

        with self.assertRaises(ValidationError) as context:
            history.save()

        self.assertIn('content', context.exception.message_dict)

    def test_review_history_time_spent_validation(self):
        """Test time_spent cannot exceed 24 hours."""
        history = ReviewHistory(
            content=self.content,
            user=self.user,
            result='remembered',
            time_spent=86401  # 24 hours + 1 second
        )

        with self.assertRaises(ValidationError) as context:
            history.save()

        self.assertIn('time_spent', context.exception.message_dict)

    def test_review_history_time_spent_non_negative(self):
        """Test time_spent must be non-negative."""
        history = ReviewHistory(
            content=self.content,
            user=self.user,
            result='remembered',
            time_spent=-1
        )

        with self.assertRaises(ValidationError):
            history.save()

    def test_review_history_time_spent_null_allowed(self):
        """Test time_spent can be null."""
        history = ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='remembered',
            time_spent=None
        )

        history.refresh_from_db()
        self.assertIsNone(history.time_spent)

    def test_review_history_auto_now_add(self):
        """Test review_date is auto-set."""
        before = timezone.now()

        history = ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='remembered'
        )

        after = timezone.now()

        self.assertIsNotNone(history.review_date)
        self.assertGreaterEqual(history.review_date, before)
        self.assertLessEqual(history.review_date, after)
