"""
AI 기반 콘텐츠 검증 서비스

학습 콘텐츠를 다음 항목에 대해 검증합니다:
- 사실적 정확성
- 논리적 일관성
- 제목 적합성

고품질 검증을 위해 Claude 3.7 Sonnet을 사용합니다.
"""

import logging

from langchain_core.prompts import ChatPromptTemplate

from ai_services.base import BaseAIService

logger = logging.getLogger(__name__)


class ContentValidator(BaseAIService):
    """
    AI를 사용하여 학습 콘텐츠를 검증합니다.

    사실적 정확성, 논리적 일관성, 제목-내용 일치도를 확인합니다.
    """

    def __init__(self):
        # 고품질 검증을 위해 Claude 3.7 Sonnet 사용
        super().__init__(model="claude-3-7-sonnet-20250219", use_langchain=True)

    def _get_temperature(self) -> float:
        return 0.3

    def _get_max_tokens(self) -> int:
        return 2000

    def validate_content(self, title: str, content: str) -> dict:
        """
        AI를 사용하여 학습 콘텐츠를 검증합니다.

        Args:
            title: 콘텐츠 제목
            content: 콘텐츠 본문 (마크다운)

        Returns:
            dict: 점수와 피드백이 포함된 검증 결과
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
                prompt_template, title=title, content=content
            )

            if not response_text:
                return self._get_error_response("AI 응답을 받지 못했습니다")

            logger.info(f"AI validation response received for '{title[:50]}...'")

            result = self.parse_json_response(response_text)
            if not result:
                return self._get_error_response("AI 응답 파싱 실패")

            # 응답 구조 검증
            required_keys = [
                "is_valid",
                "factual_accuracy",
                "logical_consistency",
                "title_relevance",
                "overall_feedback",
            ]

            if not self.validate_required_fields(result, required_keys):
                return self._get_error_response("AI 응답 형식 오류")

            return result

        except Exception as e:
            logger.error(
                f"AI validation failed for title '{title[:50]}...': {str(e)}",
                exc_info=True,
            )
            return self._get_error_response(f"AI 검증 중 오류가 발생했습니다: {str(e)}")

    def _create_validation_prompt(self) -> ChatPromptTemplate:
        """검증 프롬프트 템플릿을 생성합니다."""
        return ChatPromptTemplate.from_template(
            """당신은 학습 자료 검증 전문가입니다. 다음 학습 콘텐츠를 엄격하게 검토해주세요.

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

JSON만 반환하세요."""
        )

    def _get_error_response(self, error_message: str) -> dict:
        """에러 응답 구조를 반환합니다."""
        return {
            "is_valid": False,
            "factual_accuracy": {"score": 0, "issues": ["AI 검증 실패"]},
            "logical_consistency": {"score": 0, "issues": ["AI 검증 실패"]},
            "title_relevance": {"score": 0, "issues": ["AI 검증 실패"]},
            "overall_feedback": error_message,
        }


# 싱글톤 인스턴스
content_validator = ContentValidator()


# 하위 호환성을 위한 함수
def validate_content(title: str, content: str) -> dict:
    """
    AI를 사용하여 학습 콘텐츠를 검증합니다.

    하위 호환성을 위한 함수 인터페이스입니다.
    """
    return content_validator.validate_content(title, content)
