"""
Tests for exams views and API endpoints.
"""
from datetime import date, timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from content.models import Category, Content
from exams.models import WeeklyTest, WeeklyTestAnswer, WeeklyTestQuestion

User = get_user_model()


class WeeklyTestListCreateViewTest(TestCase):
    """Test WeeklyTest list and create endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(name='Test', user=self.user)

        # Create AI-validated contents
        self.contents = []
        for i in range(10):
            content = Content.objects.create(
                title=f'Content {i}',
                content='x' * 300,
                author=self.user,
                category=self.category,
                is_ai_validated=True,
                ai_validation_score=90
            )
            self.contents.append(content)

    def test_list_weekly_tests(self):
        """Test listing user's weekly tests."""
        WeeklyTest.objects.create(
            user=self.user,
            title='Test 1'
        )
        WeeklyTest.objects.create(
            user=self.user,
            title='Test 2'
        )

        response = self.client.get('/api/exams/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)

    def test_list_weekly_tests_unauthenticated(self):
        """Test listing without authentication."""
        self.client.logout()

        response = self.client.get('/api/exams/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('exams.views.WeeklyTestListCreateView._is_ai_available')
    @patch('exams.views.WeeklyTestListCreateView._create_simple_question')
    def test_create_weekly_test_with_content_ids(self, mock_simple, mock_ai_available):
        """Test creating weekly test with manual content selection."""
        mock_ai_available.return_value = False

        content_ids = [c.id for c in self.contents[:7]]

        response = self.client.post('/api/exams/', {
            'title': 'My Test',
            'content_ids': content_ids
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'My Test')

        # Check test was created
        test = WeeklyTest.objects.get(id=response.data['id'])
        self.assertEqual(test.user, self.user)

    @patch('exams.views.WeeklyTestListCreateView._is_ai_available')
    @patch('ai_services.graphs.select_balanced_contents_for_test')
    @patch('exams.views.WeeklyTestListCreateView._create_simple_question')
    def test_create_weekly_test_auto_balance(self, mock_simple, mock_balance, mock_ai_available):
        """Test creating weekly test with auto-balancing."""
        mock_ai_available.return_value = False
        mock_balance.return_value = [c.id for c in self.contents[:7]]

        response = self.client.post('/api/exams/', {
            'title': 'Auto Test'
            # No content_ids - triggers auto-balancing
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch('exams.views.WeeklyTestListCreateView._is_ai_available')
    def test_create_weekly_test_ai_unavailable(self, mock_ai_available):
        """Test creating test when AI is unavailable."""
        mock_ai_available.return_value = False

        content_ids = [c.id for c in self.contents[:7]]

        response = self.client.post('/api/exams/', {
            'title': 'Test',
            'content_ids': content_ids
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_weekly_test_limit_exceeded(self):
        """Test weekly limit enforcement."""
        # Create a test this week
        WeeklyTest.objects.create(
            user=self.user,
            title='This Week Test'
        )

        content_ids = [c.id for c in self.contents[:7]]

        # Try to create another
        response = self.client.post('/api/exams/', {
            'title': 'Second Test',
            'content_ids': content_ids
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertIn('주당', str(response.data['detail']))

    def test_create_weekly_test_invalid_content_ids(self):
        """Test creating with invalid content IDs."""
        response = self.client.post('/api/exams/', {
            'title': 'Test',
            'content_ids': [99999, 99998, 99997, 99996, 99995, 99994, 99993]
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content_ids', response.data)


class WeeklyTestDetailViewTest(TestCase):
    """Test WeeklyTest detail, update, delete endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.client.force_authenticate(user=self.user)

        self.test = WeeklyTest.objects.create(
            user=self.user,
            title='Original Title',
            status='pending'
        )

    def test_retrieve_weekly_test(self):
        """Test retrieving a specific weekly test."""
        response = self.client.get(f'/api/exams/{self.test.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Original Title')

    def test_update_weekly_test(self):
        """Test updating a weekly test."""
        response = self.client.patch(f'/api/exams/{self.test.id}/', {
            'title': 'Updated Title'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')

        self.test.refresh_from_db()
        self.assertEqual(self.test.title, 'Updated Title')

    def test_delete_weekly_test(self):
        """Test deleting a weekly test."""
        response = self.client.delete(f'/api/exams/{self.test.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(WeeklyTest.objects.filter(id=self.test.id).exists())

    def test_retrieve_not_owner(self):
        """Test retrieving another user's test."""
        user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user2)

        response = self.client.get(f'/api/exams/{self.test.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class StartTestViewTest(TestCase):
    """Test start_test endpoint."""

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
            title='Test',
            content='Test body',
            author=self.user,
            category=self.category
        )

        self.test = WeeklyTest.objects.create(
            user=self.user,
            status='pending'
        )

        # Add a question
        self.question = WeeklyTestQuestion.objects.create(
            weekly_test=self.test,
            content=self.content,
            question_text='Test question',
            correct_answer='A',
            order=1
        )

        # Update question count
        self.test.total_questions = 1
        self.test.save()

    def test_start_test(self):
        """Test starting a test."""
        response = self.client.post('/api/exams/start/', {
            'test_id': self.test.id
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # Check test status updated
        self.test.refresh_from_db()
        self.assertEqual(self.test.status, 'in_progress')
        self.assertIsNotNone(self.test.started_at)

    def test_start_test_not_exists(self):
        """Test starting non-existent test."""
        response = self.client.post('/api/exams/start/', {
            'test_id': 99999
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_start_test_already_completed(self):
        """Test starting already completed test."""
        self.test.status = 'completed'
        self.test.save()

        response = self.client.post('/api/exams/start/', {
            'test_id': self.test.id
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SubmitAnswerViewTest(TestCase):
    """Test submit_answer endpoint."""

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
            title='Test',
            content='Test body',
            author=self.user,
            category=self.category
        )

        self.test = WeeklyTest.objects.create(
            user=self.user,
            status='in_progress',
            total_questions=1
        )

        self.question = WeeklyTestQuestion.objects.create(
            weekly_test=self.test,
            content=self.content,
            question_text='What is 2+2?',
            correct_answer='4',
            order=1,
            points=10
        )

    def test_submit_answer_correct(self):
        """Test submitting correct answer."""
        response = self.client.post('/api/exams/submit-answer/', {
            'question_id': self.question.id,
            'user_answer': '4'
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_correct'])
        self.assertEqual(response.data['points_earned'], 10)

    def test_submit_answer_incorrect(self):
        """Test submitting incorrect answer."""
        response = self.client.post('/api/exams/submit-answer/', {
            'question_id': self.question.id,
            'user_answer': '5'
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['is_correct'])
        self.assertEqual(response.data['points_earned'], 0)

    def test_submit_answer_invalid_question(self):
        """Test submitting answer to invalid question."""
        response = self.client.post('/api/exams/submit-answer/', {
            'question_id': 99999,
            'user_answer': 'A'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CompleteTestViewTest(TestCase):
    """Test complete_test endpoint."""

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
            title='Test',
            content='Test body',
            author=self.user,
            category=self.category
        )

        self.test = WeeklyTest.objects.create(
            user=self.user,
            status='in_progress',
            total_questions=2,
            started_at=timezone.now()
        )

        # Create questions
        for i in range(2):
            question = WeeklyTestQuestion.objects.create(
                weekly_test=self.test,
                content=self.content,
                question_text=f'Question {i}',
                correct_answer='A',
                order=i + 1,
                points=10
            )

            # Submit answers
            WeeklyTestAnswer.objects.create(
                question=question,
                user=self.user,
                user_answer='A'
            )

    def test_complete_test(self):
        """Test completing a test."""
        response = self.client.post('/api/exams/complete/', {
            'test_id': self.test.id
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['correct_answers'], 2)
        self.assertEqual(response.data['total_questions'], 2)
        self.assertEqual(response.data['score_percentage'], 100.0)

        # Check test status updated
        self.test.refresh_from_db()
        self.assertEqual(self.test.status, 'completed')
        self.assertIsNotNone(self.test.completed_at)

    def test_complete_test_not_in_progress(self):
        """Test completing test not in progress."""
        self.test.status = 'pending'
        self.test.save()

        response = self.client.post('/api/exams/complete/', {
            'test_id': self.test.id
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestResultsViewTest(TestCase):
    """Test test_results endpoint."""

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
            title='Test',
            content='Test body',
            author=self.user,
            category=self.category
        )

        self.test = WeeklyTest.objects.create(
            user=self.user,
            status='completed',
            total_questions=1,
            correct_answers=1,
            score_percentage=100.0
        )

        self.question = WeeklyTestQuestion.objects.create(
            weekly_test=self.test,
            content=self.content,
            question_text='Test question',
            correct_answer='A',
            order=1
        )

        self.answer = WeeklyTestAnswer.objects.create(
            question=self.question,
            user=self.user,
            user_answer='A'
        )

    def test_get_test_results(self):
        """Test retrieving test results."""
        response = self.client.get(f'/api/exams/{self.test.id}/results/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('test', response.data)
        self.assertIn('answers', response.data)
        self.assertEqual(response.data['test']['score_percentage'], 100.0)

    def test_get_test_results_not_owner(self):
        """Test retrieving results for another user's test."""
        user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user2)

        response = self.client.get(f'/api/exams/{self.test.id}/results/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
