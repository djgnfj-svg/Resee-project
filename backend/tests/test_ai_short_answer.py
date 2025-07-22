"""
Tests for AI Short Answer Question Generation and Evaluation
"""
import json
from unittest.mock import patch, Mock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from content.models import Content, Category
from ai_review.models import AIQuestionType, AIQuestion, AIEvaluation
from ai_review.services import ai_service, AIServiceError

# Test cache settings to avoid Redis dependency
TEST_CACHE_SETTINGS = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

User = get_user_model()


@override_settings(CACHES=TEST_CACHE_SETTINGS)
class AIShortAnswerTestCase(TestCase):
    """Test short answer question generation and evaluation"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        
        # Create test content about machine learning
        self.category = Category.objects.create(
            name='Machine Learning',
            user=self.user
        )
        self.content = Content.objects.create(
            title='Introduction to Neural Networks',
            content='''
            Neural networks are computational models inspired by biological neural networks.
            They consist of interconnected nodes (neurons) organized in layers.
            A typical neural network has an input layer, one or more hidden layers, and an output layer.
            Each connection has a weight that determines the strength of the signal.
            Training involves adjusting these weights through backpropagation and gradient descent.
            Activation functions like ReLU, sigmoid, and tanh introduce non-linearity.
            Deep neural networks with many layers are called deep learning models.
            Common applications include image recognition, natural language processing, and predictive analytics.
            ''',
            category=self.category,
            author=self.user
        )
        
        # Get or create short answer question type
        self.sa_type, _ = AIQuestionType.objects.get_or_create(
            name='short_answer',
            defaults={
                'display_name': 'Short Answer',
                'description': 'Generate open-ended questions requiring text responses',
                'is_active': True
            }
        )
    
    def test_short_answer_question_creation(self):
        """Test creating short answer questions manually"""
        sa_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.sa_type,
            question_text='Explain the purpose of activation functions in neural networks.',
            correct_answer='Activation functions introduce non-linearity to neural networks, allowing them to learn complex patterns and relationships. They determine whether a neuron should be activated based on the weighted input, enabling the network to approximate non-linear functions.',
            difficulty=3,
            explanation='This question tests understanding of a key concept in neural network architecture.',
            keywords=['activation function', 'non-linearity', 'neural networks']
        )
        
        self.assertEqual(sa_question.question_type.name, 'short_answer')
        self.assertIsNone(sa_question.options)  # Short answer questions don't have options
        self.assertTrue(sa_question.is_active)
        self.assertIn('activation', sa_question.question_text.lower())
    
    @patch.object(ai_service, '_make_api_call')
    def test_ai_short_answer_generation(self, mock_api_call):
        """Test AI-generated short answer questions"""
        # Mock AI response
        mock_response = json.dumps({
            "questions": [
                {
                    "question_type": "short_answer",
                    "question_text": "Describe the process of backpropagation in neural network training.",
                    "correct_answer": "Backpropagation is a learning algorithm that calculates gradients by propagating errors backward through the network layers. It computes the partial derivatives of the loss function with respect to each weight, allowing the network to adjust weights in the direction that minimizes the error.",
                    "explanation": "This question tests understanding of the fundamental training mechanism in neural networks.",
                    "keywords": ["backpropagation", "gradients", "training", "weights", "error"]
                }
            ]
        })
        
        mock_api_call.return_value = (mock_response, 1800)
        
        # Generate short answer questions
        questions = ai_service.generate_questions(
            content=self.content,
            question_types=['short_answer'],
            difficulty=3,
            count=1
        )
        
        self.assertEqual(len(questions), 1)
        question = questions[0]
        
        self.assertEqual(question['question_type'], 'short_answer')
        self.assertIn('question_text', question)
        self.assertIn('correct_answer', question)
        self.assertNotIn('options', question)  # Short answers don't have options
        self.assertIn('explanation', question)
        self.assertIn('keywords', question)
        self.assertIn('backpropagation', question['question_text'].lower())
    
    def test_short_answer_evaluation_exact_match(self):
        """Test evaluation of short answers that exactly match"""
        sa_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.sa_type,
            question_text='What does ReLU stand for?',
            correct_answer='Rectified Linear Unit',
            difficulty=1
        )
        
        # Test exact match (should score very high)
        with patch.object(ai_service, '_make_api_call') as mock_call:
            mock_response = json.dumps({
                "score": 1.0,
                "feedback": "Perfect! You provided the exact correct answer.",
                "similarity_score": 1.0,
                "evaluation_details": {
                    "strengths": ["Exact match with correct answer"],
                    "weaknesses": [],
                    "suggestions": []
                }
            })
            mock_call.return_value = (mock_response, 600)
            
            evaluation = ai_service.evaluate_answer(sa_question, 'Rectified Linear Unit')
            self.assertEqual(evaluation['score'], 1.0)
            self.assertEqual(evaluation['similarity_score'], 1.0)
    
    def test_short_answer_evaluation_semantic_match(self):
        """Test evaluation of semantically similar short answers"""
        sa_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.sa_type,
            question_text='What is the purpose of hidden layers in neural networks?',
            correct_answer='Hidden layers extract and learn features from input data, enabling the network to recognize complex patterns and relationships.',
            difficulty=2
        )
        
        # Test semantically similar answer (should score well)
        with patch.object(ai_service, '_make_api_call') as mock_call:
            mock_response = json.dumps({
                "score": 0.85,
                "feedback": "Good answer! You correctly identified that hidden layers learn features and patterns. You could be more specific about how they extract features from input data.",
                "similarity_score": 0.88,
                "evaluation_details": {
                    "strengths": ["Correctly identified feature learning", "Mentioned pattern recognition"],
                    "weaknesses": ["Could be more specific about feature extraction"],
                    "suggestions": ["Explain how features are extracted from input data"]
                }
            })
            mock_call.return_value = (mock_response, 900)
            
            user_answer = "Hidden layers learn patterns and features that help the network understand the data better."
            evaluation = ai_service.evaluate_answer(sa_question, user_answer)
            
            self.assertGreater(evaluation['score'], 0.8)
            self.assertGreater(evaluation['similarity_score'], 0.8)
            self.assertIn('feature', evaluation['feedback'].lower())
    
    def test_short_answer_evaluation_partial_understanding(self):
        """Test evaluation of answers with partial understanding"""
        sa_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.sa_type,
            question_text='Explain gradient descent in neural network training.',
            correct_answer='Gradient descent is an optimization algorithm that iteratively adjusts network weights by moving in the direction opposite to the gradient of the loss function, minimizing the error.',
            difficulty=4
        )
        
        # Test partially correct answer
        with patch.object(ai_service, '_make_api_call') as mock_call:
            mock_response = json.dumps({
                "score": 0.6,
                "feedback": "You have a basic understanding. Gradient descent does adjust weights, but you're missing key details about how it uses gradients and the direction of movement.",
                "similarity_score": 0.65,
                "evaluation_details": {
                    "strengths": ["Correctly identified weight adjustment"],
                    "weaknesses": ["Missing gradient concept", "No mention of loss function"],
                    "suggestions": ["Explain what gradients are", "Describe the direction of weight updates"]
                }
            })
            mock_call.return_value = (mock_response, 1100)
            
            user_answer = "Gradient descent changes the weights to make the network better."
            evaluation = ai_service.evaluate_answer(sa_question, user_answer)
            
            self.assertGreater(evaluation['score'], 0.5)
            self.assertLess(evaluation['score'], 0.8)
            self.assertIn('gradient', evaluation['feedback'].lower())
    
    def test_short_answer_evaluation_incorrect_answer(self):
        """Test evaluation of incorrect short answers"""
        sa_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.sa_type,
            question_text='What is the main difference between supervised and unsupervised learning?',
            correct_answer='Supervised learning uses labeled training data to learn input-output mappings, while unsupervised learning finds patterns in unlabeled data without target outputs.',
            difficulty=2
        )
        
        # Test incorrect answer
        with patch.object(ai_service, '_make_api_call') as mock_call:
            mock_response = json.dumps({
                "score": 0.1,
                "feedback": "This answer is incorrect. You're describing neural network architecture rather than learning paradigms. Supervised learning uses labeled data, while unsupervised learning works with unlabeled data.",
                "similarity_score": 0.15,
                "evaluation_details": {
                    "strengths": [],
                    "weaknesses": ["Confused learning paradigms with network architecture"],
                    "suggestions": ["Review the difference between labeled and unlabeled data", "Study supervised vs unsupervised learning examples"]
                }
            })
            mock_call.return_value = (mock_response, 800)
            
            user_answer = "Supervised learning has more layers than unsupervised learning."
            evaluation = ai_service.evaluate_answer(sa_question, user_answer)
            
            self.assertLess(evaluation['score'], 0.3)
            self.assertLess(evaluation['similarity_score'], 0.4)
            self.assertIn('incorrect', evaluation['feedback'].lower())
    
    @patch.object(ai_service, '_make_api_call')
    def test_short_answer_generation_with_difficulty_progression(self, mock_api_call):
        """Test generating short answer questions with increasing difficulty"""
        # Easy question (difficulty 1)
        easy_response = json.dumps({
            "questions": [
                {
                    "question_type": "short_answer",
                    "question_text": "What is a neural network?",
                    "correct_answer": "A neural network is a computational model inspired by biological neural networks, consisting of interconnected nodes that process information.",
                    "explanation": "This is a basic definition question suitable for beginners.",
                    "keywords": ["neural network", "definition", "nodes"]
                }
            ]
        })
        
        # Hard question (difficulty 5)
        hard_response = json.dumps({
            "questions": [
                {
                    "question_type": "short_answer",
                    "question_text": "Analyze the vanishing gradient problem in deep neural networks and propose potential solutions.",
                    "correct_answer": "The vanishing gradient problem occurs when gradients become exponentially smaller as they propagate backward through deep networks, making it difficult to train early layers. Solutions include using ReLU activations, skip connections (ResNet), proper weight initialization (Xavier/He), batch normalization, and LSTM/GRU for sequential data.",
                    "explanation": "This advanced question requires deep understanding of training challenges and modern solutions.",
                    "keywords": ["vanishing gradient", "deep networks", "ReLU", "ResNet", "batch normalization"]
                }
            ]
        })
        
        # Test easy question generation
        mock_api_call.return_value = (easy_response, 1000)
        easy_questions = ai_service.generate_questions(
            content=self.content,
            question_types=['short_answer'],
            difficulty=1,
            count=1
        )
        
        self.assertEqual(len(easy_questions), 1)
        self.assertIn('what is', easy_questions[0]['question_text'].lower())
        
        # Test hard question generation
        mock_api_call.return_value = (hard_response, 2000)
        hard_questions = ai_service.generate_questions(
            content=self.content,
            question_types=['short_answer'],
            difficulty=5,
            count=1
        )
        
        self.assertEqual(len(hard_questions), 1)
        self.assertIn('analyze', hard_questions[0]['question_text'].lower())
        
        # Verify both API calls were made
        self.assertEqual(mock_api_call.call_count, 2)
    
    def test_short_answer_evaluation_with_keywords(self):
        """Test that evaluation considers keyword presence"""
        sa_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.sa_type,
            question_text='List three common activation functions used in neural networks.',
            correct_answer='Three common activation functions are ReLU (Rectified Linear Unit), sigmoid, and tanh (hyperbolic tangent).',
            keywords=['ReLU', 'sigmoid', 'tanh', 'activation functions'],
            difficulty=2
        )
        
        # Answer with correct keywords should score well
        with patch.object(ai_service, '_make_api_call') as mock_call:
            mock_response = json.dumps({
                "score": 0.9,
                "feedback": "Excellent! You correctly identified all three major activation functions: ReLU, sigmoid, and tanh.",
                "similarity_score": 0.92,
                "evaluation_details": {
                    "strengths": ["Listed all three activation functions", "Correctly named ReLU, sigmoid, tanh"],
                    "weaknesses": [],
                    "suggestions": ["Could provide brief explanation of each function"]
                }
            })
            mock_call.return_value = (mock_response, 700)
            
            user_answer = "ReLU, sigmoid, and tanh are three common activation functions."
            evaluation = ai_service.evaluate_answer(sa_question, user_answer)
            
            self.assertGreater(evaluation['score'], 0.85)
            self.assertIn('relu', evaluation['feedback'].lower())
            self.assertIn('sigmoid', evaluation['feedback'].lower())
    
    def test_short_answer_persistence(self):
        """Test that short answer evaluations are properly saved"""
        sa_question = AIQuestion.objects.create(
            content=self.content,
            question_type=self.sa_type,
            question_text='Define overfitting in machine learning.',
            correct_answer='Overfitting occurs when a model learns the training data too well, including noise and random fluctuations, resulting in poor generalization to new, unseen data.',
            difficulty=3
        )
        
        # Create evaluation directly
        evaluation = AIEvaluation.objects.create(
            question=sa_question,
            user=self.user,
            user_answer='Overfitting is when the model memorizes the training data and performs poorly on new data.',
            ai_score=0.75,
            feedback='Good basic understanding. You correctly identified the core concept of poor generalization.',
            similarity_score=0.80,
            evaluation_details={
                'strengths': ['Understood generalization problem'],
                'weaknesses': ['Could mention memorization vs learning'],
                'suggestions': ['Explain the difference between fitting patterns vs memorizing data']
            }
        )
        
        # Verify evaluation was saved correctly
        saved_evaluation = AIEvaluation.objects.get(id=evaluation.id)
        self.assertEqual(saved_evaluation.question, sa_question)
        self.assertEqual(saved_evaluation.user, self.user)
        self.assertEqual(saved_evaluation.ai_score, 0.75)
        self.assertIn('overfitting', saved_evaluation.user_answer.lower())
        self.assertIsInstance(saved_evaluation.evaluation_details, dict)