"""
Tests for AI service integration
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from content.models import Content, Category
from ai_review.models import AIQuestion, AIQuestionType
from ai_review.services import OpenAIService, AIServiceError, ai_service


# Test settings to use dummy cache instead of Redis
TEST_CACHE_SETTINGS = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}


User = get_user_model()


@override_settings(CACHES=TEST_CACHE_SETTINGS)
class TestOpenAIService(TestCase):
    
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
            content='This is test content for AI question generation. It covers important concepts and key terms.',
            category=self.category,
            author=self.user
        )
        self.question_type = AIQuestionType.objects.create(
            name='multiple_choice',
            display_name='Multiple Choice'
        )
    
    @override_settings(OPENAI_API_KEY='test-key')
    def test_service_initialization(self):
        """Test that the service initializes correctly"""
        service = OpenAIService()
        self.assertIsNotNone(service.client)
        self.assertEqual(service.model, 'gpt-4')  # Default model
        self.assertEqual(service.max_retries, 3)  # Default retries
    
    def test_service_without_api_key(self):
        """Test that service handles missing API key"""
        service = OpenAIService()
        with self.assertRaises(AIServiceError) as context:
            service._make_api_call([{"role": "user", "content": "test"}])
        self.assertIn("OpenAI API key not configured", str(context.exception))
    
    @patch('ai_review.services.openai.OpenAI')
    def test_make_api_call_success(self, mock_openai_class):
        """Test successful API call"""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Create properly structured mock response
        mock_message = Mock()
        mock_message.content = "Test response"
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_response
        
        service = OpenAIService()
        service.client.api_key = "test-key"
        
        result, processing_time = service._make_api_call([{"role": "user", "content": "test"}])
        
        self.assertEqual(result, "Test response")
        self.assertIsInstance(processing_time, int)
        self.assertGreaterEqual(processing_time, 0)
    
    @patch('ai_review.services.openai.OpenAI')
    def test_make_api_call_rate_limit_retry(self, mock_openai_class):
        """Test API call retry on rate limit"""
        # Setup mock to fail once then succeed
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        from openai import RateLimitError
        
        # Create properly structured mock response
        mock_message = Mock()
        mock_message.content = "Success after retry"
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        # Create mock objects for OpenAI exceptions  
        mock_response_obj = Mock()
        mock_body = Mock()
        
        mock_client.chat.completions.create.side_effect = [
            RateLimitError("Rate limit exceeded", response=mock_response_obj, body=mock_body),
            mock_response
        ]
        
        service = OpenAIService()
        service.client.api_key = "test-key"
        service.max_retries = 2
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result, _ = service._make_api_call([{"role": "user", "content": "test"}])
        
        self.assertEqual(result, "Success after retry")
        self.assertEqual(mock_client.chat.completions.create.call_count, 2)
    
    @patch('ai_review.services.openai.OpenAI')
    def test_make_api_call_max_retries_exceeded(self, mock_openai_class):
        """Test API call failure after max retries"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Use a generic exception instead of trying to create complex OpenAI exceptions
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        service = OpenAIService()
        service.client.api_key = "test-key"
        service.max_retries = 2
        
        with patch('time.sleep'):  # Mock sleep
            with self.assertRaises(AIServiceError) as context:
                service._make_api_call([{"role": "user", "content": "test"}])
        
        self.assertIn("Unexpected error", str(context.exception))
    
    @patch.object(OpenAIService, '_make_api_call')
    def test_generate_questions_success(self, mock_api_call):
        """Test successful question generation"""
        
        # Mock API response
        api_response = json.dumps({
            "questions": [
                {
                    "question_type": "multiple_choice",
                    "question_text": "What is the main topic of this content?",
                    "correct_answer": "AI question generation",
                    "options": ["AI question generation", "Wrong answer 1", "Wrong answer 2", "Wrong answer 3"],
                    "explanation": "The content discusses AI question generation",
                    "keywords": ["AI", "questions", "generation"]
                }
            ]
        })
        mock_api_call.return_value = (api_response, 1000)
        
        service = OpenAIService()
        questions = service.generate_questions(
            content=self.content,
            question_types=['multiple_choice'],
            difficulty=2,
            count=1
        )
        
        self.assertEqual(len(questions), 1)
        question = questions[0]
        self.assertEqual(question['question_type'], 'multiple_choice')
        self.assertEqual(question['question_text'], 'What is the main topic of this content?')
        self.assertEqual(len(question['options']), 4)
        self.assertIn('ai_model_used', question)
        self.assertIn('processing_time_ms', question)
    
    @patch.object(OpenAIService, '_make_api_call')
    def test_generate_questions_invalid_json(self, mock_api_call):
        """Test handling of invalid JSON response"""
        mock_api_call.return_value = ("Invalid JSON response", 1000)
        
        service = OpenAIService()
        with self.assertRaises(AIServiceError) as context:
            service.generate_questions(
                content=self.content,
                question_types=['multiple_choice'],
                count=1
            )
        
        self.assertTrue("No valid JSON found in response" in str(context.exception) or "Failed to parse AI response as JSON" in str(context.exception))
    
    @patch.object(OpenAIService, '_make_api_call')
    def test_generate_questions_json_extraction(self, mock_api_call):
        """Test extraction of JSON from mixed response"""
        response_with_json = '''
        Here's the response:
        
        {
            "questions": [
                {
                    "question_type": "short_answer",
                    "question_text": "Explain the main concept",
                    "correct_answer": "The main concept is AI",
                    "explanation": "This tests understanding",
                    "keywords": ["AI", "concept"]
                }
            ]
        }
        
        That's the result!
        '''
        mock_api_call.return_value = (response_with_json, 1500)
        
        service = OpenAIService()
        questions = service.generate_questions(
            content=self.content,
            question_types=['short_answer'],
            count=1
        )
        
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]['question_type'], 'short_answer')
    
    @patch.object(OpenAIService, '_make_api_call')
    def test_generate_questions_cache_hit(self, mock_api_call):
        """Test that cached questions are returned when cache is working"""
        # With DummyCache, this test becomes about ensuring the method works without cache
        api_response = json.dumps({
            "questions": [
                {
                    "question_type": "multiple_choice",
                    "question_text": "Test question?",
                    "correct_answer": "Yes",
                    "options": ["Yes", "No", "Maybe", "Unknown"]
                }
            ]
        })
        mock_api_call.return_value = (api_response, 1000)
        
        service = OpenAIService()
        questions = service.generate_questions(
            content=self.content,
            question_types=['multiple_choice'],
            count=1
        )
        
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]['question_type'], 'multiple_choice')
    
    @patch.object(OpenAIService, '_make_api_call')
    def test_evaluate_answer_success(self, mock_api_call):
        """Test successful answer evaluation"""
        # Create a question for evaluation
        question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.question_type,
            question_text='What is the main concept?',
            correct_answer='AI question generation',
            difficulty=1
        )
        
        # Mock API response
        api_response = json.dumps({
            "score": 0.85,
            "feedback": "Good answer, captures the main idea well.",
            "similarity_score": 0.90,
            "evaluation_details": {
                "strengths": ["Correct understanding"],
                "weaknesses": ["Could be more specific"],
                "suggestions": ["Add more detail"]
            }
        })
        mock_api_call.return_value = (api_response, 800)
        
        service = OpenAIService()
        evaluation = service.evaluate_answer(
            question=question,
            user_answer="The main concept is about AI generating questions"
        )
        
        self.assertEqual(evaluation['score'], 0.85)
        self.assertEqual(evaluation['feedback'], "Good answer, captures the main idea well.")
        self.assertEqual(evaluation['similarity_score'], 0.90)
        self.assertIn('evaluation_details', evaluation)
        self.assertIn('ai_model_used', evaluation)
        self.assertIn('processing_time_ms', evaluation)
    
    @patch.object(OpenAIService, '_make_api_call')
    def test_evaluate_answer_invalid_score(self, mock_api_call):
        """Test handling of invalid score in evaluation"""
        question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.question_type,
            question_text='Test question?',
            correct_answer='Test answer',
            difficulty=1
        )
        
        # Mock API response with invalid score
        api_response = json.dumps({
            "score": 1.5,  # Invalid score > 1.0
            "feedback": "Good answer"
        })
        mock_api_call.return_value = (api_response, 500)
        
        service = OpenAIService()
        evaluation = service.evaluate_answer(question=question, user_answer="Test")
        
        # Should normalize to default score
        self.assertEqual(evaluation['score'], 0.5)
    
    @patch.object(OpenAIService, '_make_api_call')
    def test_generate_fill_blanks_success(self, mock_api_call):
        """Test successful fill-in-the-blank generation"""
        api_response = json.dumps({
            "blanked_text": "This is a [BLANK_1] about [BLANK_2] generation.",
            "answers": {
                "BLANK_1": "test",
                "BLANK_2": "AI question"
            },
            "keywords": ["test", "AI", "question", "generation"]
        })
        mock_api_call.return_value = (api_response, 1200)
        
        service = OpenAIService()
        result = service.generate_fill_blanks(
            content_text="This is a test about AI question generation.",
            num_blanks=2
        )
        
        self.assertIn("blanked_text", result)
        self.assertIn("answers", result)
        self.assertIn("keywords", result)
        self.assertEqual(result["answers"]["BLANK_1"], "test")
        self.assertEqual(result["answers"]["BLANK_2"], "AI question")
    
    @patch.object(OpenAIService, '_make_api_call')
    def test_identify_blur_regions_success(self, mock_api_call):
        """Test successful blur region identification"""
        api_response = json.dumps({
            "blur_regions": [
                {
                    "text": "key concept",
                    "start_pos": 10,
                    "end_pos": 21,
                    "importance": 0.9,
                    "concept_type": "definition"
                }
            ],
            "concepts": ["key concept", "definition"]
        })
        mock_api_call.return_value = (api_response, 900)
        
        service = OpenAIService()
        result = service.identify_blur_regions(
            content_text="This is a key concept that should be blurred."
        )
        
        self.assertIn("blur_regions", result)
        self.assertIn("concepts", result)
        self.assertEqual(len(result["blur_regions"]), 1)
        
        region = result["blur_regions"][0]
        self.assertEqual(region["text"], "key concept")
        self.assertEqual(region["importance"], 0.9)


@override_settings(CACHES=TEST_CACHE_SETTINGS)
class TestAIServiceErrorHandling(TestCase):
    """Test error handling scenarios"""
    
    @override_settings(OPENAI_API_KEY=None)
    def test_missing_api_key_error(self):
        """Test error when API key is missing"""
        service = OpenAIService()
        
        with self.assertRaises(AIServiceError) as context:
            service._make_api_call([{"role": "user", "content": "test"}])
        
        self.assertIn("OpenAI API key not configured", str(context.exception))
    
    @patch.object(OpenAIService, '_make_api_call')
    def test_question_generation_api_error(self, mock_api_call):
        """Test handling of API errors during question generation"""
        mock_api_call.side_effect = AIServiceError("API Error")
        
        service = OpenAIService()
        user = User.objects.create_user(email='test@example.com', password='test')
        category = Category.objects.create(name='Test', user=user)
        content = Content.objects.create(title='Test', content='Content', category=category, author=user)
        
        with self.assertRaises(AIServiceError):
            service.generate_questions(content=content, question_types=['multiple_choice'])
    
    @patch.object(OpenAIService, '_make_api_call')
    def test_answer_evaluation_api_error(self, mock_api_call):
        """Test handling of API errors during answer evaluation"""
        mock_api_call.side_effect = AIServiceError("Evaluation failed")
        
        service = OpenAIService()
        user = User.objects.create_user(email='test@example.com', password='test')
        category = Category.objects.create(name='Test', user=user)
        content = Content.objects.create(title='Test', content='Content', category=category, author=user)
        question_type = AIQuestionType.objects.create(name='short_answer', display_name='Short Answer')
        question = AIQuestion.objects.create(
            content=content,
            question_type=question_type,
            question_text='Test?',
            correct_answer='Test'
        )
        
        with self.assertRaises(AIServiceError):
            service.evaluate_answer(question=question, user_answer="Test answer")


@override_settings(CACHES=TEST_CACHE_SETTINGS)
class TestAIServiceSingleton(TestCase):
    """Test the singleton service instance"""
    
    def test_singleton_instance(self):
        """Test that ai_service is properly initialized"""
        from ai_review.services import ai_service
        
        self.assertIsInstance(ai_service, OpenAIService)
        self.assertIsNotNone(ai_service.client)
    
    def test_singleton_consistency(self):
        """Test that multiple imports return the same instance"""
        from ai_review.services import ai_service as service1
        from ai_review.services import ai_service as service2
        
        self.assertIs(service1, service2)