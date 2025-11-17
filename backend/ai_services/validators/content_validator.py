"""
AI-powered content validation service.

Validates learning content for:
- Factual accuracy
- Logical consistency
- Title relevance

Uses Claude 3.7 Sonnet for high-quality validation.
"""

import logging

from langchain_core.prompts import ChatPromptTemplate

from ai_services.base import BaseAIService

logger = logging.getLogger(__name__)


class ContentValidator(BaseAIService):
    """
    Validates learning content using AI.

    Checks factual accuracy, logical consistency, and title-content alignment.
    """

    def __init__(self):
        # Use Claude 3.7 Sonnet for high-quality validation
        super().__init__(
            model="claude-3-7-sonnet-20250219",
            use_langchain=True
        )

    def _get_temperature(self) -> float:
        return 0.3

    def _get_max_tokens(self) -> int:
        return 2000

    def validate_content(self, title: str, content: str) -> dict:
        """
        Validate learning content using AI.

        Args:
            title: Content title
            content: Content body (markdown)

        Returns:
            dict: Validation results with scores and feedback
            {
                'is_valid': bool,
                'factual_accuracy': {'score': int, 'issues': list},
                'logical_consistency': {'score': int, 'issues': list},
                'title_relevance': {'score': int, 'issues': list},
                'overall_feedback': str
            }
        """
        if not self.is_available():
            logger.error("AI service not available")
            return self._get_error_response("API 키가 설정되지 않았습니다")

        try:
            prompt_template = self._create_validation_prompt()
            response_text = self.call_langchain(
                prompt_template,
                title=title,
                content=content
            )

            if not response_text:
                return self._get_error_response("AI 응답을 받지 못했습니다")

            logger.info(f"AI validation response received for '{title[:50]}...'")

            result = self.parse_json_response(response_text)
            if not result:
                return self._get_error_response("AI 응답 파싱 실패")

            # Validate structure
            required_keys = [
                'is_valid',
                'factual_accuracy',
                'logical_consistency',
                'title_relevance',
                'overall_feedback'
            ]

            if not self.validate_required_fields(result, required_keys):
                return self._get_error_response("AI 응답 형식 오류")

            return result

        except Exception as e:
            logger.error(
                f"AI validation failed for title '{title[:50]}...': {str(e)}",
                exc_info=True
            )
            return self._get_error_response(f"AI 검증 중 오류가 발생했습니다: {str(e)}")

    def _create_validation_prompt(self) -> ChatPromptTemplate:
        """Create validation prompt template."""
        return ChatPromptTemplate.from_template("""당신은 학습 자료 검증 전문가입니다. 다음 학습 콘텐츠를 엄격하게 검토해주세요.

제목: {title}
내용:
{content}

다음 3가지를 평가해주세요:

1. **사실적 정확성** (Factual Accuracy):
   - 내용이 객관적으로 정확한가?
   - 잘못된 정보나 오해의 소지가 있는가?
   - 점수: 0-100 (100점 만점)

2. **논리적 일관성** (Logical Consistency):
   - 설명의 논리가 타당한가?
   - 모순되는 내용이 있는가?
   - 점수: 0-100 (100점 만점)

3. **제목-내용 적합성** (Title Relevance):
   - 제목과 내용이 일치하는가?
   - 제목에서 기대되는 내용을 다루고 있는가?
   - 점수: 0-100 (100점 만점)

**응답 형식 (JSON만 반환, 다른 텍스트 없이):**
{{
  "is_valid": true/false (모든 점수가 70점 이상이면 true),
  "factual_accuracy": {{
    "score": 0-100,
    "issues": ["문제점1", "문제점2", ...] (없으면 빈 배열)
  }},
  "logical_consistency": {{
    "score": 0-100,
    "issues": ["문제점1", "문제점2", ...] (없으면 빈 배열)
  }},
  "title_relevance": {{
    "score": 0-100,
    "issues": ["문제점1", "문제점2", ...] (없으면 빈 배열)
  }},
  "overall_feedback": "전체 평가 요약 (2-3문장)"
}}

**평가 기준:**
- 90-100점: 매우 우수, 문제 없음
- 70-89점: 양호, 사소한 개선 필요
- 50-69점: 보통, 중요한 개선 필요
- 0-49점: 부족, 전면 수정 필요

JSON만 반환하세요.""")

    def _get_error_response(self, error_message: str) -> dict:
        """Get error response structure."""
        return {
            "is_valid": False,
            "factual_accuracy": {"score": 0, "issues": ["AI 검증 실패"]},
            "logical_consistency": {"score": 0, "issues": ["AI 검증 실패"]},
            "title_relevance": {"score": 0, "issues": ["AI 검증 실패"]},
            "overall_feedback": error_message
        }


# Singleton instance
content_validator = ContentValidator()


# Backward compatibility function
def validate_content(title: str, content: str) -> dict:
    """
    Validate learning content using AI.

    Backward-compatible function interface.
    """
    return content_validator.validate_content(title, content)
