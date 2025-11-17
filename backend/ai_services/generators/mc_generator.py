"""
AI-powered multiple choice options generator.

Generates 4-choice quiz options based on content.
User sees content and chooses correct title from 4 options.

Uses Claude 3 Haiku for fast and cost-efficient generation.
"""

import logging
from typing import Dict, Optional

from langchain_core.prompts import ChatPromptTemplate

from ai_services.base import BaseAIService

logger = logging.getLogger(__name__)


class MCGenerator(BaseAIService):
    """
    Generates multiple choice options based on content.

    Creates 4 options including the correct title and 3 plausible distractors.
    """

    def __init__(self):
        # Use Claude 3 Haiku for fast generation
        super().__init__(
            model="claude-3-haiku-20240307",
            use_langchain=True
        )

    def _get_temperature(self) -> float:
        # Higher temperature for creative wrong options
        return 0.7

    def _get_max_tokens(self) -> int:
        return 500

    def generate_multiple_choice_options(
        self,
        title: str,
        content: str
    ) -> Optional[Dict]:
        """
        Generate multiple choice options based on content.

        Args:
            title: Correct title (answer)
            content: Content body (markdown)

        Returns:
            {
                "choices": ["제목1", "제목2", "제목3", "제목4"],
                "correct_answer": "제목1"  # Same as title parameter
            }
            or None if generation fails
        """
        if not self.is_available():
            logger.warning("AI service not available")
            return None

        try:
            prompt_template = self._create_generation_prompt()
            response_text = self.call_langchain(
                prompt_template,
                title=title,
                content=content[:1500] + ("..." if len(content) > 1500 else "")
            )

            if not response_text:
                logger.warning(f"No response from AI for MC generation: {title}")
                return None

            result = self.parse_json_response(response_text)
            if not result:
                return None

            # Validate structure
            if not self._validate_mc_response(result, title):
                return None

            logger.info(f"Successfully generated MC options for: {title}")
            return result

        except Exception as e:
            logger.error(
                f"Failed to generate MC options for '{title[:50]}...': {e}",
                exc_info=True
            )
            return None

    def _create_generation_prompt(self) -> ChatPromptTemplate:
        """Create MC generation prompt template."""
        return ChatPromptTemplate.from_template("""당신은 학습 콘텐츠 기반 객관식 문제 생성 전문가입니다.

다음 학습 콘텐츠의 **내용**을 읽고, 가장 적합한 **제목**을 맞추는 4지선다 문제를 만들어주세요.

**정답 제목**: {title}

**콘텐츠 내용**:
{content}

**요구사항**:
1. 정답 제목({title})을 포함하여 총 4개의 보기 생성
2. 오답 3개는 다음 조건을 만족해야 함:
   - 내용과 어느 정도 관련이 있어 보이지만 정답은 아닌 제목
   - 너무 쉽게 구분되지 않도록 (하지만 명확히 틀린 것)
   - 길이와 형식이 정답과 유사
3. 4개 보기의 순서는 랜덤하게 배치 (정답이 항상 첫 번째가 아니도록)

**응답 형식 (JSON만 반환, 다른 텍스트 없이)**:
{{
  "choices": ["제목1", "제목2", "제목3", "제목4"],
  "correct_answer": "{title}"
}}

**예시**:
정답: "파이썬 리스트 기초"
오답: ["파이썬 딕셔너리 활용", "파이썬 문자열 처리", "파이썬 반복문 이해"]

JSON만 반환하세요.""")

    def _validate_mc_response(self, result: Dict, expected_title: str) -> bool:
        """Validate MC response structure."""
        # Check required keys
        if 'choices' not in result or 'correct_answer' not in result:
            logger.warning("Missing required keys: choices or correct_answer")
            return False

        # Check choices is a list
        if not isinstance(result['choices'], list):
            logger.warning("choices must be a list")
            return False

        # Check exactly 4 choices
        if len(result['choices']) != 4:
            logger.warning(f"Must have exactly 4 choices, got {len(result['choices'])}")
            return False

        # Check correct answer is in choices
        if result['correct_answer'] not in result['choices']:
            logger.warning("correct_answer must be one of the choices")
            return False

        # Ensure correct answer matches expected title
        if result['correct_answer'] != expected_title:
            logger.warning(
                f"AI returned different correct_answer: {result['correct_answer']} vs {expected_title}"
            )
            result['correct_answer'] = expected_title

            # Replace one of the choices with the expected title if not present
            if expected_title not in result['choices']:
                result['choices'][0] = expected_title

        return True


# Singleton instance
mc_generator = MCGenerator()


# Backward compatibility function
def generate_multiple_choice_options(title: str, content: str) -> Optional[Dict]:
    """
    Generate multiple choice options based on content.

    Backward-compatible function interface.
    """
    return mc_generator.generate_multiple_choice_options(title, content)
