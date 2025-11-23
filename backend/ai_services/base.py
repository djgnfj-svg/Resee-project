"""
모든 AI 서비스의 공통 기능을 제공하는 기본 AI 서비스

제공 기능:
- API 키 검증
- LangChain/Anthropic SDK 초기화
- JSON 파싱 유틸리티
- 에러 처리
- 로깅
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import anthropic
from django.conf import settings
from langchain_anthropic import ChatAnthropic

logger = logging.getLogger(__name__)


class BaseAIService(ABC):
    """
    Anthropic Claude를 사용하는 모든 AI 서비스의 기본 클래스

    공통 초기화, 검증, 유틸리티 메서드를 제공합니다.
    """

    def __init__(
        self, model: str = "claude-3-haiku-20240307", use_langchain: bool = True
    ):
        """
        AI 서비스를 초기화합니다.

        Args:
            model: 사용할 Claude 모델
            use_langchain: True이면 LangChain 사용, 아니면 Anthropic SDK 사용
        """
        self.model = model
        self.use_langchain = use_langchain
        self.client = None
        self.llm = None
        self._initialize()

    def _initialize(self):
        """API 클라이언트를 초기화합니다."""
        api_key = self._get_api_key()

        if not api_key:
            logger.warning(
                f"{self.__class__.__name__}: ANTHROPIC_API_KEY가 설정되지 않았습니다"
            )
            return

        if not self._validate_api_key(api_key):
            logger.error(f"{self.__class__.__name__}: 잘못된 ANTHROPIC_API_KEY 형식")
            return

        try:
            if self.use_langchain:
                self.llm = ChatAnthropic(
                    model=self.model,
                    temperature=self._get_temperature(),
                    max_tokens=self._get_max_tokens(),
                    api_key=api_key,
                )
                logger.info(
                    f"{self.__class__.__name__}: LangChain client initialized (model: {self.model})"
                )
            else:
                self.client = anthropic.Anthropic(api_key=api_key)
                logger.info(
                    f"{self.__class__.__name__}: Anthropic SDK client initialized (model: {self.model})"
                )
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: Failed to initialize client: {e}")

    def _get_api_key(self) -> Optional[str]:
        """설정에서 Anthropic API 키를 가져옵니다."""
        return getattr(settings, "ANTHROPIC_API_KEY", None)

    def _validate_api_key(self, api_key: str) -> bool:
        """API 키 형식을 검증합니다."""
        return api_key.startswith("sk-ant-api") and len(api_key) >= 20

    def is_available(self) -> bool:
        """AI 서비스가 사용 가능한지 확인합니다."""
        return (self.llm is not None) or (self.client is not None)

    @abstractmethod
    def _get_temperature(self) -> float:
        """이 서비스의 temperature 값을 반환합니다. 하위 클래스에서 구현해야 합니다."""

    @abstractmethod
    def _get_max_tokens(self) -> int:
        """이 서비스의 max_tokens 값을 반환합니다. 하위 클래스에서 구현해야 합니다."""

    def parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        AI 응답에서 JSON 객체를 추출하여 파싱합니다.

        중괄호 카운팅을 사용하여 완전한 JSON 객체를 찾습니다.
        코드 블록(```json, ```)을 처리합니다.

        Args:
            response_text: 원본 AI 응답 텍스트

        Returns:
            파싱된 JSON dict 또는 파싱 실패 시 None
        """
        try:
            text = response_text.strip()

            # 코드 블록 제거
            if text.startswith("```json"):
                text = text[7:].strip()
                if "```" in text:
                    text = text[: text.index("```")].strip()
            elif text.startswith("```"):
                text = text[3:].strip()
                if "```" in text:
                    text = text[: text.index("```")].strip()

            # 중괄호 카운팅으로 JSON 객체 경계 찾기
            if text.startswith("{"):
                brace_count = 0
                for i, char in enumerate(text):
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            text = text[: i + 1]
                            break

            result = json.loads(text)
            return result

        except json.JSONDecodeError as e:
            logger.error(f"{self.__class__.__name__}: JSON parsing failed: {e}")
            logger.error(f"Raw AI response: {response_text[:1000]}")
            return None
        except Exception as e:
            logger.error(
                f"{self.__class__.__name__}: Response parsing failed: {e}",
                exc_info=True,
            )
            return None

    def validate_required_fields(
        self, data: Dict[str, Any], required_fields: list
    ) -> bool:
        """
        데이터에 모든 필수 필드가 있는지 검증합니다.

        Args:
            data: 검증할 데이터 딕셔너리
            required_fields: 필수 필드 이름 리스트

        Returns:
            모든 필드가 있으면 True, 그렇지 않으면 False
        """
        missing = [field for field in required_fields if field not in data]

        if missing:
            logger.warning(
                f"{self.__class__.__name__}: Missing required fields: {missing}"
            )
            return False

        return True

    def call_langchain(self, prompt_template, **kwargs) -> Optional[str]:
        """
        프롬프트 템플릿으로 LangChain을 호출합니다.

        Args:
            prompt_template: ChatPromptTemplate 인스턴스
            **kwargs: 프롬프트 템플릿 변수

        Returns:
            응답 텍스트 또는 호출 실패 시 None
        """
        if not self.llm:
            logger.warning(f"{self.__class__.__name__}: LangChain not initialized")
            return None

        try:
            response = self.llm.invoke(prompt_template.format(**kwargs))
            return response.content if response else None
        except Exception as e:
            logger.error(
                f"{self.__class__.__name__}: LangChain call failed: {e}", exc_info=True
            )
            return None

    def call_anthropic(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """
        프롬프트로 Anthropic SDK를 호출합니다.

        Args:
            prompt: 프롬프트 텍스트
            temperature: 기본 temperature 값 오버라이드
            max_tokens: 기본 max_tokens 값 오버라이드

        Returns:
            응답 텍스트 또는 호출 실패 시 None
        """
        if not self.client:
            logger.warning(f"{self.__class__.__name__}: Anthropic SDK not initialized")
            return None

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self._get_max_tokens(),
                temperature=temperature or self._get_temperature(),
                messages=[{"role": "user", "content": prompt}],
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
            logger.error(
                f"{self.__class__.__name__}: API call failed: {e}", exc_info=True
            )
            return None
