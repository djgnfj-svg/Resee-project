"""
Tests for exams models (WeeklyTest, WeeklyTestQuestion, WeeklyTestAnswer).
"""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from content.models import Category, Content
from exams.models import WeeklyTest, WeeklyTestAnswer, WeeklyTestQuestion

User = get_user_model()


class WeeklyTestModelTest(TestCase):
    """Test WeeklyTest model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )

    def test_weekly_test_creation(self):
        """Test basic weekly test creation."""
        today = date.today()
        test = WeeklyTest.objects.create(
            user=self.user,
            title='주간 시험 1',
            description='첫 번째 주간 시험',
            start_date=today,
            end_date=today + timedelta(days=7)
        )
        self.assertEqual(test.user, self.user)
        self.assertEqual(test.title, '주간 시험 1')
        self.assertEqual(test.status, 'pending')  # default

    def test_weekly_test_default_values(self):
        """Test default field values."""
        test = WeeklyTest.objects.create(user=self.user)
        self.assertEqual(test.title, '주간 시험')
        self.assertEqual(test.status, 'pending')
        self.assertEqual(test.total_questions, 0)
        self.assertEqual(test.correct_answers, 0)
        self.assertIsNone(test.score_percentage)

    def test_weekly_test_status_choices(self):
        """Test all status choices."""
        statuses = ['pending', 'preparing', 'in_progress', 'completed']

        for idx, status in enumerate(statuses):
            test = WeeklyTest.objects.create(
                user=self.user,
                status=status,
                start_date=date.today() + timedelta(days=idx * 10),
                end_date=date.today() + timedelta(days=idx * 10 + 7)
            )
            self.assertEqual(test.status, status)

    def test_weekly_test_calculate_score_with_questions(self):
        """Test score calculation with questions."""
        test = WeeklyTest.objects.create(
            user=self.user,
            total_questions=10,
            correct_answers=7
        )

        score = test.calculate_score()

        self.assertEqual(score, 70.0)
        self.assertEqual(test.score_percentage, 70.0)

    def test_weekly_test_calculate_score_zero_questions(self):
        """Test score calculation with zero questions."""
        test = WeeklyTest.objects.create(
            user=self.user,
            total_questions=0,
            correct_answers=0
        )

        score = test.calculate_score()

        self.assertEqual(score, 0)
        self.assertEqual(test.score_percentage, 0)

    def test_weekly_test_str(self):
        """Test string representation."""
        today = date.today()
        test = WeeklyTest.objects.create(
            user=self.user,
            title='Test Title',
            start_date=today,
            end_date=today + timedelta(days=7)
        )
        expected = f"{self.user.email} - Test Title ({today} ~ {today + timedelta(days=7)})"
        self.assertEqual(str(test), expected)

    def test_weekly_test_ordering(self):
        """Test ordering by created_at descending."""
        test1 = WeeklyTest.objects.create(
            user=self.user,
            title='First',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7)
        )
        test2 = WeeklyTest.objects.create(
            user=self.user,
            title='Second',
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=17)
        )

        tests = list(WeeklyTest.objects.all())
        self.assertEqual(tests[0].title, 'Second')  # Most recent first
        self.assertEqual(tests[1].title, 'First')

    def test_weekly_test_unique_together(self):
        """Test unique_together constraint for user, start_date, end_date."""
        today = date.today()
        end = today + timedelta(days=7)

        WeeklyTest.objects.create(
            user=self.user,
            start_date=today,
            end_date=end
        )

        # Same user, same dates should fail
        with self.assertRaises(Exception):  # IntegrityError
            WeeklyTest.objects.create(
                user=self.user,
                start_date=today,
                end_date=end
            )

    def test_weekly_test_different_user_same_dates(self):
        """Test same dates allowed for different users."""
        user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )

        today = date.today()
        end = today + timedelta(days=7)

        test1 = WeeklyTest.objects.create(
            user=self.user,
            start_date=today,
            end_date=end
        )
        test2 = WeeklyTest.objects.create(
            user=user2,
            start_date=today,
            end_date=end
        )

        self.assertNotEqual(test1.user, test2.user)
        self.assertEqual(test1.start_date, test2.start_date)


class WeeklyTestQuestionModelTest(TestCase):
    """Test WeeklyTestQuestion model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
        self.content = Content.objects.create(
            title='Test Content',
            content='Test content body',
            author=self.user,
            category=self.category
        )
        self.weekly_test = WeeklyTest.objects.create(
            user=self.user,
            title='Test Week'
        )

    def test_question_creation(self):
        """Test basic question creation."""
        question = WeeklyTestQuestion.objects.create(
            weekly_test=self.weekly_test,
            content=self.content,
            question_type='multiple_choice',
            question_text='What is Python?',
            choices=['A', 'B', 'C', 'D'],
            correct_answer='A',
            explanation='Explanation here',
            order=1,
            points=10
        )

        self.assertEqual(question.weekly_test, self.weekly_test)
        self.assertEqual(question.content, self.content)
        self.assertEqual(question.question_type, 'multiple_choice')

    def test_question_default_values(self):
        """Test default field values."""
        question = WeeklyTestQuestion.objects.create(
            weekly_test=self.weekly_test,
            content=self.content,
            question_text='Test question',
            correct_answer='A'
        )

        self.assertEqual(question.question_type, 'multiple_choice')
        self.assertEqual(question.order, 1)
        self.assertEqual(question.points, 1)

    def test_question_types(self):
        """Test all question types."""
        types = ['multiple_choice', 'true_false']

        for idx, qtype in enumerate(types):
            question = WeeklyTestQuestion.objects.create(
                weekly_test=self.weekly_test,
                content=self.content,
                question_type=qtype,
                question_text=f'Question {idx}',
                correct_answer='A',
                order=idx + 1
            )
            self.assertEqual(question.question_type, qtype)

    def test_question_json_choices(self):
        """Test JSON field for choices."""
        choices = ['Option A', 'Option B', 'Option C', 'Option D']
        question = WeeklyTestQuestion.objects.create(
            weekly_test=self.weekly_test,
            content=self.content,
            question_text='Test',
            choices=choices,
            correct_answer='Option A'
        )

        question.refresh_from_db()
        self.assertEqual(question.choices, choices)
        self.assertIsInstance(question.choices, list)

    def test_question_str(self):
        """Test string representation."""
        question = WeeklyTestQuestion.objects.create(
            weekly_test=self.weekly_test,
            content=self.content,
            question_text='This is a very long question text that should be truncated',
            correct_answer='A',
            order=5
        )

        expected = f"{self.weekly_test.title} - Q5: This is a very long question text that should be t"
        self.assertEqual(str(question), expected)

    def test_question_ordering(self):
        """Test ordering by order field."""
        q1 = WeeklyTestQuestion.objects.create(
            weekly_test=self.weekly_test,
            content=self.content,
            question_text='Q1',
            correct_answer='A',
            order=3
        )
        q2 = WeeklyTestQuestion.objects.create(
            weekly_test=self.weekly_test,
            content=self.content,
            question_text='Q2',
            correct_answer='B',
            order=1
        )
        q3 = WeeklyTestQuestion.objects.create(
            weekly_test=self.weekly_test,
            content=self.content,
            question_text='Q3',
            correct_answer='C',
            order=2
        )

        questions = list(WeeklyTestQuestion.objects.all())
        self.assertEqual(questions[0].order, 1)
        self.assertEqual(questions[1].order, 2)
        self.assertEqual(questions[2].order, 3)

    def test_question_unique_together(self):
        """Test unique_together constraint for weekly_test and order."""
        WeeklyTestQuestion.objects.create(
            weekly_test=self.weekly_test,
            content=self.content,
            question_text='Q1',
            correct_answer='A',
            order=1
        )

        # Same test, same order should fail
        with self.assertRaises(Exception):  # IntegrityError
            WeeklyTestQuestion.objects.create(
                weekly_test=self.weekly_test,
                content=self.content,
                question_text='Q2',
                correct_answer='B',
                order=1
            )


class WeeklyTestAnswerModelTest(TestCase):
    """Test WeeklyTestAnswer model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
        self.content = Content.objects.create(
            title='Test Content',
            content='Test content body',
            author=self.user,
            category=self.category
        )
        self.weekly_test = WeeklyTest.objects.create(
            user=self.user,
            title='Test Week'
        )
        self.question = WeeklyTestQuestion.objects.create(
            weekly_test=self.weekly_test,
            content=self.content,
            question_text='What is 2+2?',
            correct_answer='4',
            order=1,
            points=10
        )

    def test_answer_creation(self):
        """Test basic answer creation."""
        answer = WeeklyTestAnswer.objects.create(
            question=self.question,
            user=self.user,
            user_answer='4'
        )

        self.assertEqual(answer.question, self.question)
        self.assertEqual(answer.user, self.user)
        self.assertEqual(answer.user_answer, '4')

    def test_answer_auto_grading_correct(self):
        """Test automatic grading for correct answer."""
        answer = WeeklyTestAnswer.objects.create(
            question=self.question,
            user=self.user,
            user_answer='4'
        )

        self.assertTrue(answer.is_correct)
        self.assertEqual(answer.points_earned, 10)

    def test_answer_auto_grading_incorrect(self):
        """Test automatic grading for incorrect answer."""
        answer = WeeklyTestAnswer.objects.create(
            question=self.question,
            user=self.user,
            user_answer='5'
        )

        self.assertFalse(answer.is_correct)
        self.assertEqual(answer.points_earned, 0)

    def test_answer_case_insensitive_comparison(self):
        """Test case-insensitive answer comparison."""
        self.question.correct_answer = 'Python'
        self.question.save()

        answer1 = WeeklyTestAnswer.objects.create(
            question=self.question,
            user=self.user,
            user_answer='python'
        )
        self.assertTrue(answer1.is_correct)

        # Create another user for second answer
        user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )
        answer2 = WeeklyTestAnswer.objects.create(
            question=self.question,
            user=user2,
            user_answer='PYTHON'
        )
        self.assertTrue(answer2.is_correct)

    def test_answer_whitespace_trimming(self):
        """Test whitespace trimming in answer comparison."""
        answer = WeeklyTestAnswer.objects.create(
            question=self.question,
            user=self.user,
            user_answer='  4  '
        )

        self.assertTrue(answer.is_correct)
        self.assertEqual(answer.points_earned, 10)

    def test_answer_str(self):
        """Test string representation."""
        answer = WeeklyTestAnswer.objects.create(
            question=self.question,
            user=self.user,
            user_answer='4'
        )

        expected = f"{self.user.email} - What is 2+2? - ✓"
        self.assertEqual(str(answer), expected)

    def test_answer_str_incorrect(self):
        """Test string representation for incorrect answer."""
        answer = WeeklyTestAnswer.objects.create(
            question=self.question,
            user=self.user,
            user_answer='5'
        )

        expected = f"{self.user.email} - What is 2+2? - ✗"
        self.assertEqual(str(answer), expected)

    def test_answer_unique_together(self):
        """Test unique_together constraint for question and user."""
        WeeklyTestAnswer.objects.create(
            question=self.question,
            user=self.user,
            user_answer='4'
        )

        # Same question, same user should fail
        with self.assertRaises(Exception):  # IntegrityError
            WeeklyTestAnswer.objects.create(
                question=self.question,
                user=self.user,
                user_answer='5'
            )

    def test_answer_ai_fields(self):
        """Test AI evaluation fields."""
        answer = WeeklyTestAnswer.objects.create(
            question=self.question,
            user=self.user,
            user_answer='4',
            ai_score=95.5,
            ai_feedback='Excellent answer'
        )

        answer.refresh_from_db()
        self.assertEqual(answer.ai_score, 95.5)
        self.assertEqual(answer.ai_feedback, 'Excellent answer')
