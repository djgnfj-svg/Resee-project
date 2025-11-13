"""
AI-powered title evaluation service.

Evaluates user's guessed title based on content.
Provides scoring, correctness check, and feedback.

Uses Claude 3 Haiku for cost-efficient evaluation.
"""

import logging
from typing import Dict, Optional
from langchain_core.prompts import ChatPromptTemplate

from ai_services.base import BaseAIService

logger = logging.getLogger(__name__)


class TitleEvaluator(BaseAIService):
    """
    Evaluates user's guessed title using AI.

    Features:
    - Semantic similarity check with actual title
    - Scoring (0-100) based on understanding
    - Detailed feedback in Korean
    - Automatic remembered/forgot classification
    """

    def __init__(self):
        # Use Claude 3 Haiku for cost-efficient evaluation
        super().__init__(
            model="claude-3-haiku-20240307",
            use_langchain=True
        )

    def _get_temperature(self) -> float:
        return 0.3

    def _get_max_tokens(self) -> int:
        return 500

    def evaluate_title(
        self,
        content: str,
        user_title: str,
        actual_title: str
    ) -> Optional[Dict]:
        """
        Evaluate user's guessed title using AI.

        Args:
            content: Learning content body
            user_title: User's guessed title
            actual_title: Actual title (correct answer)

        Returns:
            {
                'score': float (0-100),
                'feedback': str,
                'is_correct': bool,
                'auto_result': str ('remembered' or 'forgot')
            }
            or None if AI service unavailable
        """
        if not self.is_available():
            logger.warning("AI service not available")
            return None

        # Check title length
        if not user_title or len(user_title.strip()) < 2:
            return {
                'score': 0,
                'feedback': '제목이 너무 짧습니다. 내용에 맞는 제목을 작성해주세요.',
                'is_correct': False,
                'auto_result': 'forgot'
            }

        try:
            prompt_template = self._create_evaluation_prompt()
            response_text = self.call_langchain(
                prompt_template,
                content=content[:1500] + ("..." if len(content) > 1500 else ""),
                actual_title=actual_title,
                user_title=user_title
            )

            if not response_text:
                logger.warning(f"No response from AI for title evaluation: {actual_title}")
                return None

            result = self.parse_json_response(response_text)
            if not result:
                return None

            # Validate required fields
            required_fields = ['score', 'is_correct', 'feedback']
            if not self.validate_required_fields(result, required_fields):
                return None

            # Validate and normalize score
            score = float(result['score'])
            if not (0 <= score <= 100):
                logger.warning(f"Invalid score: {score}")
                score = max(0, min(100, score))

            # Ensure is_correct matches score
            is_correct = score >= 70

            # Auto-generate auto_result if not provided
            auto_result = result.get('auto_result')
            if not auto_result:
                auto_result = 'remembered' if score >= 70 else 'forgot'

            evaluation_result = {
                'score': score,
                'is_correct': is_correct,
                'feedback': result['feedback'],
                'auto_result': auto_result
            }

            logger.info(
                f"Title evaluated: '{user_title}' vs '{actual_title}' - {score} points ({auto_result})"
            )

            return evaluation_result

        except Exception as e:
            logger.error(
                f"Failed to evaluate title '{user_title}': {e}",
                exc_info=True
            )
            return None

    def _create_evaluation_prompt(self) -> ChatPromptTemplate:
        """Create evaluation prompt template."""
        return ChatPromptTemplate.from_template("""다음 학습 콘텐츠의 내용을 읽고, 사용자가 유추한 제목이 적절한지 평가해주세요.

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
{{{{
  "score": 0-100 사이의 점수,
  "is_correct": true (70점 이상) 또는 false (70점 미만),
  "feedback": "구체적이고 건설적인 피드백 (2-3문장, 한국어)",
  "auto_result": "remembered" (70점 이상) 또는 "forgot" (70점 미만)
}}}}

**중요**:
- 반드시 유효한 JSON 형식으로만 응답
- 의미가 비슷하면 표현이 달라도 높은 점수
- 핵심을 잘못 파악했으면 반드시 감점
- 70점 미만은 "forgot", 70점 이상만 "remembered"로 판단""")


# Singleton instance
ai_title_evaluator = TitleEvaluator()
