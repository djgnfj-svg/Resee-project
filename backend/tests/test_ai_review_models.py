"""
Tests for AI Review models
"""
import pytest
from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from content.models import Content, Category
from ai_review.models import AIQuestionType, AIQuestion, AIEvaluation, AIReviewSession
from review.models import ReviewHistory


User = get_user_model()


@pytest.mark.django_db
class TestAIQuestionTypeModel(TestCase):
    
    def test_question_type_choices(self):
        """Test that all question type choices are valid"""
        valid_choices = ['multiple_choice', 'short_answer', 'fill_blank', 'blur_processing']
        
        for choice in valid_choices:
            question_type = AIQuestionType(name=choice, display_name=choice.replace('_', ' ').title())
            question_type.full_clean()  # Should not raise ValidationError
    
    def test_question_type_string_representation(self):
        """Test string representation of question type"""
        question_type = AIQuestionType(name='multiple_choice', display_name='Multiple Choice')
        self.assertEqual(str(question_type), 'Multiple Choice')
    
    def test_question_type_unique_name(self):
        """Test that question type names are unique"""
        AIQuestionType.objects.create(name='multiple_choice', display_name='Multiple Choice')
        
        with self.assertRaises(IntegrityError):
            AIQuestionType.objects.create(name='multiple_choice', display_name='Another MC')


@pytest.mark.django_db
class TestAIQuestionModel(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
        self.content = Content.objects.create(
            title='Test Content',
            content='This is test content for AI questions',
            category=self.category,
            author=self.user
        )
        self.question_type = AIQuestionType.objects.create(
            name='multiple_choice',
            display_name='Multiple Choice'
        )
    
    def test_create_ai_question(self):
        """Test creating an AI question"""
        question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.question_type,
            question_text='What is the main topic of this content?',
            correct_answer='Test content',
            options=['Test content', 'Wrong answer 1', 'Wrong answer 2', 'Wrong answer 3'],
            difficulty=1
        )
        
        self.assertEqual(question.content, self.content)
        self.assertEqual(question.question_type, self.question_type)
        self.assertEqual(question.difficulty, 1)
        self.assertTrue(question.is_active)
        self.assertIsNotNone(question.created_at)
    
    def test_ai_question_string_representation(self):
        """Test string representation of AI question"""
        question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.question_type,
            question_text='What is the main topic?',
            correct_answer='Test',
            difficulty=1
        )
        
        expected = f"{self.content.title} - Multiple Choice"
        self.assertEqual(str(question), expected)
    
    def test_ai_question_difficulty_range(self):
        """Test that difficulty is within valid range"""
        # Create a short answer question type for validation test
        short_answer_type = AIQuestionType.objects.create(
            name='short_answer',
            display_name='Short Answer'
        )
        
        # Valid difficulty
        question = AIQuestion(
            content=self.content,
            question_type=short_answer_type,
            question_text='Test question?',
            correct_answer='Test',
            difficulty=3
        )
        question.full_clean()  # Should not raise ValidationError
        
        # Invalid difficulty (too low)
        question_low = AIQuestion(
            content=self.content,
            question_type=short_answer_type,
            question_text='Test question?',
            correct_answer='Test',
            difficulty=0
        )
        with self.assertRaises(ValidationError):
            question_low.full_clean()
        
        # Invalid difficulty (too high)
        question_high = AIQuestion(
            content=self.content,
            question_type=short_answer_type,
            question_text='Test question?',
            correct_answer='Test',
            difficulty=6
        )
        with self.assertRaises(ValidationError):
            question_high.full_clean()
    
    def test_multiple_choice_options_validation(self):
        """Test that multiple choice questions have valid options"""
        # Valid options (4 choices)
        question = AIQuestion(
            content=self.content,
            question_type=self.question_type,
            question_text='What is correct?',
            correct_answer='Option A',
            options=['Option A', 'Option B', 'Option C', 'Option D'],
            difficulty=1
        )
        question.full_clean()  # Should not raise ValidationError
    
    def test_get_active_questions_for_content(self):
        """Test getting active questions for content"""
        # Create active question
        active_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.question_type,
            question_text='Active question?',
            correct_answer='Yes',
            difficulty=1,
            is_active=True
        )
        
        # Create inactive question
        AIQuestion.objects.create(
            content=self.content,
            question_type=self.question_type,
            question_text='Inactive question?',
            correct_answer='No',
            difficulty=1,
            is_active=False
        )
        
        active_questions = AIQuestion.objects.filter(content=self.content, is_active=True)
        self.assertEqual(active_questions.count(), 1)
        self.assertEqual(active_questions.first(), active_question)


@pytest.mark.django_db
class TestAIEvaluationModel(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
        self.content = Content.objects.create(
            title='Test Content',
            content='Test content',
            category=self.category,
            author=self.user
        )
        self.question_type = AIQuestionType.objects.create(
            name='short_answer',
            display_name='Short Answer'
        )
        self.question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.question_type,
            question_text='What is this?',
            correct_answer='Test content',
            difficulty=1
        )
    
    def test_create_ai_evaluation(self):
        """Test creating an AI evaluation"""
        evaluation = AIEvaluation.objects.create(
            question=self.question,
            user=self.user,
            user_answer='This is test content',
            ai_score=0.85,
            feedback='Very close! The answer captures the main idea.',
            processing_time_ms=1200
        )
        
        self.assertEqual(evaluation.question, self.question)
        self.assertEqual(evaluation.user, self.user)
        self.assertEqual(evaluation.ai_score, 0.85)
        self.assertIsNotNone(evaluation.created_at)
    
    def test_ai_evaluation_string_representation(self):
        """Test string representation of AI evaluation"""
        evaluation = AIEvaluation.objects.create(
            question=self.question,
            user=self.user,
            user_answer='Test answer',
            ai_score=0.9,
            feedback='Excellent!'
        )
        
        expected = f"{self.user.email} - What is this? - 0.9"
        self.assertEqual(str(evaluation), expected)
    
    def test_ai_score_range(self):
        """Test that AI score is within valid range (0.0 to 1.0)"""
        # Valid score
        evaluation = AIEvaluation(
            question=self.question,
            user=self.user,
            user_answer='Test',
            ai_score=0.75,
            feedback='Good'
        )
        evaluation.full_clean()  # Should not raise ValidationError
        
        # Invalid score (too low)
        evaluation_low = AIEvaluation(
            question=self.question,
            user=self.user,
            user_answer='Test',
            ai_score=-0.1,
            feedback='Invalid'
        )
        with self.assertRaises(ValidationError):
            evaluation_low.full_clean()
        
        # Invalid score (too high)
        evaluation_high = AIEvaluation(
            question=self.question,
            user=self.user,
            user_answer='Test',
            ai_score=1.1,
            feedback='Invalid'
        )
        with self.assertRaises(ValidationError):
            evaluation_high.full_clean()
    
    def test_get_user_evaluations(self):
        """Test getting evaluations for a user"""
        # Create evaluations for different users
        evaluation1 = AIEvaluation.objects.create(
            question=self.question,
            user=self.user,
            user_answer='Answer 1',
            ai_score=0.8,
            feedback='Good'
        )
        
        other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123'
        )
        AIEvaluation.objects.create(
            question=self.question,
            user=other_user,
            user_answer='Answer 2',
            ai_score=0.7,
            feedback='Okay'
        )
        
        user_evaluations = AIEvaluation.objects.filter(user=self.user)
        self.assertEqual(user_evaluations.count(), 1)
        self.assertEqual(user_evaluations.first(), evaluation1)


@pytest.mark.django_db
class TestAIReviewSessionModel(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
        self.content = Content.objects.create(
            title='Test Content',
            content='Test content',
            category=self.category,
            author=self.user
        )
        
        # Create ReviewHistory (needed for AIReviewSession)
        self.review_history = ReviewHistory.objects.create(
            user=self.user,
            content=self.content,
            result='remembered'
        )
    
    def test_create_ai_review_session(self):
        """Test creating an AI review session"""
        session = AIReviewSession.objects.create(
            review_history=self.review_history,
            questions_generated=5,
            questions_answered=4,
            average_score=0.82,
            session_duration_seconds=180,
            ai_processing_time_ms=3500
        )
        
        self.assertEqual(session.review_history, self.review_history)
        self.assertEqual(session.questions_generated, 5)
        self.assertEqual(session.questions_answered, 4)
        self.assertEqual(session.average_score, 0.82)
        self.assertIsNotNone(session.created_at)
    
    def test_ai_review_session_string_representation(self):
        """Test string representation of AI review session"""
        session = AIReviewSession.objects.create(
            review_history=self.review_history,
            questions_generated=3,
            questions_answered=3,
            average_score=0.9
        )
        
        expected = f"{self.user.email} - {self.content.title} - AI Session"
        self.assertEqual(str(session), expected)
    
    def test_average_score_range(self):
        """Test that average score is within valid range"""
        # Valid score
        session = AIReviewSession(
            review_history=self.review_history,
            questions_generated=3,
            questions_answered=3,
            average_score=0.85
        )
        session.full_clean()  # Should not raise ValidationError
        
        # Invalid score (too high)
        session_high = AIReviewSession(
            review_history=self.review_history,
            questions_generated=3,
            questions_answered=3,
            average_score=1.5
        )
        with self.assertRaises(ValidationError):
            session_high.full_clean()
    
    def test_completion_percentage_property(self):
        """Test completion percentage calculation"""
        session = AIReviewSession.objects.create(
            review_history=self.review_history,
            questions_generated=10,
            questions_answered=7,
            average_score=0.8
        )
        
        self.assertEqual(session.completion_percentage, 70.0)
    
    def test_completion_percentage_zero_questions(self):
        """Test completion percentage with zero questions"""
        session = AIReviewSession.objects.create(
            review_history=self.review_history,
            questions_generated=0,
            questions_answered=0,
            average_score=0.0
        )
        
        self.assertEqual(session.completion_percentage, 0.0)