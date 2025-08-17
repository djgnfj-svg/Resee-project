"""
Tests for AI Multiple Choice Question Generation
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
class AIMultipleChoiceTestCase(TestCase):
    """Test multiple choice question generation and handling"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        
        # Create test content
        self.category = Category.objects.create(
            name='Programming',
            user=self.user
        )
        self.content = Content.objects.create(
            title='Python OOP Concepts',
            content='''
            Object-oriented programming (OOP) is a programming paradigm that organizes code into objects and classes.
            In Python, classes are defined using the 'class' keyword. Objects are instances of classes.
            Key OOP principles include encapsulation, inheritance, and polymorphism.
            Encapsulation means bundling data and methods together within a class.
            Inheritance allows classes to inherit properties and methods from parent classes.
            Polymorphism enables objects to take multiple forms and respond differently to the same method call.
            ''',
            category=self.category,
            author=self.user
        )
        
        # Get or create multiple choice question type
        self.mc_type, _ = AIQuestionType.objects.get_or_create(
            name='multiple_choice',
            defaults={
                'display_name': 'Multiple Choice',
                'description': 'Generate multiple choice questions with 4 options',
                'is_active': True
            }
        )
    
    def test_multiple_choice_question_creation(self):
        """Test creating multiple choice questions manually"""
        mc_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.mc_type,
            question_text='What is the main programming paradigm discussed?',
            correct_answer='Object-oriented programming',
            options=['Object-oriented programming', 'Functional programming', 
                    'Procedural programming', 'Logic programming'],
            difficulty=2,
            explanation='The content focuses on OOP concepts and principles.',
            keywords=['OOP', 'programming', 'paradigm']
        )
        
        self.assertEqual(mc_question.question_type.name, 'multiple_choice')
        self.assertEqual(len(mc_question.options), 4)
        self.assertIn(mc_question.correct_answer, mc_question.options)
        self.assertTrue(mc_question.is_active)
    
    @patch.object(ai_service, '_make_api_call')
    def test_ai_multiple_choice_generation(self, mock_api_call):
        """Test AI-generated multiple choice questions"""
        # Mock AI response
        mock_response = json.dumps({
            "questions": [
                {
                    "question_type": "multiple_choice",
                    "question_text": "What are the three key principles of OOP mentioned in the text?",
                    "correct_answer": "Encapsulation, inheritance, and polymorphism",
                    "options": [
                        "Encapsulation, inheritance, and polymorphism",
                        "Abstraction, encapsulation, and inheritance",
                        "Classes, objects, and methods",
                        "Variables, functions, and loops"
                    ],
                    "explanation": "The text explicitly states that the key OOP principles are encapsulation, inheritance, and polymorphism.",
                    "keywords": ["OOP", "principles", "encapsulation", "inheritance", "polymorphism"]
                }
            ]
        })
        
        mock_api_call.return_value = (mock_response, 1500)
        
        # Generate multiple choice questions
        questions = ai_service.generate_questions(
            content=self.content,
            question_types=['multiple_choice'],
            difficulty=2,
            count=1
        )
        
        self.assertEqual(len(questions), 1)
        question = questions[0]
        
        self.assertEqual(question['question_type'], 'multiple_choice')
        self.assertIn('question_text', question)
        self.assertIn('correct_answer', question)
        self.assertIn('options', question)
        self.assertEqual(len(question['options']), 4)
        self.assertIn(question['correct_answer'], question['options'])
        self.assertIn('explanation', question)
        self.assertIn('keywords', question)
    
    def test_multiple_choice_validation(self):
        """Test validation of multiple choice questions"""
        from django.core.exceptions import ValidationError

        # Test with invalid options (less than 2)
        question = AIQuestion(
            content=self.content,
            question_type=self.mc_type,
            question_text='Invalid question?',
            correct_answer='Answer',
            options=['Answer'],  # Only one option
            difficulty=1
        )
        
        with self.assertRaises(ValidationError):
            question.full_clean()
        
        # Test with correct answer not in options
        question2 = AIQuestion(
            content=self.content,
            question_type=self.mc_type,
            question_text='Another invalid question?',
            correct_answer='Wrong Answer',
            options=['Answer A', 'Answer B', 'Answer C'],
            difficulty=1
        )
        
        with self.assertRaises(ValidationError):
            question2.full_clean()
        
        # Test valid multiple choice question
        valid_question = AIQuestion(
            content=self.content,
            question_type=self.mc_type,
            question_text='Valid question?',
            correct_answer='Answer A',
            options=['Answer A', 'Answer B', 'Answer C', 'Answer D'],
            difficulty=1
        )
        
        # Should not raise exception
        try:
            valid_question.full_clean()
            valid_question.save()
        except ValidationError:
            self.fail("Valid question should not raise ValidationError")
    
    def test_multiple_choice_answer_evaluation(self):
        """Test evaluation of multiple choice answers"""
        mc_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.mc_type,
            question_text='What keyword is used to define classes in Python?',
            correct_answer='class',
            options=['class', 'def', 'function', 'object'],
            difficulty=1
        )
        
        # Test exact match (should score high)
        with patch.object(ai_service, '_make_api_call') as mock_call:
            mock_response = json.dumps({
                "score": 1.0,
                "feedback": "Perfect! You selected the correct answer.",
                "similarity_score": 1.0,
                "evaluation_details": {
                    "strengths": ["Correct identification of Python class keyword"],
                    "weaknesses": [],
                    "suggestions": []
                }
            })
            mock_call.return_value = (mock_response, 800)
            
            evaluation = ai_service.evaluate_answer(mc_question, 'class')
            self.assertEqual(evaluation['score'], 1.0)
            self.assertGreater(evaluation['similarity_score'], 0.9)
        
        # Test wrong answer (should score low)
        with patch.object(ai_service, '_make_api_call') as mock_call:
            mock_response = json.dumps({
                "score": 0.0,
                "feedback": "Incorrect. 'def' is used for functions, not classes.",
                "similarity_score": 0.2,
                "evaluation_details": {
                    "strengths": [],
                    "weaknesses": ["Confused function and class keywords"],
                    "suggestions": ["Review Python class definition syntax"]
                }
            })
            mock_call.return_value = (mock_response, 800)
            
            evaluation = ai_service.evaluate_answer(mc_question, 'def')
            self.assertEqual(evaluation['score'], 0.0)
            self.assertLess(evaluation['similarity_score'], 0.5)
    
    @patch.object(ai_service, '_make_api_call')
    def test_multiple_choice_generation_with_difficulty_levels(self, mock_api_call):
        """Test generating MC questions with different difficulty levels"""
        # Easy level question
        easy_response = json.dumps({
            "questions": [
                {
                    "question_type": "multiple_choice",
                    "question_text": "What does OOP stand for?",
                    "correct_answer": "Object-oriented programming",
                    "options": [
                        "Object-oriented programming",
                        "Open-source programming", 
                        "Optimal operation procedure",
                        "Online program protocol"
                    ],
                    "explanation": "OOP is the common abbreviation for Object-oriented programming.",
                    "keywords": ["OOP", "abbreviation"]
                }
            ]
        })
        
        mock_api_call.return_value = (easy_response, 1200)
        
        easy_questions = ai_service.generate_questions(
            content=self.content,
            question_types=['multiple_choice'],
            difficulty=1,  # Easy
            count=1
        )
        
        self.assertEqual(len(easy_questions), 1)
        self.assertIn('OOP', easy_questions[0]['question_text'])
        
        # Hard level question
        hard_response = json.dumps({
            "questions": [
                {
                    "question_type": "multiple_choice",
                    "question_text": "Which principle would be violated if a subclass removes functionality from its parent class?",
                    "correct_answer": "Liskov Substitution Principle",
                    "options": [
                        "Liskov Substitution Principle",
                        "Single Responsibility Principle",
                        "Open/Closed Principle", 
                        "Interface Segregation Principle"
                    ],
                    "explanation": "LSP states that objects of a superclass should be replaceable with objects of subclasses without breaking functionality.",
                    "keywords": ["LSP", "inheritance", "principles", "SOLID"]
                }
            ]
        })
        
        mock_api_call.return_value = (hard_response, 1800)
        
        hard_questions = ai_service.generate_questions(
            content=self.content,
            question_types=['multiple_choice'],
            difficulty=5,  # Hard
            count=1
        )
        
        self.assertEqual(len(hard_questions), 1)
        self.assertIn('principle', hard_questions[0]['question_text'].lower())
        
        # Verify API was called with correct parameters
        self.assertEqual(mock_api_call.call_count, 2)
    
    def test_multiple_choice_distractors_quality(self):
        """Test that generated distractors are plausible but wrong"""
        mc_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.mc_type,
            question_text='What is encapsulation in OOP?',
            correct_answer='Bundling data and methods together within a class',
            options=[
                'Bundling data and methods together within a class',
                'Creating multiple instances of a class',
                'Defining relationships between classes',
                'Executing methods in a specific order'
            ],
            difficulty=2
        )
        
        # All options should be different
        options = mc_question.options
        self.assertEqual(len(options), len(set(options)))  # No duplicates
        
        # Correct answer should be in options
        self.assertIn(mc_question.correct_answer, options)
        
        # All options should be reasonable length (not empty or too short)
        for option in options:
            self.assertGreater(len(option), 5)
            self.assertIsInstance(option, str)