"""
Tests for review serializers.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from content.models import Category, Content
from review.models import ReviewHistory, ReviewSchedule
from review.serializers import (
    ReviewHistorySerializer, ReviewScheduleSerializer,
)

User = get_user_model()


class ReviewScheduleSerializerTest(TestCase):
    """Test ReviewScheduleSerializer."""

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
        # Signal auto-creates ReviewSchedule
        self.schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)

    def test_serialize_review_schedule(self):
        """Test serializing a review schedule."""
        serializer = ReviewScheduleSerializer(self.schedule)
        data = serializer.data

        self.assertEqual(data['interval_index'], 0)
        self.assertTrue(data['is_active'])
        self.assertFalse(data['initial_review_completed'])
        self.assertIsNotNone(data['content'])  # Nested content
        self.assertEqual(data['content']['title'], 'Test Content')

    def test_serialize_review_schedule_with_advanced_interval(self):
        """Test serializing schedule with advanced interval."""
        self.schedule.interval_index = 3
        self.schedule.initial_review_completed = True
        self.schedule.save()

        serializer = ReviewScheduleSerializer(self.schedule)
        data = serializer.data

        self.assertEqual(data['interval_index'], 3)
        self.assertTrue(data['initial_review_completed'])

    def test_read_only_fields(self):
        """Test read-only fields."""
        read_only = ReviewScheduleSerializer.Meta.read_only_fields
        self.assertIn('id', read_only)
        self.assertIn('user', read_only)
        self.assertIn('created_at', read_only)
        self.assertIn('updated_at', read_only)

    def test_serialize_multiple_schedules(self):
        """Test serializing multiple schedules."""
        # Create additional content
        content2 = Content.objects.create(
            title='Content 2',
            content='Body 2',
            author=self.user,
            category=self.category
        )

        schedules = ReviewSchedule.objects.all()
        serializer = ReviewScheduleSerializer(schedules, many=True)

        self.assertEqual(len(serializer.data), 2)


class ReviewHistorySerializerTest(TestCase):
    """Test ReviewHistorySerializer."""

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

    def test_serialize_review_history(self):
        """Test serializing a review history."""
        history = ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='remembered',
            time_spent=120,
            notes='Good review'
        )

        serializer = ReviewHistorySerializer(history)
        data = serializer.data

        self.assertEqual(data['result'], 'remembered')
        self.assertEqual(data['time_spent'], 120)
        self.assertEqual(data['notes'], 'Good review')
        self.assertIsNotNone(data['content'])  # Nested content
        self.assertEqual(data['content']['title'], 'Test Content')

    def test_serialize_review_history_with_ai_fields(self):
        """Test serializing history with AI evaluation fields."""
        history = ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='remembered',
            descriptive_answer='User answer here',
            ai_score=85.5,
            ai_feedback='Good answer'
        )

        serializer = ReviewHistorySerializer(history)
        data = serializer.data

        self.assertEqual(data['descriptive_answer'], 'User answer here')
        self.assertEqual(data['ai_score'], 85.5)
        self.assertEqual(data['ai_feedback'], 'Good answer')

    def test_read_only_fields(self):
        """Test read-only fields."""
        read_only = ReviewHistorySerializer.Meta.read_only_fields
        self.assertIn('id', read_only)
        self.assertIn('user', read_only)
        self.assertIn('review_date', read_only)
        self.assertIn('ai_score', read_only)
        self.assertIn('ai_feedback', read_only)

    def test_serialize_review_history_all_results(self):
        """Test serializing histories with all result types."""
        results = ['remembered', 'partial', 'forgot']

        for result in results:
            history = ReviewHistory.objects.create(
                content=self.content,
                user=self.user,
                result=result
            )

            serializer = ReviewHistorySerializer(history)
            self.assertEqual(serializer.data['result'], result)

            # Clean up for next iteration
            history.delete()

    def test_serialize_multiple_histories(self):
        """Test serializing multiple review histories."""
        for i in range(3):
            ReviewHistory.objects.create(
                content=self.content,
                user=self.user,
                result='remembered',
                notes=f'Review {i}'
            )

        histories = ReviewHistory.objects.all()
        serializer = ReviewHistorySerializer(histories, many=True)

        self.assertEqual(len(serializer.data), 3)

    def test_serialize_review_history_null_time_spent(self):
        """Test serializing history with null time_spent."""
        history = ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='remembered',
            time_spent=None
        )

        serializer = ReviewHistorySerializer(history)
        data = serializer.data

        self.assertIsNone(data['time_spent'])

    def test_serialize_review_history_ordering(self):
        """Test histories are serialized in correct order (recent first)."""
        import time

        history1 = ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='remembered'
        )

        time.sleep(0.01)  # Ensure different timestamps

        history2 = ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='forgot'
        )

        histories = ReviewHistory.objects.all()
        serializer = ReviewHistorySerializer(histories, many=True)

        # Most recent first (history2 before history1)
        self.assertEqual(serializer.data[0]['id'], history2.id)
        self.assertEqual(serializer.data[1]['id'], history1.id)
