"""
Tests for BaseAIService.
"""
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from ai_services.base import BaseAIService


class MockAIService(BaseAIService):
    """Mock AI service for testing."""

    def _get_temperature(self) -> float:
        return 0.5

    def _get_max_tokens(self) -> int:
        return 1000


class BaseAIServiceTest(TestCase):
    """Test BaseAIService initialization and utilities."""

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    def test_initialization_with_valid_key(self):
        """Test service initialization with valid API key."""
        service = MockAIService()
        self.assertTrue(service.is_available())

    @override_settings(ANTHROPIC_API_KEY=None)
    def test_initialization_without_api_key(self):
        """Test service initialization without API key."""
        service = MockAIService()
        self.assertFalse(service.is_available())

    @override_settings(ANTHROPIC_API_KEY='invalid-key')
    def test_initialization_with_invalid_key_format(self):
        """Test service initialization with invalid API key format."""
        service = MockAIService()
        self.assertFalse(service.is_available())

    def test_validate_api_key_valid(self):
        """Test API key validation with valid key."""
        service = MockAIService()
        self.assertTrue(service._validate_api_key('sk-ant-api03-test-key-1234567890'))

    def test_validate_api_key_invalid_prefix(self):
        """Test API key validation with invalid prefix."""
        service = MockAIService()
        self.assertFalse(service._validate_api_key('invalid-key-1234567890'))

    def test_validate_api_key_too_short(self):
        """Test API key validation with too short key."""
        service = MockAIService()
        self.assertFalse(service._validate_api_key('sk-ant-api'))

    def test_parse_json_response_simple(self):
        """Test parsing simple JSON response."""
        service = MockAIService()
        response = '{"score": 85, "feedback": "Good job"}'
        result = service.parse_json_response(response)
        self.assertEqual(result['score'], 85)
        self.assertEqual(result['feedback'], "Good job")

    def test_parse_json_response_with_code_block(self):
        """Test parsing JSON response wrapped in code blocks."""
        service = MockAIService()
        response = '```json\n{"score": 85}\n```'
        result = service.parse_json_response(response)
        self.assertEqual(result['score'], 85)

    def test_parse_json_response_with_generic_code_block(self):
        """Test parsing JSON response with generic code block."""
        service = MockAIService()
        response = '```\n{"score": 85}\n```'
        result = service.parse_json_response(response)
        self.assertEqual(result['score'], 85)

    def test_parse_json_response_with_trailing_text(self):
        """Test parsing JSON response with trailing text."""
        service = MockAIService()
        response = '{"score": 85} extra text here'
        result = service.parse_json_response(response)
        self.assertEqual(result['score'], 85)

    def test_parse_json_response_nested_braces(self):
        """Test parsing JSON response with nested objects."""
        service = MockAIService()
        response = '{"data": {"score": 85, "details": {"level": "good"}}}'
        result = service.parse_json_response(response)
        self.assertEqual(result['data']['score'], 85)
        self.assertEqual(result['data']['details']['level'], "good")

    def test_parse_json_response_invalid(self):
        """Test parsing invalid JSON response."""
        service = MockAIService()
        response = 'not a json response'
        result = service.parse_json_response(response)
        self.assertIsNone(result)

    def test_parse_json_response_malformed(self):
        """Test parsing malformed JSON response."""
        service = MockAIService()
        response = '{"score": 85'
        result = service.parse_json_response(response)
        self.assertIsNone(result)

    def test_validate_required_fields_all_present(self):
        """Test field validation with all required fields present."""
        service = MockAIService()
        data = {"score": 85, "feedback": "Good", "evaluation": "excellent"}
        required = ["score", "feedback", "evaluation"]
        self.assertTrue(service.validate_required_fields(data, required))

    def test_validate_required_fields_missing(self):
        """Test field validation with missing fields."""
        service = MockAIService()
        data = {"score": 85}
        required = ["score", "feedback", "evaluation"]
        self.assertFalse(service.validate_required_fields(data, required))

    def test_validate_required_fields_empty_list(self):
        """Test field validation with empty required list."""
        service = MockAIService()
        data = {"score": 85}
        required = []
        self.assertTrue(service.validate_required_fields(data, required))

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch('ai_services.base.ChatAnthropic')
    def test_call_langchain_success(self, mock_langchain):
        """Test successful LangChain call."""
        service = MockAIService()

        # Mock LangChain response
        mock_response = Mock()
        mock_response.content = "AI response text"
        service.llm = Mock()
        service.llm.invoke.return_value = mock_response

        # Create a simple prompt template
        from langchain_core.prompts import ChatPromptTemplate
        prompt_template = ChatPromptTemplate.from_template("Test prompt: {input}")

        result = service.call_langchain(prompt_template, input="test")
        self.assertEqual(result, "AI response text")

    def test_call_langchain_not_initialized(self):
        """Test LangChain call when not initialized."""
        service = MockAIService()
        service.llm = None

        from langchain_core.prompts import ChatPromptTemplate
        prompt_template = ChatPromptTemplate.from_template("Test prompt: {input}")

        result = service.call_langchain(prompt_template, input="test")
        self.assertIsNone(result)

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    def test_call_langchain_exception(self):
        """Test LangChain call with exception."""
        service = MockAIService()
        service.llm = Mock()
        service.llm.invoke.side_effect = Exception("API error")

        from langchain_core.prompts import ChatPromptTemplate
        prompt_template = ChatPromptTemplate.from_template("Test prompt: {input}")

        result = service.call_langchain(prompt_template, input="test")
        self.assertIsNone(result)

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    @patch('ai_services.base.anthropic.Anthropic')
    def test_call_anthropic_success(self, mock_anthropic_class):
        """Test successful Anthropic SDK call."""
        service = MockAIService(use_langchain=False)

        # Mock Anthropic response
        mock_content = Mock()
        mock_content.text = "AI response text"
        mock_message = Mock()
        mock_message.content = [mock_content]

        service.client = Mock()
        service.client.messages.create.return_value = mock_message

        result = service.call_anthropic("Test prompt")
        self.assertEqual(result, "AI response text")

    def test_call_anthropic_not_initialized(self):
        """Test Anthropic SDK call when not initialized."""
        service = MockAIService(use_langchain=False)
        service.client = None

        result = service.call_anthropic("Test prompt")
        self.assertIsNone(result)

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    def test_call_anthropic_authentication_error(self):
        """Test Anthropic SDK call with authentication error."""
        import anthropic

        service = MockAIService(use_langchain=False)
        service.client = Mock()

        # Create mock response for Anthropic error
        mock_response = Mock()
        mock_response.status_code = 401
        error = anthropic.AuthenticationError(
            "Invalid API key",
            response=mock_response,
            body={"error": "Invalid API key"}
        )
        service.client.messages.create.side_effect = error

        result = service.call_anthropic("Test prompt")
        self.assertIsNone(result)

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    def test_call_anthropic_rate_limit_error(self):
        """Test Anthropic SDK call with rate limit error."""
        import anthropic

        service = MockAIService(use_langchain=False)
        service.client = Mock()

        # Create mock response for Anthropic error
        mock_response = Mock()
        mock_response.status_code = 429
        error = anthropic.RateLimitError(
            "Rate limit exceeded",
            response=mock_response,
            body={"error": "Rate limit exceeded"}
        )
        service.client.messages.create.side_effect = error

        result = service.call_anthropic("Test prompt")
        self.assertIsNone(result)

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    def test_call_anthropic_api_connection_error(self):
        """Test Anthropic SDK call with connection error."""
        import anthropic

        service = MockAIService(use_langchain=False)
        service.client = Mock()
        service.client.messages.create.side_effect = anthropic.APIConnectionError(request=Mock())

        result = service.call_anthropic("Test prompt")
        self.assertIsNone(result)

    @override_settings(ANTHROPIC_API_KEY='sk-ant-api03-test-key-1234567890')
    def test_call_anthropic_timeout_error(self):
        """Test Anthropic SDK call with timeout error."""
        import anthropic

        service = MockAIService(use_langchain=False)
        service.client = Mock()
        service.client.messages.create.side_effect = anthropic.APITimeoutError(request=Mock())

        result = service.call_anthropic("Test prompt")
        self.assertIsNone(result)

    def test_get_temperature(self):
        """Test getting temperature value."""
        service = MockAIService()
        self.assertEqual(service._get_temperature(), 0.5)

    def test_get_max_tokens(self):
        """Test getting max tokens value."""
        service = MockAIService()
        self.assertEqual(service._get_max_tokens(), 1000)
