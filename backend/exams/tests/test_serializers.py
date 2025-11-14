"""
Tests for exams serializers.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from rest_framework import serializers as drf_serializers
from datetime import date, timedelta

from exams.models import WeeklyTest, WeeklyTestQuestion, WeeklyTestAnswer
from exams.serializers import (
    WeeklyTestQuestionSerializer,
    WeeklyTestAnswerSerializer,
    WeeklyTestSerializer,
    WeeklyTestListSerializer,
    SubmitAnswerSerializer,
    StartTestSerializer,
    CompleteTestSerializer
)
from content.models import Content, Category

User = get_user_model()


class WeeklyTestQuestionSerializerTest(TestCase):
    """Test WeeklyTestQuestionSerializer."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='Test body',
            author=self.user,
            category=self.category
        )
        self.weekly_test = WeeklyTest.objects.create(user=self.user)
        self.question = WeeklyTestQuestion.objects.create(
            weekly_test=self.weekly_test,
            content=self.content,
            question_text='Test question',
            correct_answer='A',
            order=1
        )

    def test_serialize_question(self):
        """Test serializing a question."""
        serializer = WeeklyTestQuestionSerializer(self.question)
        data = serializer.data

        self.assertEqual(data['question_text'], 'Test question')
        self.assertEqual(data['correct_answer'], 'A')
        self.assertEqual(data['order'], 1)
        self.assertIsNotNone(data['content'])  # Nested content
        self.assertEqual(data['content']['title'], 'Test Content')

    def test_read_only_fields(self):
        """Test read-only fields."""
        # id and created_at should be read-only
        self.assertIn('id', WeeklyTestQuestionSerializer.Meta.read_only_fields)
        self.assertIn('created_at', WeeklyTestQuestionSerializer.Meta.read_only_fields)


class WeeklyTestAnswerSerializerTest(TestCase):
    """Test WeeklyTestAnswerSerializer."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='Test body',
            author=self.user,
            category=self.category
        )
        self.weekly_test = WeeklyTest.objects.create(user=self.user)
        self.question = WeeklyTestQuestion.objects.create(
            weekly_test=self.weekly_test,
            content=self.content,
            question_text='Test question',
            correct_answer='A',
            order=1,
            points=10
        )
        self.answer = WeeklyTestAnswer.objects.create(
            question=self.question,
            user=self.user,
            user_answer='A'
        )

    def test_serialize_answer(self):
        """Test serializing an answer."""
        serializer = WeeklyTestAnswerSerializer(self.answer)
        data = serializer.data

        self.assertEqual(data['user_answer'], 'A')
        self.assertTrue(data['is_correct'])
        self.assertEqual(data['points_earned'], 10)
        self.assertIsNotNone(data['question'])  # Nested question

    def test_read_only_fields(self):
        """Test read-only fields."""
        read_only = WeeklyTestAnswerSerializer.Meta.read_only_fields
        self.assertIn('id', read_only)
        self.assertIn('is_correct', read_only)
        self.assertIn('points_earned', read_only)
        self.assertIn('ai_score', read_only)
        self.assertIn('ai_feedback', read_only)
        self.assertIn('answered_at', read_only)


class WeeklyTestSerializerTest(TestCase):
    """Test WeeklyTestSerializer."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
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

    def test_serialize_weekly_test(self):
        """Test serializing a weekly test."""
        test = WeeklyTest.objects.create(
            user=self.user,
            title='Test Week',
            status='pending'
        )

        serializer = WeeklyTestSerializer(test)
        data = serializer.data

        self.assertEqual(data['title'], 'Test Week')
        self.assertEqual(data['status'], 'pending')

    def test_validate_content_ids_duplicate(self):
        """Test duplicate content IDs validation."""
        request = self.factory.post('/')
        request.user = self.user

        # Use 7+ IDs with a duplicate
        content_ids = [c.id for c in self.contents[:6]] + [self.contents[0].id]  # Duplicate first

        serializer = WeeklyTestSerializer(
            data={
                'title': 'Test',
                'content_ids': content_ids
            },
            context={'request': request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('content_ids', serializer.errors)
        self.assertIn('중복', str(serializer.errors['content_ids']))

    def test_validate_content_ids_not_owner(self):
        """Test content ownership validation."""
        # Create content owned by user2
        content_other = Content.objects.create(
            title='Other User Content',
            content='x' * 300,
            author=self.user2,
            is_ai_validated=True
        )

        request = self.factory.post('/')
        request.user = self.user

        # Use 6 valid + 1 invalid (total 7)
        content_ids = [c.id for c in self.contents[:6]] + [content_other.id]

        serializer = WeeklyTestSerializer(
            data={
                'title': 'Test',
                'content_ids': content_ids
            },
            context={'request': request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('content_ids', serializer.errors)
        self.assertIn('유효하지 않은', str(serializer.errors['content_ids']))

    def test_validate_content_ids_not_ai_validated(self):
        """Test AI validation requirement."""
        # Create non-validated content
        not_validated = Content.objects.create(
            title='Not Validated',
            content='x' * 300,
            author=self.user,
            is_ai_validated=False
        )

        request = self.factory.post('/')
        request.user = self.user

        # Use 6 validated + 1 not validated (total 7)
        content_ids = [c.id for c in self.contents[:6]] + [not_validated.id]

        serializer = WeeklyTestSerializer(
            data={
                'title': 'Test',
                'content_ids': content_ids
            },
            context={'request': request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('content_ids', serializer.errors)
        self.assertIn('AI 검증', str(serializer.errors['content_ids']))

    def test_validate_content_ids_empty_allowed(self):
        """Test omitting content_ids for auto-balancing mode."""
        request = self.factory.post('/')
        request.user = self.user

        # Omit content_ids entirely (required=False)
        serializer = WeeklyTestSerializer(
            data={
                'title': 'Auto Balanced Test'
            },
            context={'request': request}
        )

        self.assertTrue(serializer.is_valid())

    def test_validate_content_ids_valid(self):
        """Test valid content_ids."""
        request = self.factory.post('/')
        request.user = self.user

        content_ids = [c.id for c in self.contents[:7]]

        serializer = WeeklyTestSerializer(
            data={
                'title': 'Valid Test',
                'content_ids': content_ids
            },
            context={'request': request}
        )

        self.assertTrue(serializer.is_valid())

    def test_create_saves_content_ids(self):
        """Test create method saves content_ids."""
        request = self.factory.post('/')
        request.user = self.user

        content_ids = [c.id for c in self.contents[:7]]

        serializer = WeeklyTestSerializer(
            data={
                'title': 'Test',
                'content_ids': content_ids
            },
            context={'request': request}
        )

        self.assertTrue(serializer.is_valid())
        test = serializer.save()

        # Check that content_ids are stored temporarily
        self.assertEqual(test._selected_content_ids, content_ids)

    def test_read_only_fields(self):
        """Test read-only fields."""
        read_only = WeeklyTestSerializer.Meta.read_only_fields
        self.assertIn('id', read_only)
        self.assertIn('total_questions', read_only)
        self.assertIn('correct_answers', read_only)
        self.assertIn('score_percentage', read_only)
        self.assertIn('started_at', read_only)
        self.assertIn('completed_at', read_only)


class WeeklyTestListSerializerTest(TestCase):
    """Test WeeklyTestListSerializer."""

    def test_simplified_fields(self):
        """Test list serializer has simplified fields."""
        fields = WeeklyTestListSerializer.Meta.fields

        # Should have these
        self.assertIn('id', fields)
        self.assertIn('title', fields)
        self.assertIn('status', fields)

        # Should NOT have these (compared to full serializer)
        self.assertNotIn('questions', fields)
        self.assertNotIn('user_answers', fields)
        self.assertNotIn('content_ids', fields)


class SubmitAnswerSerializerTest(TestCase):
    """Test SubmitAnswerSerializer."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test', user=self.user)
        self.content = Content.objects.create(
            title='Test',
            content='Test body',
            author=self.user,
            category=self.category
        )
        self.weekly_test = WeeklyTest.objects.create(user=self.user)
        self.question = WeeklyTestQuestion.objects.create(
            weekly_test=self.weekly_test,
            content=self.content,
            question_text='Test',
            correct_answer='A',
            order=1
        )

    def test_validate_question_not_exists(self):
        """Test validation with non-existent question."""
        request = self.factory.post('/')
        request.user = self.user

        serializer = SubmitAnswerSerializer(
            data={
                'question_id': 99999,
                'user_answer': 'A'
            },
            context={'request': request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('question_id', serializer.errors)
        self.assertIn('존재하지 않는', str(serializer.errors['question_id']))

    def test_validate_question_not_owner(self):
        """Test validation with question from another user's test."""
        request = self.factory.post('/')
        request.user = self.user2

        serializer = SubmitAnswerSerializer(
            data={
                'question_id': self.question.id,
                'user_answer': 'A'
            },
            context={'request': request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('question_id', serializer.errors)
        self.assertIn('권한', str(serializer.errors['question_id']))

    def test_validate_question_valid(self):
        """Test validation with valid question."""
        request = self.factory.post('/')
        request.user = self.user

        serializer = SubmitAnswerSerializer(
            data={
                'question_id': self.question.id,
                'user_answer': 'A'
            },
            context={'request': request}
        )

        self.assertTrue(serializer.is_valid())


class StartTestSerializerTest(TestCase):
    """Test StartTestSerializer."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        self.test = WeeklyTest.objects.create(
            user=self.user,
            status='pending'
        )

    def test_validate_test_not_exists(self):
        """Test validation with non-existent test."""
        request = self.factory.post('/')
        request.user = self.user

        serializer = StartTestSerializer(
            data={'test_id': 99999},
            context={'request': request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('test_id', serializer.errors)
        self.assertIn('존재하지 않는', str(serializer.errors['test_id']))

    def test_validate_test_not_owner(self):
        """Test validation with another user's test."""
        request = self.factory.post('/')
        request.user = self.user2

        serializer = StartTestSerializer(
            data={'test_id': self.test.id},
            context={'request': request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('test_id', serializer.errors)
        self.assertIn('권한', str(serializer.errors['test_id']))

    def test_validate_test_completed(self):
        """Test validation with completed test."""
        self.test.status = 'completed'
        self.test.save()

        request = self.factory.post('/')
        request.user = self.user

        serializer = StartTestSerializer(
            data={'test_id': self.test.id},
            context={'request': request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('test_id', serializer.errors)
        self.assertIn('완료', str(serializer.errors['test_id']))

    def test_validate_test_pending(self):
        """Test validation with pending test (valid)."""
        request = self.factory.post('/')
        request.user = self.user

        serializer = StartTestSerializer(
            data={'test_id': self.test.id},
            context={'request': request}
        )

        self.assertTrue(serializer.is_valid())

    def test_validate_test_in_progress(self):
        """Test validation with in_progress test (valid - continue feature)."""
        self.test.status = 'in_progress'
        self.test.save()

        request = self.factory.post('/')
        request.user = self.user

        serializer = StartTestSerializer(
            data={'test_id': self.test.id},
            context={'request': request}
        )

        self.assertTrue(serializer.is_valid())


class CompleteTestSerializerTest(TestCase):
    """Test CompleteTestSerializer."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        self.test = WeeklyTest.objects.create(
            user=self.user,
            status='in_progress'
        )

    def test_validate_test_not_exists(self):
        """Test validation with non-existent test."""
        request = self.factory.post('/')
        request.user = self.user

        serializer = CompleteTestSerializer(
            data={'test_id': 99999},
            context={'request': request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('test_id', serializer.errors)
        self.assertIn('존재하지 않는', str(serializer.errors['test_id']))

    def test_validate_test_not_owner(self):
        """Test validation with another user's test."""
        request = self.factory.post('/')
        request.user = self.user2

        serializer = CompleteTestSerializer(
            data={'test_id': self.test.id},
            context={'request': request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('test_id', serializer.errors)
        self.assertIn('권한', str(serializer.errors['test_id']))

    def test_validate_test_not_in_progress(self):
        """Test validation with non-in-progress test."""
        self.test.status = 'pending'
        self.test.save()

        request = self.factory.post('/')
        request.user = self.user

        serializer = CompleteTestSerializer(
            data={'test_id': self.test.id},
            context={'request': request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('test_id', serializer.errors)
        self.assertIn('진행 중인', str(serializer.errors['test_id']))

    def test_validate_test_valid(self):
        """Test validation with in-progress test (valid)."""
        request = self.factory.post('/')
        request.user = self.user

        serializer = CompleteTestSerializer(
            data={'test_id': self.test.id},
            context={'request': request}
        )

        self.assertTrue(serializer.is_valid())
