"""
Tests for AI Blur Processing Functionality
"""
import json
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from ai_review.models import AIQuestion, AIQuestionType
from ai_review.services import AIServiceError, ai_service
from content.models import Category, Content

# Test cache settings to avoid Redis dependency
TEST_CACHE_SETTINGS = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

User = get_user_model()


@override_settings(CACHES=TEST_CACHE_SETTINGS)
class AIBlurProcessingTestCase(TestCase):
    """Test blur processing functionality for interactive learning"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        
        # Create test content about biology
        self.category = Category.objects.create(
            name='Biology',
            user=self.user
        )
        self.content = Content.objects.create(
            title='Cell Structure and Function',
            content='''
            The cell membrane is a selectively permeable barrier that controls what enters and exits the cell.
            The nucleus contains the cell's DNA and acts as the control center for cellular activities.
            Mitochondria are the powerhouses of the cell, generating ATP through cellular respiration.
            The endoplasmic reticulum (ER) is involved in protein synthesis and lipid metabolism.
            Ribosomes are small structures that synthesize proteins by translating mRNA.
            The Golgi apparatus modifies, packages, and ships proteins from the ER.
            Lysosomes contain digestive enzymes that break down waste materials and worn-out organelles.
            ''',
            category=self.category,
            author=self.user
        )
        
        # Get or create blur processing question type
        self.blur_type, _ = AIQuestionType.objects.get_or_create(
            name='blur_processing',
            defaults={
                'display_name': 'Blur Processing',
                'description': 'Identify key concepts to blur in content for interactive review',
                'is_active': True
            }
        )
    
    @patch.object(ai_service, '_make_api_call')
    def test_basic_blur_region_identification(self, mock_api_call):
        """Test basic blur region identification"""
        # Mock AI response
        mock_response = json.dumps({
            "blur_regions": [
                {
                    "text": "selectively permeable",
                    "start_pos": 23,
                    "end_pos": 44,
                    "importance": 0.9,
                    "concept_type": "definition"
                },
                {
                    "text": "DNA",
                    "start_pos": 142,
                    "end_pos": 145,
                    "importance": 0.95,
                    "concept_type": "key_term"
                },
                {
                    "text": "ATP",
                    "start_pos": 298,
                    "end_pos": 301,
                    "importance": 0.8,
                    "concept_type": "molecule"
                }
            ],
            "concepts": ["cell membrane", "nucleus", "mitochondria", "ATP", "DNA"]
        })
        
        mock_api_call.return_value = (mock_response, 1400)
        
        # Identify blur regions
        result = ai_service.identify_blur_regions(
            content_text=self.content.content
        )
        
        # Verify structure
        self.assertIn('blur_regions', result)
        self.assertIn('concepts', result)
        self.assertIn('ai_model_used', result)
        self.assertIn('processing_time_ms', result)
        
        # Verify content
        blur_regions = result['blur_regions']
        self.assertEqual(len(blur_regions), 3)
        
        # Check first region
        region1 = blur_regions[0]
        self.assertEqual(region1['text'], 'selectively permeable')
        self.assertEqual(region1['concept_type'], 'definition')
        self.assertGreater(region1['importance'], 0.8)
        self.assertIsInstance(region1['start_pos'], int)
        self.assertIsInstance(region1['end_pos'], int)
        
        # Check concepts list
        self.assertIn('DNA', result['concepts'])
        self.assertIn('mitochondria', result['concepts'])
        
        # Verify timing
        self.assertEqual(result['processing_time_ms'], 1400)
    
    @patch.object(ai_service, '_make_api_call')
    def test_blur_region_concept_types(self, mock_api_call):
        """Test identification of different concept types"""
        mock_response = json.dumps({
            "blur_regions": [
                {
                    "text": "cellular respiration",
                    "start_pos": 320,
                    "end_pos": 339,
                    "importance": 0.9,
                    "concept_type": "process"
                },
                {
                    "text": "endoplasmic reticulum",
                    "start_pos": 365,
                    "end_pos": 386,
                    "importance": 0.85,
                    "concept_type": "organelle"
                },
                {
                    "text": "protein synthesis",
                    "start_pos": 410,
                    "end_pos": 427,
                    "importance": 0.8,
                    "concept_type": "function"
                },
                {
                    "text": "mRNA",
                    "start_pos": 520,
                    "end_pos": 524,
                    "importance": 0.75,
                    "concept_type": "molecule"
                }
            ],
            "concepts": ["cellular respiration", "endoplasmic reticulum", "protein synthesis", "mRNA"]
        })
        
        mock_api_call.return_value = (mock_response, 1600)
        
        result = ai_service.identify_blur_regions(
            content_text=self.content.content
        )
        
        # Verify different concept types are identified
        concept_types = [region['concept_type'] for region in result['blur_regions']]
        self.assertIn('process', concept_types)
        self.assertIn('organelle', concept_types)
        self.assertIn('function', concept_types)
        self.assertIn('molecule', concept_types)
    
    def test_blur_processing_question_creation(self):
        """Test creating blur processing questions"""
        # Create a blur processing question that stores regions for interactive use
        blur_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.blur_type,
            question_text='Identify the blurred concepts in the cell biology text.',
            correct_answer='mitochondria, nucleus, DNA, ATP, ribosomes',
            options=None,  # Blur questions don't use traditional options
            difficulty=3,
            explanation='This interactive exercise tests recognition of key cellular components.',
            keywords=['mitochondria', 'nucleus', 'DNA', 'ATP', 'ribosomes']
        )
        
        self.assertEqual(blur_question.question_type.name, 'blur_processing')
        self.assertIn('blurred', blur_question.question_text)
        self.assertIn('mitochondria', blur_question.correct_answer)
        self.assertIn('nucleus', blur_question.correct_answer)
    
    @patch.object(ai_service, '_make_api_call')
    def test_blur_region_importance_ranking(self, mock_api_call):
        """Test that blur regions are ranked by importance"""
        mock_response = json.dumps({
            "blur_regions": [
                {
                    "text": "DNA",
                    "start_pos": 142,
                    "end_pos": 145,
                    "importance": 0.98,
                    "concept_type": "key_term"
                },
                {
                    "text": "mitochondria",
                    "start_pos": 250,
                    "end_pos": 262,
                    "importance": 0.95,
                    "concept_type": "organelle"
                },
                {
                    "text": "ribosomes",
                    "start_pos": 480,
                    "end_pos": 489,
                    "importance": 0.85,
                    "concept_type": "organelle"
                },
                {
                    "text": "enzymes",
                    "start_pos": 680,
                    "end_pos": 687,
                    "importance": 0.75,
                    "concept_type": "molecule"
                }
            ],
            "concepts": ["DNA", "mitochondria", "ribosomes", "enzymes"]
        })
        
        mock_api_call.return_value = (mock_response, 1200)
        
        result = ai_service.identify_blur_regions(
            content_text=self.content.content
        )
        
        # Verify importance scores are in expected range
        importance_scores = [region['importance'] for region in result['blur_regions']]
        
        # All scores should be between 0 and 1
        for score in importance_scores:
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
        
        # Most important concepts should have higher scores
        dna_region = next(r for r in result['blur_regions'] if r['text'] == 'DNA')
        enzyme_region = next(r for r in result['blur_regions'] if r['text'] == 'enzymes')
        self.assertGreater(dna_region['importance'], enzyme_region['importance'])
    
    @patch.object(ai_service, '_make_api_call')
    def test_blur_processing_with_text_positions(self, mock_api_call):
        """Test that blur regions have accurate text positions"""
        mock_response = json.dumps({
            "blur_regions": [
                {
                    "text": "nucleus",
                    "start_pos": 120,
                    "end_pos": 127,
                    "importance": 0.9,
                    "concept_type": "organelle"
                },
                {
                    "text": "control center",
                    "start_pos": 180,
                    "end_pos": 194,
                    "importance": 0.85,
                    "concept_type": "function"
                }
            ],
            "concepts": ["nucleus", "control center"]
        })
        
        mock_api_call.return_value = (mock_response, 1000)
        
        result = ai_service.identify_blur_regions(
            content_text=self.content.content
        )
        
        # Verify position data is valid
        for region in result['blur_regions']:
            start_pos = region['start_pos']
            end_pos = region['end_pos']
            
            # Positions should be non-negative integers
            self.assertIsInstance(start_pos, int)
            self.assertIsInstance(end_pos, int)
            self.assertGreaterEqual(start_pos, 0)
            self.assertGreater(end_pos, start_pos)
            
            # Text length should match position difference
            expected_length = end_pos - start_pos
            actual_length = len(region['text'])
            
            # Allow some tolerance for spacing differences
            self.assertLessEqual(abs(expected_length - actual_length), 5)
    
    @patch.object(ai_service, '_make_api_call')
    def test_blur_processing_error_handling(self, mock_api_call):
        """Test error handling in blur processing"""
        # Mock API error
        mock_api_call.side_effect = Exception("API connection failed")
        
        with self.assertRaises(AIServiceError):
            ai_service.identify_blur_regions(
                content_text=self.content.content
            )
    
    @patch.object(ai_service, '_make_api_call')
    def test_blur_processing_invalid_json(self, mock_api_call):
        """Test handling of invalid JSON in blur processing"""
        # Mock invalid JSON response
        invalid_response = "This is not valid JSON for blur regions"
        mock_api_call.return_value = (invalid_response, 800)
        
        with self.assertRaises(AIServiceError) as context:
            ai_service.identify_blur_regions(
                content_text=self.content.content
            )
        
        self.assertIn('parse', str(context.exception).lower())
    
    @patch.object(ai_service, '_make_api_call')
    def test_blur_processing_content_length_handling(self, mock_api_call):
        """Test blur processing with different content lengths"""
        # Test with short content
        short_content = "The cell membrane controls entry. The nucleus contains DNA."
        
        short_response = json.dumps({
            "blur_regions": [
                {
                    "text": "cell membrane",
                    "start_pos": 4,
                    "end_pos": 17,
                    "importance": 0.9,
                    "concept_type": "organelle"
                },
                {
                    "text": "DNA",
                    "start_pos": 55,
                    "end_pos": 58,
                    "importance": 0.95,
                    "concept_type": "molecule"
                }
            ],
            "concepts": ["cell membrane", "DNA"]
        })
        
        mock_api_call.return_value = (short_response, 400)
        
        result = ai_service.identify_blur_regions(content_text=short_content)
        
        self.assertEqual(len(result['blur_regions']), 2)
        self.assertIn('cell membrane', result['concepts'])
        self.assertIn('DNA', result['concepts'])
        
        # Test with very long content (should be truncated in the service)
        long_content = self.content.content * 10
        
        long_response = json.dumps({
            "blur_regions": [
                {
                    "text": "cell membrane",
                    "start_pos": 23,
                    "end_pos": 36,
                    "importance": 0.9,
                    "concept_type": "organelle"
                }
            ],
            "concepts": ["cell membrane"]
        })
        
        mock_api_call.return_value = (long_response, 1500)
        
        result_long = ai_service.identify_blur_regions(content_text=long_content)
        
        # Verify the service handled the long content
        self.assertIn('blur_regions', result_long)
        
        # Check that the service truncated the content (evident in the API call)
        call_args = mock_api_call.call_args[0][0]
        user_message = call_args[1]['content']
        self.assertLess(len(user_message), len(long_content))
    
    @patch.object(ai_service, '_make_api_call')
    def test_blur_processing_educational_context(self, mock_api_call):
        """Test that blur processing focuses on educationally relevant concepts"""
        mock_response = json.dumps({
            "blur_regions": [
                {
                    "text": "selectively permeable",
                    "start_pos": 23,
                    "end_pos": 44,
                    "importance": 0.92,
                    "concept_type": "property"
                },
                {
                    "text": "powerhouses of the cell",
                    "start_pos": 275,
                    "end_pos": 298,
                    "importance": 0.88,
                    "concept_type": "metaphor"
                },
                {
                    "text": "translating mRNA",
                    "start_pos": 505,
                    "end_pos": 521,
                    "importance": 0.85,
                    "concept_type": "process"
                }
            ],
            "concepts": ["selective permeability", "mitochondria function", "protein synthesis"]
        })
        
        mock_api_call.return_value = (mock_response, 1300)
        
        result = ai_service.identify_blur_regions(
            content_text=self.content.content
        )
        
        # Verify that educational concepts are prioritized
        blur_regions = result['blur_regions']
        
        # Should include important biological concepts
        blurred_texts = [region['text'] for region in blur_regions]
        
        # These are key educational concepts that should be blurred for learning
        self.assertIn('selectively permeable', blurred_texts)
        self.assertIn('powerhouses of the cell', blurred_texts) 
        self.assertIn('translating mRNA', blurred_texts)
        
        # Verify concept types are educationally relevant
        concept_types = [region['concept_type'] for region in blur_regions]
        educational_types = ['property', 'metaphor', 'process', 'function', 'organelle', 'molecule']
        
        for concept_type in concept_types:
            self.assertIn(concept_type, educational_types)
    
    @patch.object(ai_service, '_make_api_call')
    def test_blur_processing_interactive_learning(self, mock_api_call):
        """Test blur processing for interactive learning scenarios"""
        # Simulate a response that's optimized for interactive learning
        mock_response = json.dumps({
            "blur_regions": [
                {
                    "text": "mitochondria",
                    "start_pos": 250,
                    "end_pos": 262,
                    "importance": 0.95,
                    "concept_type": "organelle"
                },
                {
                    "text": "ATP",
                    "start_pos": 298,
                    "end_pos": 301,
                    "importance": 0.9,
                    "concept_type": "molecule"
                },
                {
                    "text": "protein synthesis",
                    "start_pos": 410,
                    "end_pos": 427,
                    "importance": 0.85,
                    "concept_type": "process"
                },
                {
                    "text": "digestive enzymes",
                    "start_pos": 670,
                    "end_pos": 687,
                    "importance": 0.8,
                    "concept_type": "molecule"
                }
            ],
            "concepts": ["organelles", "energy production", "protein synthesis", "cellular digestion"]
        })
        
        mock_api_call.return_value = (mock_response, 1600)
        
        result = ai_service.identify_blur_regions(
            content_text=self.content.content
        )
        
        # For interactive learning, the system should identify:
        # 1. Key terms that test vocabulary
        # 2. Concepts that test understanding
        # 3. Processes that test knowledge of mechanisms
        
        blur_regions = result['blur_regions']
        self.assertEqual(len(blur_regions), 4)
        
        # Should have a mix of different concept types for comprehensive learning
        concept_types = [region['concept_type'] for region in blur_regions]
        unique_types = set(concept_types)
        self.assertGreaterEqual(len(unique_types), 2)  # At least 2 different types
        
        # All regions should have reasonable importance scores for learning
        for region in blur_regions:
            self.assertGreaterEqual(region['importance'], 0.7)  # High educational value
        
        # Concepts list should provide broader context
        concepts = result['concepts']
        self.assertGreaterEqual(len(concepts), 3)  # Multiple learning objectives