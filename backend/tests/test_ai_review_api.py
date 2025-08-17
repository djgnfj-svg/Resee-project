"""
Tests for AI Review API endpoints
"""
import json
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from ai_review.models import AIEvaluation, AIQuestion, AIQuestionType
from ai_review.services import AIServiceError
from content.models import Category, Content

User = get_user_model()


class AIReviewAPITestCase(TestCase):
    """Base test case for AI Review API"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123'
        )
        
        # Create test content
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
        self.content = Content.objects.create(
            title='Test Content',
            content='This is test content for AI question generation. It covers key concepts.',
            category=self.category,
            author=self.user
        )
        
        # Get or create test question types (may exist from migration)
        self.mc_type, _ = AIQuestionType.objects.get_or_create(
            name='multiple_choice',
            defaults={
                'display_name': 'Multiple Choice',
                'is_active': True
            }
        )
        self.sa_type, _ = AIQuestionType.objects.get_or_create(
            name='short_answer',
            defaults={
                'display_name': 'Short Answer',
                'is_active': True
            }
        )
        
        # Create test question
        self.question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.mc_type,
            question_text='What is the main topic?',
            correct_answer='AI question generation',
            options=['AI question generation', 'Wrong 1', 'Wrong 2', 'Wrong 3'],
            difficulty=1
        )
        
    def authenticate(self, user=None):
        """Helper method to authenticate user"""
        if user is None:
            user = self.user
        self.client.force_authenticate(user=user)


class TestAIHealthEndpoint(AIReviewAPITestCase):
    """Test AI review health endpoint"""
    
    def test_health_check_authenticated(self):
        """Test health check with authentication"""
        self.authenticate()
        url = reverse('ai_review:health')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')
        self.assertIn('active_question_types', response.data)
        self.assertIn('ai_service_available', response.data)
    
    def test_health_check_unauthenticated(self):
        """Test health check without authentication"""
        url = reverse('ai_review:health')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestAIQuestionTypeListView(AIReviewAPITestCase):
    """Test AI question types listing"""
    
    def test_list_question_types_authenticated(self):
        """Test listing question types with authentication"""
        self.authenticate()
        url = reverse('ai_review:question-types')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # API returns paginated response
        self.assertIn('results', response.data)
        data_list = response.data['results']
        
        self.assertGreaterEqual(len(data_list), 2)  # At least mc_type and sa_type
        
        # Check structure
        if len(data_list) > 0:
            question_type = data_list[0]
            self.assertIn('id', question_type)
            self.assertIn('name', question_type)
            self.assertIn('display_name', question_type)
            self.assertIn('is_active', question_type)
    
    def test_list_question_types_only_active(self):
        """Test that only active question types are returned"""
        # Get initial active count
        initial_count = AIQuestionType.objects.filter(is_active=True).count()
        
        # Create inactive question type
        AIQuestionType.objects.create(
            name='inactive_type',
            display_name='Inactive Type',
            is_active=False
        )
        
        self.authenticate()
        url = reverse('ai_review:question-types')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # API returns paginated response
        data_list = response.data['results']
        self.assertEqual(len(data_list), initial_count)  # Only active types
        
        names = [qt['name'] for qt in data_list]
        self.assertNotIn('inactive_type', names)


class TestGenerateQuestionsView(AIReviewAPITestCase):
    """Test AI question generation endpoint"""
    
    @patch('ai_review.views.ai_service.generate_questions')
    def test_generate_questions_success(self, mock_generate):
        """Test successful question generation"""
        # Mock AI service response
        mock_generate.return_value = [
            {
                'question_type': 'multiple_choice',
                'question_text': 'What is the main concept?',
                'correct_answer': 'Test concept',
                'options': ['Test concept', 'Wrong 1', 'Wrong 2', 'Wrong 3'],
                'explanation': 'This is the main concept',
                'keywords': ['test', 'concept'],
                'ai_model_used': 'gpt-4',
                'processing_time_ms': 1500
            }
        ]
        
        self.authenticate()
        url = reverse('ai_review:generate-questions')
        data = {
            'content_id': self.content.id,
            'question_types': ['multiple_choice'],
            'difficulty': 2,
            'count': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 1)
        
        question_data = response.data[0]
        self.assertEqual(question_data['question_text'], 'What is the main concept?')
        self.assertEqual(question_data['difficulty'], 2)
        self.assertIn('id', question_data)
        
        # Verify question was saved to database
        self.assertTrue(
            AIQuestion.objects.filter(
                content=self.content,
                question_text='What is the main concept?'
            ).exists()
        )
        
        # Verify AI service was called with correct parameters
        mock_generate.assert_called_once_with(
            content=self.content,
            question_types=['multiple_choice'],
            difficulty=2,
            count=1
        )
    
    def test_generate_questions_invalid_content_id(self):
        """Test question generation with invalid content ID"""
        self.authenticate()
        url = reverse('ai_review:generate-questions')
        data = {
            'content_id': 999999,  # Non-existent content
            'question_types': ['multiple_choice'],
            'difficulty': 1,
            'count': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content_id', response.data)
    
    def test_generate_questions_other_user_content(self):
        """Test question generation with content from another user"""
        other_content = Content.objects.create(
            title='Other User Content',
            content='Content from another user',
            category=self.category,
            author=self.other_user
        )
        
        self.authenticate()
        url = reverse('ai_review:generate-questions')
        data = {
            'content_id': other_content.id,
            'question_types': ['multiple_choice'],
            'difficulty': 1,
            'count': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('content_id', response.data)
    
    def test_generate_questions_invalid_question_types(self):
        """Test question generation with invalid question types"""
        self.authenticate()
        url = reverse('ai_review:generate-questions')
        data = {
            'content_id': self.content.id,
            'question_types': ['invalid_type'],
            'difficulty': 1,
            'count': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('question_types', response.data)
    
    @patch('ai_review.views.ai_service.generate_questions')
    def test_generate_questions_ai_service_error(self, mock_generate):
        """Test handling of AI service errors"""
        mock_generate.side_effect = AIServiceError("AI service unavailable")
        
        self.authenticate()
        url = reverse('ai_review:generate-questions')
        data = {
            'content_id': self.content.id,
            'question_types': ['multiple_choice'],
            'difficulty': 1,
            'count': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('AI service temporarily unavailable', response.data['error'])
    
    def test_generate_questions_validation(self):
        """Test question generation request validation"""
        self.authenticate()
        url = reverse('ai_review:generate-questions')
        
        # Test missing fields
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid difficulty
        data = {
            'content_id': self.content.id,
            'question_types': ['multiple_choice'],
            'difficulty': 10,  # Too high
            'count': 1
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid count
        data = {
            'content_id': self.content.id,
            'question_types': ['multiple_choice'],
            'difficulty': 1,
            'count': 50  # Too high
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestEvaluateAnswerView(AIReviewAPITestCase):
    """Test AI answer evaluation endpoint"""
    
    @patch('ai_review.views.ai_service.evaluate_answer')
    def test_evaluate_answer_success(self, mock_evaluate):
        """Test successful answer evaluation"""
        # Mock AI service response
        mock_evaluate.return_value = {
            'score': 0.85,
            'feedback': 'Good answer, captures the main idea',
            'similarity_score': 0.90,
            'evaluation_details': {
                'strengths': ['Correct concept'],
                'weaknesses': ['Could be more specific']
            },
            'ai_model_used': 'gpt-4',
            'processing_time_ms': 800
        }
        
        self.authenticate()
        url = reverse('ai_review:evaluate-answer')
        data = {
            'question_id': self.question.id,
            'user_answer': 'The main topic is AI question generation'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['score'], 0.85)
        self.assertEqual(response.data['feedback'], 'Good answer, captures the main idea')
        self.assertIn('evaluation_id', response.data)
        
        # Verify evaluation was saved to database
        evaluation = AIEvaluation.objects.get(id=response.data['evaluation_id'])
        self.assertEqual(evaluation.question, self.question)
        self.assertEqual(evaluation.user, self.user)
        self.assertEqual(evaluation.ai_score, 0.85)
        
        # Verify AI service was called correctly
        mock_evaluate.assert_called_once_with(
            question=self.question,
            user_answer='The main topic is AI question generation'
        )
    
    def test_evaluate_answer_invalid_question(self):
        """Test answer evaluation with invalid question ID"""
        self.authenticate()
        url = reverse('ai_review:evaluate-answer')
        data = {
            'question_id': 999999,  # Non-existent question
            'user_answer': 'Test answer'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('question_id', response.data)
    
    def test_evaluate_answer_inactive_question(self):
        """Test answer evaluation with inactive question"""
        # Create inactive question
        inactive_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.mc_type,
            question_text='Inactive question?',
            correct_answer='Answer',
            difficulty=1,
            is_active=False
        )
        
        self.authenticate()
        url = reverse('ai_review:evaluate-answer')
        data = {
            'question_id': inactive_question.id,
            'user_answer': 'Test answer'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('question_id', response.data)
    
    @patch('ai_review.views.ai_service.evaluate_answer')
    def test_evaluate_answer_ai_service_error(self, mock_evaluate):
        """Test handling of AI service errors during evaluation"""
        mock_evaluate.side_effect = AIServiceError("Evaluation failed")
        
        self.authenticate()
        url = reverse('ai_review:evaluate-answer')
        data = {
            'question_id': self.question.id,
            'user_answer': 'Test answer'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('AI evaluation service temporarily unavailable', response.data['error'])


class TestContentQuestionsView(AIReviewAPITestCase):
    """Test content questions listing endpoint"""
    
    def test_list_content_questions_success(self):
        """Test listing questions for user's content"""
        # Clear existing questions first
        AIQuestion.objects.filter(content=self.content).delete()
        
        # Create questions for this test
        question1 = AIQuestion.objects.create(
            content=self.content,
            question_type=self.mc_type,
            question_text='Test question 1?',
            correct_answer='Answer 1',
            difficulty=1
        )
        question2 = AIQuestion.objects.create(
            content=self.content,
            question_type=self.sa_type,
            question_text='Another question?',
            correct_answer='Another answer',
            difficulty=2
        )
        
        self.authenticate()
        url = reverse('ai_review:content-questions', kwargs={'content_id': self.content.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # API returns paginated response
        data_list = response.data['results']
        self.assertEqual(len(data_list), 2)
        
        # Check question data structure
        question_data = data_list[0]
        self.assertIn('id', question_data)
        self.assertIn('question_text', question_data)
        self.assertIn('question_type_display', question_data)
        self.assertIn('content_title', question_data)
    
    def test_list_content_questions_other_user(self):
        """Test listing questions for another user's content"""
        other_content = Content.objects.create(
            title='Other User Content',
            content='Other content',
            category=self.category,
            author=self.other_user
        )
        
        self.authenticate()
        url = reverse('ai_review:content-questions', kwargs={'content_id': other_content.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_list_content_questions_only_active(self):
        """Test that only active questions are returned"""
        # Clear existing questions first
        AIQuestion.objects.filter(content=self.content).delete()
        
        # Create active question
        active_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.mc_type,
            question_text='Active question?',
            correct_answer='Answer',
            difficulty=1,
            is_active=True
        )
        
        # Create inactive question
        inactive_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.sa_type,
            question_text='Inactive question?',
            correct_answer='Answer',
            difficulty=1,
            is_active=False
        )
        
        self.authenticate()
        url = reverse('ai_review:content-questions', kwargs={'content_id': self.content.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # API returns paginated response
        data_list = response.data['results']
        self.assertEqual(len(data_list), 1)  # Only active question


class TestUserEvaluationsView(AIReviewAPITestCase):
    """Test user evaluations listing endpoint"""
    
    def test_list_user_evaluations(self):
        """Test listing user's AI evaluations"""
        # Clear existing evaluations first
        AIEvaluation.objects.filter(user=self.user).delete()
        
        # Create evaluations
        eval1 = AIEvaluation.objects.create(
            question=self.question,
            user=self.user,
            user_answer='Test answer 1',
            ai_score=0.8,
            feedback='Good'
        )
        eval2 = AIEvaluation.objects.create(
            question=self.question,
            user=self.user,
            user_answer='Test answer 2',
            ai_score=0.9,
            feedback='Excellent'
        )
        
        # Create evaluation for other user (should not appear)
        eval3 = AIEvaluation.objects.create(
            question=self.question,
            user=self.other_user,
            user_answer='Other user answer',
            ai_score=0.7,
            feedback='Okay'
        )
        
        self.authenticate()
        url = reverse('ai_review:user-evaluations')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # API returns paginated response
        data_list = response.data['results']
        self.assertEqual(len(data_list), 2)  # Only current user's evaluations
        
        # Check evaluation data structure
        evaluation_data = data_list[0]
        self.assertIn('id', evaluation_data)
        self.assertIn('ai_score', evaluation_data)
        self.assertIn('feedback', evaluation_data)
        self.assertIn('question_text', evaluation_data)
        self.assertIn('user_email', evaluation_data)


class TestFillBlanksView(AIReviewAPITestCase):
    """Test fill-in-the-blank generation endpoint"""
    
    @patch('ai_review.views.ai_service.generate_fill_blanks')
    def test_generate_fill_blanks_success(self, mock_generate):
        """Test successful fill-blanks generation"""
        # Mock AI service response
        mock_generate.return_value = {
            'blanked_text': 'This is a [BLANK_1] about [BLANK_2].',
            'answers': {
                'BLANK_1': 'test',
                'BLANK_2': 'AI'
            },
            'keywords': ['test', 'AI'],
            'ai_model_used': 'gpt-4',
            'processing_time_ms': 1200
        }
        
        self.authenticate()
        url = reverse('ai_review:generate-fill-blanks')
        data = {
            'content_id': self.content.id,
            'num_blanks': 2
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('blanked_text', response.data)
        self.assertIn('answers', response.data)
        self.assertIn('keywords', response.data)
        
        # Verify AI service was called correctly
        mock_generate.assert_called_once_with(
            content_text=self.content.content,
            num_blanks=2
        )
    
    def test_generate_fill_blanks_invalid_content(self):
        """Test fill-blanks generation with invalid content"""
        self.authenticate()
        url = reverse('ai_review:generate-fill-blanks')
        data = {
            'content_id': 999999,
            'num_blanks': 2
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestBlurRegionsView(AIReviewAPITestCase):
    """Test blur regions identification endpoint"""
    
    @patch('ai_review.views.ai_service.identify_blur_regions')
    def test_identify_blur_regions_success(self, mock_identify):
        """Test successful blur regions identification"""
        # Mock AI service response
        mock_identify.return_value = {
            'blur_regions': [
                {
                    'text': 'key concept',
                    'start_pos': 10,
                    'end_pos': 21,
                    'importance': 0.9,
                    'concept_type': 'definition'
                }
            ],
            'concepts': ['key concept'],
            'ai_model_used': 'gpt-4',
            'processing_time_ms': 900
        }
        
        self.authenticate()
        url = reverse('ai_review:identify-blur-regions')
        data = {
            'content_id': self.content.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('blur_regions', response.data)
        self.assertIn('concepts', response.data)
        
        # Check blur region structure
        blur_region = response.data['blur_regions'][0]
        self.assertIn('text', blur_region)
        self.assertIn('importance', blur_region)
        self.assertIn('concept_type', blur_region)
        
        # Verify AI service was called correctly
        mock_identify.assert_called_once_with(
            content_text=self.content.content
        )


class TestAuthenticationRequired(AIReviewAPITestCase):
    """Test that all endpoints require authentication"""
    
    def test_endpoints_require_authentication(self):
        """Test that all AI review endpoints require authentication"""
        endpoints = [
            ('ai_review:health', 'get', {}),
            ('ai_review:question-types', 'get', {}),
            ('ai_review:generate-questions', 'post', {'content_id': 1, 'question_types': ['multiple_choice']}),
            ('ai_review:content-questions', 'get', {'content_id': 1}),
            ('ai_review:evaluate-answer', 'post', {'question_id': 1, 'user_answer': 'test'}),
            ('ai_review:user-evaluations', 'get', {}),
            ('ai_review:review-sessions', 'get', {}),
            ('ai_review:generate-fill-blanks', 'post', {'content_id': 1}),
            ('ai_review:identify-blur-regions', 'post', {'content_id': 1}),
        ]
        
        for url_name, method, kwargs in endpoints:
            with self.subTest(endpoint=url_name):
                if 'content_id' in kwargs and url_name == 'ai_review:content-questions':
                    url = reverse(url_name, kwargs={'content_id': kwargs['content_id']})
                    kwargs = {}
                else:
                    url = reverse(url_name)
                
                if method == 'get':
                    response = self.client.get(url)
                else:
                    response = self.client.post(url, kwargs, format='json')
                
                self.assertEqual(
                    response.status_code,
                    status.HTTP_401_UNAUTHORIZED,
                    f"Endpoint {url_name} should require authentication"
                )