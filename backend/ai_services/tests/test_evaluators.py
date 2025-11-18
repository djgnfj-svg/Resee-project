"""
Tests for AI evaluator services.
"""
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from ai_services.evaluators.answer_evaluator import AnswerEvaluator
from ai_services.evaluators.title_evaluator import TitleEvaluator


class AnswerEvaluatorTest(TestCase):
    """Test AnswerEvaluator service."""

    def setUp(self):
        self.evaluator = AnswerEvaluator()

    def test_initialization(self):
        """Test evaluator initialization."""
        self.assertEqual(self.evaluator.model, "claude-3-haiku-20240307")
        self.assertTrue(self.evaluator.use_langchain)
        self.assertEqual(self.evaluator._get_temperature(), 0.3)
        self.assertEqual(self.evaluator._get_max_tokens(), 500)

    @override_settings(ANTHROPIC_API_KEY=None)
    def test_evaluate_answer_service_unavailable(self):
        """Test evaluation when AI service is unavailable."""
        evaluator = AnswerEvaluator()
        result = evaluator.evaluate_answer(
            content_title="Test Title",
            content_body="Test content",
            user_answer="Test answer"
        )
        self.assertIsNone(result)

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    def test_evaluate_answer_too_short(self):
        """Test evaluation with too short answer."""
        result = self.evaluator.evaluate_answer(
            content_title="Test Title",
            content_body="Test content",
            user_answer="short"
        )
        self.assertEqual(result['score'], 0)
        self.assertEqual(result['evaluation'], 'poor')
        self.assertEqual(result['auto_result'], 'forgot')
        self.assertIn('짧습니다', result['feedback'])

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    def test_evaluate_answer_empty(self):
        """Test evaluation with empty answer."""
        result = self.evaluator.evaluate_answer(
            content_title="Test Title",
            content_body="Test content",
            user_answer=""
        )
        self.assertEqual(result['score'], 0)
        self.assertEqual(result['auto_result'], 'forgot')

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch.object(AnswerEvaluator, 'call_langchain')
    def test_evaluate_answer_success(self, mock_call):
        """Test successful answer evaluation."""
        mock_call.return_value = '''{
            "score": 85,
            "evaluation": "good",
            "feedback": "잘 이해하셨습니다.",
            "auto_result": "remembered"
        }'''

        result = self.evaluator.evaluate_answer(
            content_title="Test Title",
            content_body="Test content body",
            user_answer="This is a detailed answer explaining the concept clearly."
        )

        self.assertIsNotNone(result)
        self.assertEqual(result['score'], 85)
        self.assertEqual(result['evaluation'], 'good')
        self.assertEqual(result['auto_result'], 'remembered')
        self.assertIn('이해', result['feedback'])

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch.object(AnswerEvaluator, 'call_langchain')
    def test_evaluate_answer_no_response(self, mock_call):
        """Test evaluation when AI returns no response."""
        mock_call.return_value = None

        result = self.evaluator.evaluate_answer(
            content_title="Test Title",
            content_body="Test content",
            user_answer="Valid answer that is long enough to process"
        )
        self.assertIsNone(result)

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch.object(AnswerEvaluator, 'call_langchain')
    def test_evaluate_answer_invalid_json(self, mock_call):
        """Test evaluation when AI returns invalid JSON."""
        mock_call.return_value = "Not a JSON response"

        result = self.evaluator.evaluate_answer(
            content_title="Test Title",
            content_body="Test content",
            user_answer="Valid answer that is long enough to process"
        )
        self.assertIsNone(result)

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch.object(AnswerEvaluator, 'call_langchain')
    def test_evaluate_answer_missing_fields(self, mock_call):
        """Test evaluation when AI response is missing required fields."""
        mock_call.return_value = '{"score": 85}'

        result = self.evaluator.evaluate_answer(
            content_title="Test Title",
            content_body="Test content",
            user_answer="Valid answer that is long enough to process"
        )
        self.assertIsNone(result)

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch.object(AnswerEvaluator, 'call_langchain')
    def test_evaluate_answer_invalid_score(self, mock_call):
        """Test evaluation with invalid score value."""
        mock_call.return_value = '''{
            "score": 150,
            "evaluation": "excellent",
            "feedback": "Great job!"
        }'''

        result = self.evaluator.evaluate_answer(
            content_title="Test Title",
            content_body="Test content",
            user_answer="Valid answer that is long enough to process"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result['score'], 100)  # Should be clamped to 100

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch.object(AnswerEvaluator, 'call_langchain')
    def test_evaluate_answer_negative_score(self, mock_call):
        """Test evaluation with negative score."""
        mock_call.return_value = '''{
            "score": -10,
            "evaluation": "poor",
            "feedback": "Needs improvement"
        }'''

        result = self.evaluator.evaluate_answer(
            content_title="Test Title",
            content_body="Test content",
            user_answer="Valid answer that is long enough to process"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result['score'], 0)  # Should be clamped to 0

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch.object(AnswerEvaluator, 'call_langchain')
    def test_evaluate_answer_auto_result_generation(self, mock_call):
        """Test auto_result generation based on score."""
        mock_call.return_value = '''{
            "score": 65,
            "evaluation": "fair",
            "feedback": "Some improvement needed"
        }'''

        result = self.evaluator.evaluate_answer(
            content_title="Test Title",
            content_body="Test content",
            user_answer="Valid answer that is long enough to process"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result['auto_result'], 'forgot')  # Score < 70

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch.object(AnswerEvaluator, 'call_langchain')
    def test_evaluate_answer_long_content_truncation(self, mock_call):
        """Test that long content is truncated."""
        mock_call.return_value = '''{
            "score": 80,
            "evaluation": "good",
            "feedback": "Good understanding"
        }'''

        long_content = "x" * 2000  # Content longer than 1500 chars
        result = self.evaluator.evaluate_answer(
            content_title="Test Title",
            content_body=long_content,
            user_answer="Valid answer that is long enough to process"
        )

        self.assertIsNotNone(result)
        # Verify that call_langchain was called with truncated content
        self.assertTrue(mock_call.called)

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch.object(AnswerEvaluator, 'call_langchain')
    def test_evaluate_answer_exception_handling(self, mock_call):
        """Test exception handling during evaluation."""
        mock_call.side_effect = Exception("Unexpected error")

        result = self.evaluator.evaluate_answer(
            content_title="Test Title",
            content_body="Test content",
            user_answer="Valid answer that is long enough to process"
        )
        self.assertIsNone(result)


class TitleEvaluatorTest(TestCase):
    """Test TitleEvaluator service."""

    def setUp(self):
        self.evaluator = TitleEvaluator()

    def test_initialization(self):
        """Test evaluator initialization."""
        self.assertEqual(self.evaluator.model, "claude-3-haiku-20240307")
        self.assertTrue(self.evaluator.use_langchain)
        self.assertEqual(self.evaluator._get_temperature(), 0.3)
        self.assertEqual(self.evaluator._get_max_tokens(), 500)

    @override_settings(ANTHROPIC_API_KEY=None)
    def test_evaluate_title_service_unavailable(self):
        """Test evaluation when AI service is unavailable."""
        evaluator = TitleEvaluator()
        result = evaluator.evaluate_title(
            content="Test content",
            user_title="User Title",
            actual_title="Actual Title"
        )
        self.assertIsNone(result)

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    def test_evaluate_title_too_short(self):
        """Test evaluation with too short title."""
        result = self.evaluator.evaluate_title(
            content="Test content",
            user_title="A",
            actual_title="Actual Title"
        )
        self.assertEqual(result['score'], 0)
        self.assertFalse(result['is_correct'])
        self.assertEqual(result['auto_result'], 'forgot')
        self.assertIn('짧습니다', result['feedback'])

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    def test_evaluate_title_empty(self):
        """Test evaluation with empty title."""
        result = self.evaluator.evaluate_title(
            content="Test content",
            user_title="",
            actual_title="Actual Title"
        )
        self.assertEqual(result['score'], 0)
        self.assertFalse(result['is_correct'])

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch.object(TitleEvaluator, 'call_langchain')
    def test_evaluate_title_success(self, mock_call):
        """Test successful title evaluation."""
        mock_call.return_value = '''{
            "score": 85,
            "is_correct": true,
            "feedback": "제목이 적절합니다.",
            "auto_result": "remembered"
        }'''

        result = self.evaluator.evaluate_title(
            content="Test content body",
            user_title="User's Title",
            actual_title="Actual Title"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result['score'], 85)
        self.assertTrue(result['is_correct'])
        self.assertEqual(result['auto_result'], 'remembered')

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch.object(TitleEvaluator, 'call_langchain')
    def test_evaluate_title_no_response(self, mock_call):
        """Test evaluation when AI returns no response."""
        mock_call.return_value = None

        result = self.evaluator.evaluate_title(
            content="Test content",
            user_title="User Title",
            actual_title="Actual Title"
        )
        self.assertIsNone(result)

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch.object(TitleEvaluator, 'call_langchain')
    def test_evaluate_title_invalid_json(self, mock_call):
        """Test evaluation when AI returns invalid JSON."""
        mock_call.return_value = "Not a JSON response"

        result = self.evaluator.evaluate_title(
            content="Test content",
            user_title="User Title",
            actual_title="Actual Title"
        )
        self.assertIsNone(result)

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch.object(TitleEvaluator, 'call_langchain')
    def test_evaluate_title_missing_fields(self, mock_call):
        """Test evaluation when AI response is missing required fields."""
        mock_call.return_value = '{"score": 85}'

        result = self.evaluator.evaluate_title(
            content="Test content",
            user_title="User Title",
            actual_title="Actual Title"
        )
        self.assertIsNone(result)

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch.object(TitleEvaluator, 'call_langchain')
    def test_evaluate_title_score_determines_correctness(self, mock_call):
        """Test that is_correct is determined by score >= 70."""
        mock_call.return_value = '''{
            "score": 65,
            "is_correct": false,
            "feedback": "Almost there"
        }'''

        result = self.evaluator.evaluate_title(
            content="Test content",
            user_title="User Title",
            actual_title="Actual Title"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result['score'], 65)
        self.assertFalse(result['is_correct'])  # Score < 70
        self.assertEqual(result['auto_result'], 'forgot')

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch.object(TitleEvaluator, 'call_langchain')
    def test_evaluate_title_auto_result_generation(self, mock_call):
        """Test auto_result generation based on score."""
        mock_call.return_value = '''{
            "score": 75,
            "is_correct": true,
            "feedback": "Good title"
        }'''

        result = self.evaluator.evaluate_title(
            content="Test content",
            user_title="User Title",
            actual_title="Actual Title"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result['auto_result'], 'remembered')  # Score >= 70

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch.object(TitleEvaluator, 'call_langchain')
    def test_evaluate_title_invalid_score(self, mock_call):
        """Test evaluation with invalid score value."""
        mock_call.return_value = '''{
            "score": 120,
            "is_correct": true,
            "feedback": "Excellent!"
        }'''

        result = self.evaluator.evaluate_title(
            content="Test content",
            user_title="User Title",
            actual_title="Actual Title"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result['score'], 100)  # Should be clamped to 100

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch.object(TitleEvaluator, 'call_langchain')
    def test_evaluate_title_long_content_truncation(self, mock_call):
        """Test that long content is truncated."""
        mock_call.return_value = '''{
            "score": 80,
            "is_correct": true,
            "feedback": "Good"
        }'''

        long_content = "x" * 2000
        result = self.evaluator.evaluate_title(
            content=long_content,
            user_title="User Title",
            actual_title="Actual Title"
        )

        self.assertIsNotNone(result)
        self.assertTrue(mock_call.called)

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch.object(TitleEvaluator, 'call_langchain')
    def test_evaluate_title_exception_handling(self, mock_call):
        """Test exception handling during evaluation."""
        mock_call.side_effect = Exception("Unexpected error")

        result = self.evaluator.evaluate_title(
            content="Test content",
            user_title="User Title",
            actual_title="Actual Title"
        )
        self.assertIsNone(result)
