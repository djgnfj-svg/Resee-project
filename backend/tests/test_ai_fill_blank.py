"""
Tests for AI Fill-in-the-Blank Processing Logic
"""
import json
from unittest.mock import patch, Mock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from content.models import Content, Category
from ai_review.models import AIQuestionType, AIQuestion
from ai_review.services import ai_service, AIServiceError

# Test cache settings to avoid Redis dependency
TEST_CACHE_SETTINGS = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

User = get_user_model()


@override_settings(CACHES=TEST_CACHE_SETTINGS)
class AIFillBlankTestCase(TestCase):
    """Test fill-in-the-blank processing logic"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        
        # Create test content about physics
        self.category = Category.objects.create(
            name='Physics',
            user=self.user
        )
        self.content = Content.objects.create(
            title='Newton\'s Laws of Motion',
            content='''
            Newton's First Law states that an object at rest stays at rest and an object in motion stays in motion with the same speed and in the same direction unless acted upon by an unbalanced force.
            Newton's Second Law can be expressed as F = ma, where F is the net force applied to an object, m is the mass of the object, and a is the acceleration produced.
            Newton's Third Law states that for every action, there is an equal and opposite reaction.
            These laws form the foundation of classical mechanics and describe the relationship between forces and motion.
            ''',
            category=self.category,
            author=self.user
        )
        
        # Get or create fill-in-blank question type
        self.fb_type, _ = AIQuestionType.objects.get_or_create(
            name='fill_blank',
            defaults={
                'display_name': 'Fill in the Blank',
                'description': 'Generate questions with key terms removed for filling',
                'is_active': True
            }
        )
    
    @patch.object(ai_service, '_make_api_call')
    def test_basic_fill_blank_generation(self, mock_api_call):
        """Test basic fill-in-the-blank generation"""
        # Mock AI response
        mock_response = json.dumps({
            "blanked_text": "Newton's [BLANK_1] Law states that an object at rest stays at rest and an object in motion stays in motion unless acted upon by an [BLANK_2] force.",
            "answers": {
                "BLANK_1": "First",
                "BLANK_2": "unbalanced"
            },
            "keywords": ["First", "unbalanced", "law", "motion"]
        })
        
        mock_api_call.return_value = (mock_response, 1200)
        
        # Generate fill-in-the-blank exercise
        result = ai_service.generate_fill_blanks(
            content_text=self.content.content,
            num_blanks=2
        )
        
        # Verify structure
        self.assertIn('blanked_text', result)
        self.assertIn('answers', result)
        self.assertIn('keywords', result)
        self.assertIn('ai_model_used', result)
        self.assertIn('processing_time_ms', result)
        
        # Verify content
        self.assertIn('[BLANK_1]', result['blanked_text'])
        self.assertIn('[BLANK_2]', result['blanked_text'])
        self.assertEqual(result['answers']['BLANK_1'], 'First')
        self.assertEqual(result['answers']['BLANK_2'], 'unbalanced')
        self.assertIn('First', result['keywords'])
        self.assertEqual(result['processing_time_ms'], 1200)
    
    @patch.object(ai_service, '_make_api_call')
    def test_fill_blank_with_different_counts(self, mock_api_call):
        """Test generating different numbers of blanks"""
        # Test with 1 blank
        single_response = json.dumps({
            "blanked_text": "Newton's Second Law can be expressed as [BLANK_1], where F is the net force.",
            "answers": {
                "BLANK_1": "F = ma"
            },
            "keywords": ["F = ma", "formula", "second law"]
        })
        
        mock_api_call.return_value = (single_response, 800)
        
        result_single = ai_service.generate_fill_blanks(
            content_text=self.content.content,
            num_blanks=1
        )
        
        self.assertEqual(len(result_single['answers']), 1)
        self.assertIn('[BLANK_1]', result_single['blanked_text'])
        self.assertNotIn('[BLANK_2]', result_single['blanked_text'])
        
        # Test with 5 blanks
        multiple_response = json.dumps({
            "blanked_text": "[BLANK_1] First Law states that an [BLANK_2] at rest stays at [BLANK_3] and an object in [BLANK_4] stays in motion unless acted upon by an [BLANK_5] force.",
            "answers": {
                "BLANK_1": "Newton's",
                "BLANK_2": "object",
                "BLANK_3": "rest",
                "BLANK_4": "motion", 
                "BLANK_5": "unbalanced"
            },
            "keywords": ["Newton's", "object", "rest", "motion", "unbalanced"]
        })
        
        mock_api_call.return_value = (multiple_response, 1500)
        
        result_multiple = ai_service.generate_fill_blanks(
            content_text=self.content.content,
            num_blanks=5
        )
        
        self.assertEqual(len(result_multiple['answers']), 5)
        for i in range(1, 6):
            self.assertIn(f'[BLANK_{i}]', result_multiple['blanked_text'])
        
        # Verify API was called twice
        self.assertEqual(mock_api_call.call_count, 2)
    
    def test_fill_blank_question_creation(self):
        """Test creating fill-in-the-blank questions"""
        fb_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.fb_type,
            question_text='Newton\'s [BLANK_1] Law states that for every action, there is an equal and opposite [BLANK_2].',
            correct_answer='BLANK_1: Third, BLANK_2: reaction',
            options=None,  # Fill-blank questions don't use options field
            difficulty=2,
            explanation='This tests understanding of Newton\'s Third Law.',
            keywords=['Third', 'reaction', 'action', 'Newton']
        )
        
        self.assertEqual(fb_question.question_type.name, 'fill_blank')
        self.assertIn('[BLANK_1]', fb_question.question_text)
        self.assertIn('[BLANK_2]', fb_question.question_text)
        self.assertIn('Third', fb_question.correct_answer)
        self.assertIn('reaction', fb_question.correct_answer)
    
    @patch.object(ai_service, '_make_api_call')
    def test_fill_blank_with_formulas(self, mock_api_call):
        """Test fill-in-the-blank with mathematical formulas"""
        formula_response = json.dumps({
            "blanked_text": "Newton's Second Law can be expressed as [BLANK_1], where F is the [BLANK_2], m is the [BLANK_3], and a is the [BLANK_4].",
            "answers": {
                "BLANK_1": "F = ma",
                "BLANK_2": "net force",
                "BLANK_3": "mass",
                "BLANK_4": "acceleration"
            },
            "keywords": ["F = ma", "net force", "mass", "acceleration"]
        })
        
        mock_api_call.return_value = (formula_response, 1000)
        
        result = ai_service.generate_fill_blanks(
            content_text=self.content.content,
            num_blanks=4
        )
        
        # Verify formula is preserved as a unit
        self.assertIn('F = ma', result['answers']['BLANK_1'])
        self.assertIn('net force', result['answers']['BLANK_2'])
        self.assertIn('mass', result['answers']['BLANK_3'])
        self.assertIn('acceleration', result['answers']['BLANK_4'])
    
    @patch.object(ai_service, '_make_api_call')
    def test_fill_blank_key_concept_selection(self, mock_api_call):
        """Test that important concepts are selected for blanking"""
        concept_response = json.dumps({
            "blanked_text": "These laws form the foundation of [BLANK_1] and describe the relationship between [BLANK_2] and motion.",
            "answers": {
                "BLANK_1": "classical mechanics",
                "BLANK_2": "forces"
            },
            "keywords": ["classical mechanics", "forces", "foundation", "relationship"]
        })
        
        mock_api_call.return_value = (concept_response, 900)
        
        result = ai_service.generate_fill_blanks(
            content_text=self.content.content,
            num_blanks=2
        )
        
        # Verify that key physics concepts are selected
        answers = result['answers']
        self.assertIn('classical mechanics', answers['BLANK_1'])
        self.assertIn('forces', answers['BLANK_2'])
        
        # These should be important conceptual terms, not just random words
        for answer in answers.values():
            self.assertGreater(len(answer), 3)  # Not just articles or short words
    
    @patch.object(ai_service, '_make_api_call') 
    def test_fill_blank_answer_evaluation(self, mock_api_call):
        """Test evaluation of fill-in-the-blank answers"""
        # First, create a fill-blank question
        fb_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.fb_type,
            question_text='Newton\'s [BLANK_1] Law states that F = [BLANK_2].',
            correct_answer='BLANK_1: Second, BLANK_2: ma',
            difficulty=2
        )
        
        # Mock evaluation response for correct answers
        correct_response = json.dumps({
            "score": 0.95,
            "feedback": "Excellent! You correctly identified Newton's Second Law and the formula F = ma.",
            "similarity_score": 0.98,
            "evaluation_details": {
                "strengths": ["Correctly identified Second Law", "Accurate formula"],
                "weaknesses": [],
                "suggestions": []
            }
        })
        
        mock_api_call.return_value = (correct_response, 600)
        
        user_answer = "BLANK_1: Second, BLANK_2: ma"
        evaluation = ai_service.evaluate_answer(fb_question, user_answer)
        
        self.assertGreater(evaluation['score'], 0.9)
        self.assertIn('Second Law', evaluation['feedback'])
        self.assertIn('F = ma', evaluation['feedback'])
    
    @patch.object(ai_service, '_make_api_call')
    def test_fill_blank_partial_correct_evaluation(self, mock_api_call):
        """Test evaluation of partially correct fill-blank answers"""
        fb_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.fb_type,
            question_text='Newton\'s [BLANK_1] Law states that for every [BLANK_2], there is an equal and opposite [BLANK_3].',
            correct_answer='BLANK_1: Third, BLANK_2: action, BLANK_3: reaction',
            difficulty=2
        )
        
        # Mock evaluation for partially correct answer
        partial_response = json.dumps({
            "score": 0.67,
            "feedback": "Good work! You got the law number and reaction correct, but 'force' should be 'action' for the second blank.",
            "similarity_score": 0.70,
            "evaluation_details": {
                "strengths": ["Correctly identified Third Law", "Correct understanding of reaction"],
                "weaknesses": ["Confused action with force"],
                "suggestions": ["Remember the exact terminology: action and reaction"]
            }
        })
        
        mock_api_call.return_value = (partial_response, 700)
        
        user_answer = "BLANK_1: Third, BLANK_2: force, BLANK_3: reaction"
        evaluation = ai_service.evaluate_answer(fb_question, user_answer)
        
        self.assertGreater(evaluation['score'], 0.5)
        self.assertLess(evaluation['score'], 0.8)
        self.assertIn('action', evaluation['feedback'])
    
    @patch.object(ai_service, '_make_api_call')
    def test_fill_blank_error_handling(self, mock_api_call):
        """Test error handling in fill-blank generation"""
        # Mock API error
        mock_api_call.side_effect = Exception("API connection failed")
        
        with self.assertRaises(AIServiceError):
            ai_service.generate_fill_blanks(
                content_text=self.content.content,
                num_blanks=3
            )
    
    @patch.object(ai_service, '_make_api_call')
    def test_fill_blank_invalid_json_handling(self, mock_api_call):
        """Test handling of invalid JSON responses"""
        # Mock invalid JSON response
        invalid_response = "This is not valid JSON at all"
        mock_api_call.return_value = (invalid_response, 800)
        
        with self.assertRaises(AIServiceError) as context:
            ai_service.generate_fill_blanks(
                content_text=self.content.content,
                num_blanks=2
            )
        
        self.assertIn('parse', str(context.exception).lower())
    
    def test_fill_blank_text_length_handling(self):
        """Test handling of different text lengths"""
        # Test with very short content
        short_content = "F = ma. Force equals mass times acceleration."
        
        with patch.object(ai_service, '_make_api_call') as mock_call:
            short_response = json.dumps({
                "blanked_text": "[BLANK_1] equals mass times [BLANK_2].",
                "answers": {
                    "BLANK_1": "Force",
                    "BLANK_2": "acceleration"
                },
                "keywords": ["Force", "acceleration"]
            })
            mock_call.return_value = (short_response, 400)
            
            result = ai_service.generate_fill_blanks(
                content_text=short_content,
                num_blanks=2
            )
            
            self.assertIn('Force', result['answers']['BLANK_1'])
            self.assertIn('acceleration', result['answers']['BLANK_2'])
        
        # Test with very long content (should be truncated)
        long_content = self.content.content * 10  # Very long text
        
        with patch.object(ai_service, '_make_api_call') as mock_call:
            # The service should truncate to 1500 characters
            long_response = json.dumps({
                "blanked_text": "Newton's [BLANK_1] Law states...",
                "answers": {
                    "BLANK_1": "First"
                },
                "keywords": ["First"]
            })
            mock_call.return_value = (long_response, 1000)
            
            result = ai_service.generate_fill_blanks(
                content_text=long_content,
                num_blanks=1
            )
            
            # Verify the call was made (content should be truncated in service)
            call_args = mock_call.call_args[0][0]  # First argument (messages)
            user_message = call_args[1]['content']  # User message content
            
            # The content in the message should be truncated
            self.assertLess(len(user_message), len(long_content))
            self.assertIn('Newton', user_message)  # Should still contain relevant content
    
    @patch.object(ai_service, '_make_api_call')
    def test_fill_blank_difficulty_adaptation(self, mock_api_call):
        """Test that fill-blank exercises can be adapted for different difficulty levels"""
        # Create questions with different complexity levels
        
        # Simple concept blanks (easier)
        simple_response = json.dumps({
            "blanked_text": "An object at [BLANK_1] stays at rest unless acted upon by a [BLANK_2].",
            "answers": {
                "BLANK_1": "rest",
                "BLANK_2": "force"
            },
            "keywords": ["rest", "force", "motion"]
        })
        
        # Complex multi-concept blanks (harder)
        complex_response = json.dumps({
            "blanked_text": "Newton's Second Law establishes the relationship between [BLANK_1], [BLANK_2], and [BLANK_3] through the equation F = ma.",
            "answers": {
                "BLANK_1": "net force",
                "BLANK_2": "mass", 
                "BLANK_3": "acceleration"
            },
            "keywords": ["net force", "mass", "acceleration", "relationship"]
        })
        
        # Test simple version
        mock_api_call.return_value = (simple_response, 600)
        simple_result = ai_service.generate_fill_blanks(
            content_text=self.content.content,
            num_blanks=2
        )
        
        # Test complex version  
        mock_api_call.return_value = (complex_response, 900)
        complex_result = ai_service.generate_fill_blanks(
            content_text=self.content.content,
            num_blanks=3
        )
        
        # Verify different complexity levels
        self.assertEqual(len(simple_result['answers']), 2)
        self.assertEqual(len(complex_result['answers']), 3)
        
        # Simple should have basic terms
        self.assertIn('rest', simple_result['answers']['BLANK_1'])
        
        # Complex should have more sophisticated concepts
        self.assertIn('net force', complex_result['answers']['BLANK_1'])
        self.assertIn('acceleration', complex_result['answers']['BLANK_3'])