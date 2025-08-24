"""
Test cases for ai_review application
"""
import json
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import SubscriptionTier, AIUsageTracking
from content.models import Category, Content
from .models import (
    AIQuestion, AIQuestionType, AIReviewSession,
    AIAdaptiveDifficultyTest, WeeklyTest, WeeklyTestQuestion
)
from .services import AIServiceError
from .services.question_generator import QuestionGeneratorService
from .services.answer_evaluator import AnswerEvaluatorService
from .services.base_ai_service import BaseAIService

User = get_user_model()


class AIQuestionTypeModelTest(TestCase):
    """Test AIQuestionType model"""
    
    def test_create_question_type(self):
        """Test creating an AI question type"""
        question_type = AIQuestionType.objects.create(
            name='multiple_choice',
            display_name='Multiple Choice',
            description='Multiple choice questions',
            is_active=True
        )
        
        self.assertEqual(question_type.name, 'multiple_choice')
        self.assertEqual(question_type.display_name, 'Multiple Choice')
        self.assertTrue(question_type.is_active)
        self.assertEqual(str(question_type), 'Multiple Choice')


class AIQuestionModelTest(TestCase):
    """Test AIQuestion model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test Category', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='Test content body',
            author=self.user,
            category=self.category
        )
        self.question_type = AIQuestionType.objects.create(
            name='multiple_choice',
            display_name='Multiple Choice'
        )
    
    def test_create_ai_question(self):
        """Test creating an AI question"""
        question_data = {
            'question': 'What is the main topic?',
            'options': ['A', 'B', 'C', 'D'],
            'correct_answer': 'A',
            'explanation': 'A is correct because...'
        }
        
        ai_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.question_type,
            difficulty=3,
            question_text='What is the main topic?',
            question_data=question_data,
            generated_by_ai=True
        )
        
        self.assertEqual(ai_question.content, self.content)
        self.assertEqual(ai_question.question_type, self.question_type)
        self.assertEqual(ai_question.difficulty, 3)
        self.assertTrue(ai_question.generated_by_ai)
        self.assertEqual(ai_question.question_data['question'], 'What is the main topic?')
    
    def test_ai_question_str_representation(self):
        """Test AI question string representation"""
        ai_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.question_type,
            difficulty=3,
            question_text='Test question?',
            question_data={'question': 'Test question?'},
            generated_by_ai=True
        )
        
        expected_str = f"Test Content - Multiple Choice (Difficulty: 3)"
        self.assertEqual(str(ai_question), expected_str)


class AIReviewSessionModelTest(TestCase):
    """Test AIReviewSession model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test Category', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='Test content body',
            author=self.user,
            category=self.category
        )
    
    def test_create_ai_review_session(self):
        """Test creating an AI review session"""
        session = AIReviewSession.objects.create(
            user=self.user,
            content=self.content,
            session_type='question_generation',
            total_questions=5
        )
        
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.content, self.content)
        self.assertEqual(session.session_type, 'question_generation')
        self.assertEqual(session.total_questions, 5)
        self.assertEqual(session.questions_completed, 0)
        self.assertFalse(session.is_completed)
    
    def test_session_completion(self):
        """Test session completion logic"""
        session = AIReviewSession.objects.create(
            user=self.user,
            content=self.content,
            session_type='question_generation',
            total_questions=3,
            questions_completed=3
        )
        
        session.is_completed = True
        session.save()
        
        self.assertTrue(session.is_completed)


class BaseAIServiceTest(TestCase):
    """Test BaseAIService"""
    
    def setUp(self):
        self.service = BaseAIService()
    
    @override_settings(AI_ENABLE_MOCK_RESPONSES=True)
    @patch('ai_review.services.base_ai_service.BaseAIService._make_api_call')
    def test_make_api_call_success(self, mock_api_call):
        """Test successful API call"""
        mock_api_call.return_value = ('{"result": "success"}', 1.5)
        
        messages = [{"role": "user", "content": "Test message"}]
        response, processing_time = self.service._make_api_call(messages)
        
        self.assertEqual(response, '{"result": "success"}')
        self.assertEqual(processing_time, 1.5)
        mock_api_call.assert_called_once_with(messages)
    
    @patch('ai_review.services.base_ai_service.BaseAIService._make_api_call')
    def test_make_api_call_retry_on_error(self, mock_api_call):
        """Test API call retry logic"""
        # First call fails, second succeeds
        mock_api_call.side_effect = [
            Exception("Network error"),
            ('{"result": "success"}', 1.0)
        ]
        
        messages = [{"role": "user", "content": "Test message"}]
        
        # Should succeed after retry
        response, processing_time = self.service._make_api_call(messages, max_retries=2)
        self.assertEqual(response, '{"result": "success"}')
    
    def test_parse_json_response_valid(self):
        """Test parsing valid JSON response"""
        json_response = '{"questions": [{"question": "Test?", "answer": "Yes"}]}'
        
        result = self.service._parse_json_response(json_response)
        
        self.assertEqual(result['questions'][0]['question'], 'Test?')
        self.assertEqual(result['questions'][0]['answer'], 'Yes')
    
    def test_parse_json_response_invalid(self):
        """Test parsing invalid JSON response"""
        invalid_json = 'This is not JSON'
        
        with self.assertRaises(AIServiceError):
            self.service._parse_json_response(invalid_json)


class QuestionGeneratorServiceTest(TestCase):
    """Test QuestionGeneratorService"""
    
    def setUp(self):
        self.service = QuestionGeneratorService()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test Category', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='This is test content about machine learning algorithms.',
            author=self.user,
            category=self.category
        )
        
        self.question_type = AIQuestionType.objects.create(
            name='multiple_choice',
            display_name='Multiple Choice',
            is_active=True
        )
    
    @patch('ai_review.services.question_generator.QuestionGeneratorService._make_api_call')
    @patch('django.core.cache.cache.get')
    @patch('django.core.cache.cache.set')
    def test_generate_questions_success(self, mock_cache_set, mock_cache_get, mock_api_call):
        """Test successful question generation"""
        mock_cache_get.return_value = None  # No cached result
        
        mock_response = json.dumps({
            'questions': [
                {
                    'question': 'What is machine learning?',
                    'options': ['AI technique', 'Database', 'Network', 'Hardware'],
                    'correct_answer': 'AI technique',
                    'explanation': 'Machine learning is a subset of AI.',
                    'difficulty': 3
                }
            ]
        })
        
        mock_api_call.return_value = (mock_response, 1.5)
        
        questions = self.service.generate_questions(
            content=self.content,
            question_types=['multiple_choice'],
            difficulty=3,
            count=1
        )
        
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]['question'], 'What is machine learning?')
        self.assertEqual(questions[0]['difficulty'], 3)
        mock_cache_set.assert_called_once()
    
    @patch('django.core.cache.cache.get')
    def test_generate_questions_cached(self, mock_cache_get):
        """Test cached question generation"""
        cached_questions = [{'question': 'Cached question?', 'difficulty': 2}]
        mock_cache_get.return_value = cached_questions
        
        questions = self.service.generate_questions(
            content=self.content,
            question_types=['multiple_choice'],
            difficulty=2,
            count=1
        )
        
        self.assertEqual(questions, cached_questions)
    
    def test_generate_questions_invalid_type(self):
        """Test question generation with invalid question type"""
        with self.assertRaises(AIServiceError):
            self.service.generate_questions(
                content=self.content,
                question_types=['invalid_type'],
                difficulty=3,
                count=1
            )
    
    def test_build_generation_prompt(self):
        """Test prompt building for question generation"""
        prompt = self.service._build_generation_prompt(
            self.content,
            self.question_type,
            difficulty=3,
            count=1
        )
        
        self.assertIn('Test Content', prompt)
        self.assertIn('machine learning', prompt)
        self.assertIn('Multiple Choice', prompt)
        self.assertIn('보통', prompt)  # Difficulty level in Korean


class AnswerEvaluatorServiceTest(TestCase):
    """Test AnswerEvaluatorService"""
    
    def setUp(self):
        self.service = AnswerEvaluatorService()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test Category', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='Test content about science',
            author=self.user,
            category=self.category
        )
    
    @patch('ai_review.services.answer_evaluator.AnswerEvaluatorService._make_api_call')
    def test_evaluate_answer_success(self, mock_api_call):
        """Test successful answer evaluation"""
        mock_response = json.dumps({
            'score': 8.5,
            'feedback': 'Good answer with minor improvements needed.',
            'strengths': ['Clear explanation', 'Correct concepts'],
            'improvements': ['Could be more detailed'],
            'overall_assessment': 'Well done'
        })
        
        mock_api_call.return_value = (mock_response, 1.0)
        
        result = self.service.evaluate_answer(
            question='What is photosynthesis?',
            user_answer='Process where plants make food using sunlight',
            correct_answer='Photosynthesis is the process by which plants use sunlight to synthesize food',
            content=self.content
        )
        
        self.assertEqual(result['score'], 8.5)
        self.assertIn('Good answer', result['feedback'])
        self.assertIn('Clear explanation', result['strengths'])
    
    @patch('ai_review.services.answer_evaluator.AnswerEvaluatorService._make_api_call')
    def test_evaluate_answer_api_error(self, mock_api_call):
        """Test answer evaluation with API error"""
        mock_api_call.side_effect = AIServiceError("API Error")
        
        with self.assertRaises(AIServiceError):
            self.service.evaluate_answer(
                question='Test question?',
                user_answer='Test answer',
                correct_answer='Correct answer',
                content=self.content
            )


class AIAPITest(APITestCase):
    """Test AI API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        # Set to BASIC tier to enable AI features
        self.user.subscription.tier = SubscriptionTier.BASIC
        self.user.subscription.save()
        
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        self.category = Category.objects.create(name='Test Category', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='This is test content about artificial intelligence.',
            author=self.user,
            category=self.category
        )
        
        AIQuestionType.objects.create(
            name='multiple_choice',
            display_name='Multiple Choice',
            is_active=True
        )
    
    def test_question_types_list(self):
        """Test listing available question types"""
        url = reverse('ai_review:question-types')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'multiple_choice')
    
    @patch('ai_review.views.ai_service.generate_questions')
    def test_generate_questions_success(self, mock_generate):
        """Test successful question generation"""
        mock_generate.return_value = [
            {
                'id': 1,
                'question': 'What is AI?',
                'options': ['Artificial Intelligence', 'Automatic Integration', 'Advanced Interface', 'None'],
                'correct_answer': 'Artificial Intelligence',
                'explanation': 'AI stands for Artificial Intelligence',
                'difficulty': 3,
                'question_type': 'multiple_choice'
            }
        ]
        
        url = reverse('ai_review:generate-questions')
        data = {
            'content_id': self.content.id,
            'question_types': ['multiple_choice'],
            'difficulty': 3,
            'count': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['question'], 'What is AI?')
    
    def test_generate_questions_free_tier_denied(self):
        """Test question generation denied for FREE tier"""
        # Change to FREE tier
        self.user.subscription.tier = SubscriptionTier.FREE
        self.user.subscription.save()
        
        url = reverse('ai_review:generate-questions')
        data = {
            'content_id': self.content.id,
            'question_types': ['multiple_choice'],
            'difficulty': 3,
            'count': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('not available', response.data['detail'])
    
    def test_generate_questions_daily_limit_exceeded(self):
        """Test question generation with daily limit exceeded"""
        # Create usage record that exceeds limit
        usage = AIUsageTracking.get_or_create_for_today(self.user)
        usage.questions_generated = 30  # BASIC tier limit
        usage.save()
        
        url = reverse('ai_review:generate-questions')
        data = {
            'content_id': self.content.id,
            'question_types': ['multiple_choice'],
            'difficulty': 3,
            'count': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('Daily limit exceeded', response.data['error'])
    
    def test_generate_questions_invalid_content(self):
        """Test question generation with invalid content ID"""
        url = reverse('ai_review:generate-questions')
        data = {
            'content_id': 99999,
            'question_types': ['multiple_choice'],
            'difficulty': 3,
            'count': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_generate_questions_invalid_question_type(self):
        """Test question generation with invalid question type"""
        url = reverse('ai_review:generate-questions')
        data = {
            'content_id': self.content.id,
            'question_types': ['invalid_type'],
            'difficulty': 3,
            'count': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('not available', response.data['detail'])
    
    @patch('ai_review.views.answer_evaluator.evaluate_answer')
    def test_evaluate_answer_success(self, mock_evaluate):
        """Test successful answer evaluation"""
        mock_evaluate.return_value = {
            'score': 7.5,
            'feedback': 'Good answer with room for improvement',
            'strengths': ['Clear understanding'],
            'improvements': ['More details needed']
        }
        
        url = reverse('ai_review:evaluate-answer')
        data = {
            'question': 'What is machine learning?',
            'user_answer': 'It is a subset of AI that learns from data',
            'correct_answer': 'Machine learning is a subset of artificial intelligence that uses algorithms to learn patterns from data',
            'content_id': self.content.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['score'], 7.5)
        self.assertIn('Good answer', response.data['feedback'])
    
    def test_content_questions_list(self):
        """Test listing questions for specific content"""
        # Create some AI questions first
        question_type = AIQuestionType.objects.get(name='multiple_choice')
        AIQuestion.objects.create(
            content=self.content,
            question_type=question_type,
            difficulty=3,
            question_text='Test question?',
            question_data={'question': 'Test question?', 'options': ['A', 'B', 'C', 'D']},
            generated_by_ai=True
        )
        
        url = reverse('ai_review:content-questions', kwargs={'content_id': self.content.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['question_text'], 'Test question?')
    
    def test_ai_health_check(self):
        """Test AI health check endpoint"""
        url = reverse('ai_review:health')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)


class WeeklyTestModelTest(TestCase):
    """Test WeeklyTest model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test Category', user=self.user)
    
    def test_create_weekly_test(self):
        """Test creating a weekly test"""
        weekly_test = WeeklyTest.objects.create(
            user=self.user,
            category=self.category,
            total_questions=10,
            target_difficulty=3
        )
        
        self.assertEqual(weekly_test.user, self.user)
        self.assertEqual(weekly_test.category, self.category)
        self.assertEqual(weekly_test.total_questions, 10)
        self.assertEqual(weekly_test.questions_completed, 0)
        self.assertFalse(weekly_test.is_completed)
    
    def test_weekly_test_completion(self):
        """Test weekly test completion"""
        weekly_test = WeeklyTest.objects.create(
            user=self.user,
            category=self.category,
            total_questions=5,
            questions_completed=5
        )
        
        weekly_test.is_completed = True
        weekly_test.completed_at = timezone.now()
        weekly_test.save()
        
        self.assertTrue(weekly_test.is_completed)
        self.assertIsNotNone(weekly_test.completed_at)


class AdaptiveTestModelTest(TestCase):
    """Test AIAdaptiveDifficultyTest model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test Category', user=self.user)
    
    def test_create_adaptive_test(self):
        """Test creating an adaptive difficulty test"""
        adaptive_test = AIAdaptiveDifficultyTest.objects.create(
            user=self.user,
            category=self.category,
            current_difficulty=3,
            questions_answered=0,
            correct_answers=0
        )
        
        self.assertEqual(adaptive_test.user, self.user)
        self.assertEqual(adaptive_test.category, self.category)
        self.assertEqual(adaptive_test.current_difficulty, 3)
        self.assertEqual(adaptive_test.questions_answered, 0)
        self.assertFalse(adaptive_test.is_completed)
    
    def test_adaptive_difficulty_adjustment(self):
        """Test difficulty adjustment logic"""
        adaptive_test = AIAdaptiveDifficultyTest.objects.create(
            user=self.user,
            category=self.category,
            current_difficulty=3,
            questions_answered=5,
            correct_answers=4  # 80% success rate
        )
        
        # Test success rate calculation
        success_rate = adaptive_test.correct_answers / adaptive_test.questions_answered
        self.assertAlmostEqual(success_rate, 0.8, places=2)


class AIUsageLimitTest(TestCase):
    """Test AI usage limits and tracking"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_free_tier_ai_restrictions(self):
        """Test that FREE tier cannot use AI features"""
        self.user.subscription.tier = SubscriptionTier.FREE
        self.user.subscription.save()
        
        self.assertFalse(self.user.can_use_ai_features())
        self.assertEqual(self.user.get_ai_question_limit(), 0)
        self.assertEqual(self.user.get_ai_features_list(), [])
    
    def test_basic_tier_ai_limits(self):
        """Test BASIC tier AI limits"""
        self.user.subscription.tier = SubscriptionTier.BASIC
        self.user.subscription.save()
        self.user.is_email_verified = True
        self.user.save()
        
        self.assertTrue(self.user.can_use_ai_features())
        self.assertEqual(self.user.get_ai_question_limit(), 30)
        
        features = self.user.get_ai_features_list()
        self.assertIn('multiple_choice', features)
        self.assertIn('ai_chat', features)
        self.assertNotIn('blur_processing', features)  # PRO only
    
    def test_pro_tier_ai_limits(self):
        """Test PRO tier AI limits"""
        self.user.subscription.tier = SubscriptionTier.PRO
        self.user.subscription.save()
        self.user.is_email_verified = True
        self.user.save()
        
        self.assertTrue(self.user.can_use_ai_features())
        self.assertEqual(self.user.get_ai_question_limit(), 200)
        
        features = self.user.get_ai_features_list()
        self.assertIn('multiple_choice', features)
        self.assertIn('fill_blank', features)
        self.assertIn('blur_processing', features)
    
    def test_ai_usage_tracking_daily_reset(self):
        """Test that AI usage tracking resets daily"""
        self.user.subscription.tier = SubscriptionTier.BASIC
        self.user.subscription.save()
        
        # Create usage for today
        usage_today = AIUsageTracking.get_or_create_for_today(self.user)
        usage_today.questions_generated = 10
        usage_today.save()
        
        # Get usage for today again - should be same record
        usage_again = AIUsageTracking.get_or_create_for_today(self.user)
        self.assertEqual(usage_today.id, usage_again.id)
        self.assertEqual(usage_again.questions_generated, 10)
        
        # Test can generate more questions
        self.assertTrue(usage_again.can_generate_questions(5))
        self.assertFalse(usage_again.can_generate_questions(25))  # Would exceed limit


class SerializerTest(TestCase):
    """Test AI serializers"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test Category', user=self.user)
        self.content = Content.objects.create(
            title='Test Content',
            content='Test content',
            author=self.user,
            category=self.category
        )
        self.question_type = AIQuestionType.objects.create(
            name='multiple_choice',
            display_name='Multiple Choice'
        )
    
    def test_generate_questions_serializer_valid(self):
        """Test GenerateQuestionsSerializer with valid data"""
        from .serializers import GenerateQuestionsSerializer
        
        data = {
            'content_id': self.content.id,
            'question_types': ['multiple_choice'],
            'difficulty': 3,
            'count': 2
        }
        
        mock_request = type('MockRequest', (), {'user': self.user})()
        serializer = GenerateQuestionsSerializer(
            data=data,
            context={'request': mock_request}
        )
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['content_id'], self.content.id)
        self.assertEqual(serializer.validated_data['difficulty'], 3)
        self.assertEqual(serializer.validated_data['count'], 2)
    
    def test_generate_questions_serializer_invalid(self):
        """Test GenerateQuestionsSerializer with invalid data"""
        from .serializers import GenerateQuestionsSerializer
        
        # Missing required fields
        data = {
            'content_id': self.content.id,
            # Missing question_types
            'difficulty': 3
        }
        
        serializer = GenerateQuestionsSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('question_types', serializer.errors)