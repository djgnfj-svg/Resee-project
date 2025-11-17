"""
Tests for content signals.
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from content.models import Content
from review.models import ReviewSchedule

User = get_user_model()


class ContentSignalTest(TestCase):
    """Test content creation signals."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )

    def test_review_schedule_created_on_content_creation(self):
        """Test ReviewSchedule is automatically created when content is created."""
        content = Content.objects.create(
            title='Python Basics',
            content='Python is a programming language.',
            author=self.user
        )

        # Check ReviewSchedule was created
        schedule = ReviewSchedule.objects.filter(content=content, user=self.user).first()
        self.assertIsNotNone(schedule)
        self.assertEqual(schedule.interval_index, 0)
        self.assertTrue(schedule.is_active)

    def test_review_schedule_not_created_on_update(self):
        """Test ReviewSchedule is not created again when content is updated."""
        content = Content.objects.create(
            title='Original',
            content='Original content',
            author=self.user
        )

        # Get the created schedule
        original_schedule = ReviewSchedule.objects.get(content=content, user=self.user)
        original_schedule_id = original_schedule.id

        # Update content
        content.title = 'Updated'
        content.save()

        # Check no new schedule was created
        schedules = ReviewSchedule.objects.filter(content=content, user=self.user)
        self.assertEqual(schedules.count(), 1)
        self.assertEqual(schedules.first().id, original_schedule_id)

    @patch('ai_services.mc_generator.generate_multiple_choice_options')
    def test_mc_choices_generated_for_multiple_choice_mode(self, mock_generate_mc):
        """Test MC choices are generated for multiple_choice mode."""
        mock_generate_mc.return_value = {
            'choices': ['A', 'B', 'C', 'D'],
            'correct_answer': 'A'
        }

        content = Content.objects.create(
            title='Test',
            content='x' * 250,
            author=self.user,
            review_mode='multiple_choice'
        )

        # MC options should be generated (may be called multiple times due to signal + serializer)
        self.assertTrue(mock_generate_mc.called)

        # Refresh to get updated mc_choices
        content.refresh_from_db()
        self.assertIsNotNone(content.mc_choices)
        self.assertEqual(content.mc_choices['correct_answer'], 'A')

    def test_mc_choices_not_generated_for_objective_mode(self):
        """Test MC choices are not generated for objective mode."""
        content = Content.objects.create(
            title='Test',
            content='Test content',
            author=self.user,
            review_mode='objective'
        )

        # MC options should NOT be generated for objective mode
        self.assertIsNone(content.mc_choices)

    def test_mc_choices_not_generated_if_already_exists(self):
        """Test MC choices are not regenerated if they already exist."""
        existing_choices = {
            'choices': ['Existing A', 'Existing B', 'Existing C', 'Existing D'],
            'correct_answer': 'Existing A'
        }

        content = Content.objects.create(
            title='Test',
            content='x' * 250,
            author=self.user,
            review_mode='multiple_choice',
            mc_choices=existing_choices
        )

        # MC choices should remain as provided
        content.refresh_from_db()
        self.assertEqual(content.mc_choices['correct_answer'], 'Existing A')

    @patch('ai_services.mc_generator.generate_multiple_choice_options')
    def test_mc_choices_generation_error_handling(self, mock_generate_mc):
        """Test MC choices generation handles errors gracefully."""
        mock_generate_mc.side_effect = Exception('API Error')

        # Should not raise exception, just log error
        content = Content.objects.create(
            title='Test',
            content='x' * 250,
            author=self.user,
            review_mode='multiple_choice'
        )

        # Content should be created despite MC generation failure
        self.assertIsNotNone(content.id)

    @patch('ai_services.mc_generator.generate_multiple_choice_options')
    def test_mc_choices_not_generated_on_update(self, mock_generate_mc):
        """Test MC choices signal only triggers on creation, not update."""
        mock_generate_mc.return_value = {
            'choices': ['A', 'B', 'C', 'D'],
            'correct_answer': 'A'
        }

        content = Content.objects.create(
            title='Test',
            content='x' * 250,
            author=self.user,
            review_mode='multiple_choice'
        )

        initial_call_count = mock_generate_mc.call_count

        # Update content (not title/content to avoid serializer regeneration)
        content.review_mode = 'objective'  # Change to non-MC mode
        content.save()

        # MC generation call count should not increase
        self.assertEqual(mock_generate_mc.call_count, initial_call_count)
