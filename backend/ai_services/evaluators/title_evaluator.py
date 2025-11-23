"""
AI 기반 제목 평가 서비스

콘텐츠 기반으로 사용자가 추측한 제목을 평가합니다.
점수, 정답 여부, 피드백을 제공합니다.

비용 효율적인 평가를 위해 Claude 3 Haiku를 사용합니다.
"""

import logging
from typing import Dict, Optional

from langchain_core.prompts import ChatPromptTemplate

from ai_services.base import BaseAIService

logger = logging.getLogger(__name__)


class TitleEvaluator(BaseAIService):
    """
    AI를 사용하여 사용자가 추측한 제목을 평가합니다.

    기능:
    - 실제 제목과의 의미적 유사성 확인
    - 이해도 기반 점수 평가 (0-100)
    - 상세한 한국어 피드백
    - 자동 기억함/잊음 분류
    """

    def __init__(self):
        # 비용 효율적인 평가를 위해 Claude 3 Haiku 사용
        super().__init__(model="claude-3-haiku-20240307", use_langchain=True)

    def _get_temperature(self) -> float:
        return 0.3

    def _get_max_tokens(self) -> int:
        return 500

    def evaluate_title(
        self, content: str, user_title: str, actual_title: str
    ) -> Optional[Dict]:
        """
        AI를 사용하여 사용자가 추측한 제목을 평가합니다.

        Args:
            content: 학습 콘텐츠 본문
            user_title: 사용자가 추측한 제목
            actual_title: 실제 제목 (정답)

        Returns:
            {
                'score': float (0-100),
                'feedback': str,
                'is_correct': bool,
                'auto_result': str ('remembered' or 'forgot')
            }
            또는 AI 서비스를 사용할 수 없는 경우 None
        """
        if not self.is_available():
            logger.warning("AI service not available")
            return None

        # 제목 길이 확인
        if not user_title or len(user_title.strip()) < 2:
            return {
                "score": 0,
                "feedback": "제목이 너무 짧습니다. 내용에 맞는 제목을 작성해주세요.",
                "is_correct": False,
                "auto_result": "forgot",
            }

        try:
            prompt_template = self._create_evaluation_prompt()
            response_text = self.call_langchain(
                prompt_template,
                content=content[:1500] + ("..." if len(content) > 1500 else ""),
                actual_title=actual_title,
                user_title=user_title,
            )

            if not response_text:
                logger.warning(
                    f"No response from AI for title evaluation: {actual_title}"
                )
                return None

            result = self.parse_json_response(response_text)
            if not result:
                return None

            # 필수 필드 검증
            required_fields = ["score", "is_correct", "feedback"]
            if not self.validate_required_fields(result, required_fields):
                return None

            # 점수 검증 및 정규화
            score = float(result["score"])
            if not (0 <= score <= 100):
                logger.warning(f"Invalid score: {score}")
                score = max(0, min(100, score))

            # is_correct는 점수 기반으로 결정 (70점 이상이면 정답)
            is_correct = score >= 70

            # auto_result가 없으면 자동 생성
            auto_result = result.get("auto_result")
            if not auto_result:
                auto_result = "remembered" if score >= 70 else "forgot"

            evaluation_result = {
                "score": score,
                "is_correct": is_correct,
                "feedback": result["feedback"],
                "auto_result": auto_result,
            }

            logger.info(
                f"Title evaluated: '{user_title}' vs '{actual_title}' - {score} points ({auto_result})"
            )

            return evaluation_result

        except Exception as e:
            logger.error(f"Failed to evaluate title '{user_title}': {e}", exc_info=True)
            return None

    def _create_evaluation_prompt(self) -> ChatPromptTemplate:
        """평가 프롬프트 템플릿을 생성합니다."""
        return ChatPromptTemplate.from_template(
            """다음 학습 콘텐츠의 내용을 읽고, 사용자가 유추한 제목이 적절한지 평가해주세요.

**학습 콘텐츠 내용**:
{content}

**실제 제목 (정답)**: {actual_title}
**사용자가 유추한 제목**: {user_title}

**평가 기준**:
1. **의미 일치도 (60점)**: 사용자 제목이 내용의 핵심을 정확히 표현하는가?
2. **정답과의 유사성 (30점)**: 정답 제목과 의미적으로 유사한가?
3. **적절성 (10점)**: 제목으로서 적절한가? (너무 길거나 짧지 않은가?)

**점수 산정**:
- 90-100점: 정답과 거의 동일하거나 완벽히 이해함
- 70-89점: 핵심을 정확히 파악했으나 표현이 약간 다름
- 50-69점: 일부만 이해했거나 불완전한 제목
- 0-49점: 내용을 잘못 이해했거나 전혀 관련 없는 제목

**무의미한 답변 체크 (즉시 0점)**:
- 숫자만 나열 (예: "123", "1234567")
- 무의미한 문자 반복 (예: "ㅁㅁㅁ", "aaa")
- 한 글자 또는 한 단어만
- 내용과 전혀 무관

**응답 형식 (JSON)**:
{{
  "score": 0-100,
  "is_correct": true or false,
  "feedback": "피드백 메시지",
  "auto_result": "remembered" or "forgot"
}}

**중요**:
- 반드시 유효한 JSON 형식으로만 응답
- 의미가 비슷하면 표현이 달라도 높은 점수
- 핵심을 잘못 파악했으면 반드시 감점
- 70점 미만은 "forgot", 70점 이상만 "remembered"로 판단"""
        )


# 싱글톤 인스턴스
ai_title_evaluator = TitleEvaluator()
