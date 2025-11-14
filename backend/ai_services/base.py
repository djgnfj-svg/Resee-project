"""
Base AI Service with common functionality for all AI services.

Provides:
- API key validation
- LangChain/Anthropic SDK initialization
- JSON parsing utilities
- Error handling
- Logging
"""

import json
import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from django.conf import settings
from langchain_anthropic import ChatAnthropic
import anthropic

logger = logging.getLogger(__name__)


class BaseAIService(ABC):
    """
    Base class for all AI services using Anthropic Claude.

    Provides common initialization, validation, and utility methods.
    """

    def __init__(self, model: str = "claude-3-haiku-20240307", use_langchain: bool = True):
        """
        Initialize AI service.

        Args:
            model: Claude model to use
            use_langchain: If True, use LangChain; otherwise use Anthropic SDK
        """
        self.model = model
        self.use_langchain = use_langchain
        self.client = None
        self.llm = None
        self._initialize()

    def _initialize(self):
        """Initialize API client."""
        api_key = self._get_api_key()

        if not api_key:
            logger.warning(f"{self.__class__.__name__}: ANTHROPIC_API_KEY not configured")
            return

        if not self._validate_api_key(api_key):
            logger.error(f"{self.__class__.__name__}: Invalid ANTHROPIC_API_KEY format")
            return

        try:
            if self.use_langchain:
                self.llm = ChatAnthropic(
                    model=self.model,
                    temperature=self._get_temperature(),
                    max_tokens=self._get_max_tokens(),
                    api_key=api_key
                )
                logger.info(f"{self.__class__.__name__}: LangChain client initialized (model: {self.model})")
            else:
                self.client = anthropic.Anthropic(api_key=api_key)
                logger.info(f"{self.__class__.__name__}: Anthropic SDK client initialized (model: {self.model})")
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: Failed to initialize client: {e}")

    def _get_api_key(self) -> Optional[str]:
        """Get Anthropic API key from settings."""
        return getattr(settings, 'ANTHROPIC_API_KEY', None)

    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key format."""
        return api_key.startswith('sk-ant-api') and len(api_key) >= 20

    def is_available(self) -> bool:
        """Check if AI service is available."""
        return (self.llm is not None) or (self.client is not None)

    @abstractmethod
    def _get_temperature(self) -> float:
        """Get temperature for this service. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def _get_max_tokens(self) -> int:
        """Get max tokens for this service. Must be implemented by subclasses."""
        pass

    def parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse AI response to extract JSON object.

        Uses brace counting to find complete JSON objects.
        Handles code blocks (```json, ```).

        Args:
            response_text: Raw AI response text

        Returns:
            Parsed JSON dict or None if parsing fails
        """
        try:
            text = response_text.strip()

            # Remove code blocks
            if text.startswith('```json'):
                text = text[7:].strip()
                if '```' in text:
                    text = text[:text.index('```')].strip()
            elif text.startswith('```'):
                text = text[3:].strip()
                if '```' in text:
                    text = text[:text.index('```')].strip()

            # Find JSON object boundaries using brace counting
            if text.startswith('{'):
                brace_count = 0
                for i, char in enumerate(text):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            text = text[:i+1]
                            break

            result = json.loads(text)
            return result

        except json.JSONDecodeError as e:
            logger.error(f"{self.__class__.__name__}: JSON parsing failed: {e}")
            logger.error(f"Raw AI response: {response_text[:1000]}")
            return None
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: Response parsing failed: {e}", exc_info=True)
            return None

    def validate_required_fields(self, data: Dict[str, Any], required_fields: list) -> bool:
        """
        Validate that all required fields are present in data.

        Args:
            data: Data dict to validate
            required_fields: List of required field names

        Returns:
            True if all fields present, False otherwise
        """
        missing = [field for field in required_fields if field not in data]

        if missing:
            logger.warning(f"{self.__class__.__name__}: Missing required fields: {missing}")
            return False

        return True

    def call_langchain(self, prompt_template, **kwargs) -> Optional[str]:
        """
        Call LangChain with prompt template.

        Args:
            prompt_template: ChatPromptTemplate instance
            **kwargs: Variables for prompt template

        Returns:
            Response text or None if call fails
        """
        if not self.llm:
            logger.warning(f"{self.__class__.__name__}: LangChain not initialized")
            return None

        try:
            response = self.llm.invoke(prompt_template.format(**kwargs))
            return response.content if response else None
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: LangChain call failed: {e}", exc_info=True)
            return None

    def call_anthropic(self, prompt: str, temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None) -> Optional[str]:
        """
        Call Anthropic SDK with prompt.

        Args:
            prompt: Prompt text
            temperature: Override default temperature
            max_tokens: Override default max_tokens

        Returns:
            Response text or None if call fails
        """
        if not self.client:
            logger.warning(f"{self.__class__.__name__}: Anthropic SDK not initialized")
            return None

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self._get_max_tokens(),
                temperature=temperature or self._get_temperature(),
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return message.content[0].text if message.content else None

        except anthropic.AuthenticationError as e:
            logger.error(f"{self.__class__.__name__}: API authentication failed: {e}")
            return None
        except anthropic.RateLimitError as e:
            logger.warning(f"{self.__class__.__name__}: API rate limit exceeded: {e}")
            return None
        except anthropic.APIConnectionError as e:
            logger.error(f"{self.__class__.__name__}: API connection failed: {e}")
            return None
        except anthropic.APITimeoutError as e:
            logger.warning(f"{self.__class__.__name__}: API timeout: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: API call failed: {e}", exc_info=True)
            return None
