"""
Tests for review views and API endpoints.
"""
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Subscription, SubscriptionTier
from content.models import Category, Content
from review.models import ReviewHistory, ReviewSchedule

User = get_user_model()


class ReviewScheduleViewSetTest(TestCase):
    """Test ReviewScheduleViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(name='Test', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='Test body',
            author=self.user,
            category=self.category
        )
        # Signal auto-creates ReviewSchedule
        self.schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)

    def test_list_review_schedules(self):
        """Test listing review schedules."""
        response = self.client.get('/api/review/schedules/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_list_review_schedules_unauthenticated(self):
        """Test listing without authentication."""
        self.client.logout()

        response = self.client.get('/api/review/schedules/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_review_schedule(self):
        """Test retrieving a specific review schedule."""
        response = self.client.get(f'/api/review/schedules/{self.schedule.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['interval_index'], 0)

    def test_retrieve_schedule_not_owner(self):
        """Test retrieving another user's schedule."""
        user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user2)

        response = self.client.get(f'/api/review/schedules/{self.schedule.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TodayReviewViewTest(TestCase):
    """Test TodayReviewView."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(name='Test', user=self.user)

        # Create content with due review
        self.content = Content.objects.create(
            title='Test Content',
            content='Test body',
            author=self.user,
            category=self.category
        )
        # Update schedule to be due today
        self.schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)
        self.schedule.next_review_date = timezone.now()
        self.schedule.save()

    def test_get_today_reviews(self):
        """Test getting today's reviews."""
        response = self.client.get('/api/review/schedules/today/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertIn('subscription_tier', response.data)

    def test_get_today_reviews_category_filter(self):
        """Test filtering reviews by category."""
        # Create another category and content
        category2 = Category.objects.create(name='Category 2', user=self.user)
        content2 = Content.objects.create(
            title='Content 2',
            content='Body 2',
            author=self.user,
            category=category2
        )
        schedule2 = ReviewSchedule.objects.get(content=content2, user=self.user)
        schedule2.next_review_date = timezone.now()
        schedule2.save()

        # Filter by first category
        response = self.client.get(f'/api/review/schedules/today/?category_slug={self.category.slug}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_get_today_reviews_unauthenticated(self):
        """Test getting reviews without authentication."""
        self.client.logout()

        response = self.client.get('/api/review/schedules/today/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_today_reviews_includes_initial_uncompleted(self):
        """Test initial uncompleted reviews are always included."""
        # Create new content (initial_review_completed=False by default)
        new_content = Content.objects.create(
            title='New Content',
            content='New body',
            author=self.user
        )

        response = self.client.get('/api/review/schedules/today/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include both the due review and the new uncompleted one
        self.assertGreaterEqual(response.data['count'], 2)


class CompleteReviewViewTest(TestCase):
    """Test CompleteReviewView."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(name='Test', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='x' * 250,  # Need sufficient length for Content validation
            author=self.user,
            category=self.category,
            review_mode='objective'
        )
        self.schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)

    def test_complete_review_remembered(self):
        """Test completing review with 'remembered' result."""
        response = self.client.post(f'/api/review/schedules/{self.schedule.id}/completions/', {
            'result': 'remembered',
            'time_spent': 120,
            'notes': 'Good review'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('next_review_date', response.data)
        self.assertIn('interval_index', response.data)

        # Check schedule was updated
        self.schedule.refresh_from_db()
        self.assertEqual(self.schedule.interval_index, 1)
        self.assertTrue(self.schedule.initial_review_completed)

        # Check history was created
        history = ReviewHistory.objects.filter(
            content=self.content,
            user=self.user
        ).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.result, 'remembered')
        self.assertEqual(history.time_spent, 120)

    def test_complete_review_partial(self):
        """Test completing review with 'partial' result."""
        original_index = self.schedule.interval_index

        response = self.client.post(f'/api/review/schedules/{self.schedule.id}/completions/', {
            'result': 'partial',
            'time_spent': 90
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check schedule stays at same interval
        self.schedule.refresh_from_db()
        self.assertEqual(self.schedule.interval_index, original_index)
        self.assertTrue(self.schedule.initial_review_completed)

    def test_complete_review_forgot(self):
        """Test completing review with 'forgot' result."""
        # Advance schedule first
        self.schedule.interval_index = 3
        self.schedule.save()

        response = self.client.post(f'/api/review/schedules/{self.schedule.id}/completions/', {
            'result': 'forgot'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check schedule was reset to 0
        self.schedule.refresh_from_db()
        self.assertEqual(self.schedule.interval_index, 0)

    def test_complete_review_invalid_time_spent(self):
        """Test completing review with negative time_spent."""
        response = self.client.post(f'/api/review/schedules/{self.schedule.id}/completions/', {
            'result': 'remembered',
            'time_spent': -10
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_complete_review_time_spent_too_long(self):
        """Test completing review with excessive time_spent."""
        response = self.client.post(f'/api/review/schedules/{self.schedule.id}/completions/', {
            'result': 'remembered',
            'time_spent': 86401  # 24 hours + 1
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_complete_review_notes_too_long(self):
        """Test completing review with excessively long notes."""
        response = self.client.post(f'/api/review/schedules/{self.schedule.id}/completions/', {
            'result': 'remembered',
            'notes': 'x' * 5001  # Exceeds 5000 char limit
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_complete_review_missing_result(self):
        """Test completing objective mode without result."""
        response = self.client.post(f'/api/review/schedules/{self.schedule.id}/completions/', {
            # Missing result field
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_complete_review_invalid_result(self):
        """Test completing review with invalid result value."""
        response = self.client.post(f'/api/review/schedules/{self.schedule.id}/completions/', {
            'result': 'invalid_result'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CompleteReviewMultipleChoiceTest(TestCase):
    """Test CompleteReviewView for multiple choice mode."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.client.force_authenticate(user=self.user)

        self.content = Content.objects.create(
            title='Test Content',
            content='x' * 250,  # Need sufficient length for Content validation
            author=self.user,
            review_mode='multiple_choice',
            mc_choices={
                'correct_answer': 'Option A',
                'choices': ['Option A', 'Option B', 'Option C', 'Option D']
            }
        )
        self.schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)

    def test_complete_review_mc_correct(self):
        """Test completing multiple choice with correct answer."""
        response = self.client.post(f'/api/review/schedules/{self.schedule.id}/completions/', {
            'selected_choice': 'Option A'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['final_result'], 'remembered')
        self.assertIn('ai_evaluation', response.data)
        self.assertEqual(response.data['ai_evaluation']['score'], 100.0)

    def test_complete_review_mc_incorrect(self):
        """Test completing multiple choice with incorrect answer."""
        response = self.client.post(f'/api/review/schedules/{self.schedule.id}/completions/', {
            'selected_choice': 'Option B'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['final_result'], 'forgot')
        self.assertIn('ai_evaluation', response.data)
        self.assertEqual(response.data['ai_evaluation']['score'], 0.0)

    def test_complete_review_mc_missing_choice(self):
        """Test completing multiple choice without selected_choice."""
        response = self.client.post(f'/api/review/schedules/{self.schedule.id}/completions/', {
            # Missing selected_choice
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CompleteReviewSubjectiveTest(TestCase):
    """Test CompleteReviewView for subjective mode (AI title evaluation)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.client.force_authenticate(user=self.user)

        self.content = Content.objects.create(
            title='Python Programming Basics',
            content='x' * 250,  # Need sufficient length for AI validation
            author=self.user,
            review_mode='subjective'
        )
        self.schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)

    @patch('ai_services.ai_title_evaluator')
    def test_complete_review_subjective_good_title(self, mock_evaluator):
        """Test subjective mode with good user title (AI score >= 70)."""
        mock_evaluator.is_available.return_value = True
        mock_evaluator.evaluate_title.return_value = {
            'score': 85.0,
            'evaluation': 'good',
            'feedback': 'Good understanding',
            'auto_result': 'remembered'
        }

        response = self.client.post(f'/api/review/schedules/{self.schedule.id}/completions/', {
            'user_title': 'Python Basics'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['final_result'], 'remembered')
        self.assertIn('ai_evaluation', response.data)
        self.assertEqual(response.data['ai_evaluation']['score'], 85.0)

        # Check schedule advanced
        self.schedule.refresh_from_db()
        self.assertEqual(self.schedule.interval_index, 1)

        # Check history created
        history = ReviewHistory.objects.filter(
            content=self.content,
            user=self.user
        ).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.result, 'remembered')
        self.assertEqual(history.user_title, 'Python Basics')
        self.assertEqual(history.ai_score, 85.0)

    @patch('ai_services.ai_title_evaluator')
    def test_complete_review_subjective_poor_title(self, mock_evaluator):
        """Test subjective mode with poor user title (AI score < 70)."""
        mock_evaluator.is_available.return_value = True
        mock_evaluator.evaluate_title.return_value = {
            'score': 45.0,
            'evaluation': 'poor',
            'feedback': 'Need improvement',
            'auto_result': 'forgot'
        }

        response = self.client.post(f'/api/review/schedules/{self.schedule.id}/completions/', {
            'user_title': 'Something wrong'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['final_result'], 'forgot')
        self.assertEqual(response.data['ai_evaluation']['score'], 45.0)

        # Check schedule reset to 0
        self.schedule.refresh_from_db()
        self.assertEqual(self.schedule.interval_index, 0)

    def test_complete_review_subjective_missing_user_title(self):
        """Test subjective mode without user_title."""
        response = self.client.post(f'/api/review/schedules/{self.schedule.id}/completions/', {
            # Missing user_title
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    @patch('ai_services.ai_title_evaluator')
    def test_complete_review_subjective_ai_unavailable(self, mock_evaluator):
        """Test subjective mode when AI service is unavailable."""
        mock_evaluator.is_available.return_value = False

        response = self.client.post(f'/api/review/schedules/{self.schedule.id}/completions/', {
            'user_title': 'Python Basics'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)


class CompleteReviewDescriptiveTest(TestCase):
    """Test CompleteReviewView for descriptive mode (AI answer evaluation)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.client.force_authenticate(user=self.user)

        self.content = Content.objects.create(
            title='Django ORM Concepts',
            content='x' * 250,  # Need sufficient length for AI validation
            author=self.user,
            review_mode='descriptive'
        )
        self.schedule = ReviewSchedule.objects.get(content=self.content, user=self.user)

    @patch('ai_services.ai_answer_evaluator')
    def test_complete_review_descriptive_good_answer(self, mock_evaluator):
        """Test descriptive mode with good answer (AI score >= 70)."""
        mock_evaluator.is_available.return_value = True
        mock_evaluator.evaluate_answer.return_value = {
            'score': 90.0,
            'evaluation': 'excellent',
            'feedback': 'Excellent understanding',
            'auto_result': 'remembered'
        }

        response = self.client.post(f'/api/review/schedules/{self.schedule.id}/completions/', {
            'descriptive_answer': 'Django ORM provides an abstraction layer for database operations...'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['final_result'], 'remembered')
        self.assertIn('ai_evaluation', response.data)
        self.assertEqual(response.data['ai_evaluation']['score'], 90.0)

        # Check schedule advanced
        self.schedule.refresh_from_db()
        self.assertEqual(self.schedule.interval_index, 1)

        # Check history created
        history = ReviewHistory.objects.filter(
            content=self.content,
            user=self.user
        ).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.result, 'remembered')
        self.assertEqual(history.descriptive_answer, 'Django ORM provides an abstraction layer for database operations...')
        self.assertEqual(history.ai_score, 90.0)

    @patch('ai_services.ai_answer_evaluator')
    def test_complete_review_descriptive_poor_answer(self, mock_evaluator):
        """Test descriptive mode with poor answer (AI score < 70)."""
        mock_evaluator.is_available.return_value = True
        mock_evaluator.evaluate_answer.return_value = {
            'score': 35.0,
            'evaluation': 'poor',
            'feedback': 'Major gaps in understanding',
            'auto_result': 'forgot'
        }

        response = self.client.post(f'/api/review/schedules/{self.schedule.id}/completions/', {
            'descriptive_answer': 'I don\'t know'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['final_result'], 'forgot')
        self.assertEqual(response.data['ai_evaluation']['score'], 35.0)

        # Check schedule reset to 0
        self.schedule.refresh_from_db()
        self.assertEqual(self.schedule.interval_index, 0)

    def test_complete_review_descriptive_missing_answer(self):
        """Test descriptive mode without descriptive_answer."""
        response = self.client.post(f'/api/review/schedules/{self.schedule.id}/completions/', {
            # Missing descriptive_answer
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    @patch('ai_services.ai_answer_evaluator')
    def test_complete_review_descriptive_ai_unavailable(self, mock_evaluator):
        """Test descriptive mode when AI service is unavailable."""
        mock_evaluator.is_available.return_value = False

        response = self.client.post(f'/api/review/schedules/{self.schedule.id}/completions/', {
            'descriptive_answer': 'Some answer here'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)


class ReviewHistoryViewSetTest(TestCase):
    """Test ReviewHistoryViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(name='Test', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='Test body',
            author=self.user,
            category=self.category
        )

        # Create review histories
        ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='remembered',
            time_spent=120
        )
        ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='forgot',
            time_spent=90
        )

    def test_list_review_histories(self):
        """Test listing review histories."""
        response = self.client.get('/api/review/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)

    def test_list_review_histories_ordering(self):
        """Test histories are ordered by recent first."""
        response = self.client.get('/api/review/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Most recent should be first (forgot, then remembered)
        results = response.data['results']
        self.assertEqual(results[0]['result'], 'forgot')
        self.assertEqual(results[1]['result'], 'remembered')

    def test_list_review_histories_unauthenticated(self):
        """Test listing without authentication."""
        self.client.logout()

        response = self.client.get('/api/review/history/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_review_history(self):
        """Test retrieving a specific history."""
        history = ReviewHistory.objects.first()

        response = self.client.get(f'/api/review/history/{history.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['result'], history.result)


class DashboardStatsViewTest(TestCase):
    """Test DashboardStatsView."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.client.force_authenticate(user=self.user)

        # Create some test data
        self.category = Category.objects.create(name='Test', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='Test body',
            author=self.user,
            category=self.category
        )

    def test_get_dashboard_stats(self):
        """Test getting dashboard statistics."""
        response = self.client.get('/api/review/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check required fields
        self.assertIn('today_reviews', response.data)
        self.assertIn('pending_reviews', response.data)
        self.assertIn('total_content', response.data)
        self.assertIn('success_rate', response.data)
        self.assertIn('total_reviews_30_days', response.data)

    def test_get_dashboard_stats_with_reviews(self):
        """Test dashboard stats with review history."""
        # Complete a review
        ReviewHistory.objects.create(
            content=self.content,
            user=self.user,
            result='remembered',
            time_spent=120
        )

        response = self.client.get('/api/review/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_content'], 1)
        self.assertEqual(response.data['total_reviews_30_days'], 1)

    def test_get_dashboard_stats_unauthenticated(self):
        """Test getting stats without authentication."""
        self.client.logout()

        response = self.client.get('/api/review/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CategoryReviewStatsViewTest(TestCase):
    """Test CategoryReviewStatsView."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(name='Test Category', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='Test body',
            author=self.user,
            category=self.category
        )

    def test_get_category_stats(self):
        """Test getting category statistics."""
        response = self.client.get('/api/review/category-stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should have stats for our category
        self.assertIn(self.category.slug, response.data)
        stats = response.data[self.category.slug]
        self.assertEqual(stats['category'], self.category.name)
        self.assertIn('total_content', stats)
        self.assertIn('today_reviews', stats)
        self.assertIn('success_rate', stats)

    def test_get_category_stats_unauthenticated(self):
        """Test getting stats without authentication."""
        self.client.logout()

        response = self.client.get('/api/review/category-stats/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
