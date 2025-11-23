"""
AI 기반 답변 평가 서비스

사용자의 서술형 답변을 학습 콘텐츠와 비교하여 평가합니다.
점수, 피드백, 기억함/잊음 분류를 제공합니다.

비용 효율적인 평가를 위해 Claude 3 Haiku를 사용합니다.
"""

import logging
from typing import Dict, Optional

from langchain_core.prompts import ChatPromptTemplate

from ai_services.base import BaseAIService

logger = logging.getLogger(__name__)


class AnswerEvaluator(BaseAIService):
    """
    AI를 사용하여 사용자의 서술형 답변을 평가합니다.

    기능:
    - 무효 답변 감지 (스팸, 무의미한 입력)
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

    def evaluate_answer(
        self, content_title: str, content_body: str, user_answer: str
    ) -> Optional[Dict]:
        """
        AI를 사용하여 사용자의 답변을 평가합니다.

        Args:
            content_title: 학습 콘텐츠 제목
            content_body: 학습 콘텐츠 본문
            user_answer: 사용자가 작성한 답변

        Returns:
            {
                'score': float (0-100),
                'evaluation': str ('excellent', 'good', 'fair', 'poor'),
                'feedback': str,
                'auto_result': str ('remembered' or 'forgot')
            }
            또는 AI 서비스를 사용할 수 없는 경우 None
        """
        if not self.is_available():
            logger.warning("AI service not available")
            return None

        # 답변 길이 확인
        if not user_answer or len(user_answer.strip()) < 10:
            return {
                "score": 0,
                "feedback": "답변이 너무 짧습니다. 학습한 내용을 더 자세히 설명해주세요.",
                "evaluation": "poor",
                "auto_result": "forgot",
            }

        try:
            prompt_template = self._create_evaluation_prompt()
            response_text = self.call_langchain(
                prompt_template,
                title=content_title,
                content=content_body[:1500]
                + ("..." if len(content_body) > 1500 else ""),
                answer=user_answer,
            )

            if not response_text:
                logger.warning(f"No response from AI for content: {content_title}")
                return None

            result = self.parse_json_response(response_text)
            if not result:
                return None

            # 필수 필드 검증
            required_fields = ["score", "evaluation", "feedback"]
            if not self.validate_required_fields(result, required_fields):
                return None

            # 점수 검증 및 정규화
            score = float(result["score"])
            if not (0 <= score <= 100):
                logger.warning(f"Invalid score: {score}")
                score = max(0, min(100, score))

            # auto_result가 없으면 자동 생성 (70점 이상이면 remembered)
            auto_result = result.get("auto_result")
            if not auto_result:
                auto_result = "remembered" if score >= 70 else "forgot"

            evaluation_result = {
                "score": score,
                "evaluation": result["evaluation"],
                "feedback": result["feedback"],
                "auto_result": auto_result,
            }

            logger.info(
                f"Answer evaluated for '{content_title}': {score} points ({auto_result})"
            )

            return evaluation_result

        except Exception as e:
            logger.error(
                f"Failed to evaluate answer for '{content_title}': {e}", exc_info=True
            )
            return None

    def _create_evaluation_prompt(self) -> ChatPromptTemplate:
        """평가 프롬프트 템플릿을 생성합니다."""
        return ChatPromptTemplate.from_template(
            """다음 학습 콘텐츠에 대한 사용자의 서술형 답변을 **깐깐하게** 평가해주세요.

**학습 콘텐츠:**
제목: {title}
내용: {content}

**사용자 답변:**
{answer}

**1단계: 답변 유효성 검사 (필수)**
먼저 다음 사항을 확인하세요. 하나라도 해당하면 **즉시 0점 처리**:
- 숫자만 나열된 경우 (예: "123456", "1417141717147")
- 무의미한 문자 반복 (예: "ㅁㅁㅁㅁ", "aaaaaa")
- 학습 내용과 전혀 무관한 내용
- 한 단어나 짧은 단어만 나열
- 복사-붙여넣기로 보이는 원문 그대로 (이해 없이 복사)

**2단계: 내용 평가 (유효한 답변인 경우)**
1. 핵심 개념 이해도 (40점): 주요 내용을 정확하고 완전하게 이해했는가?
2. 설명의 명확성 (30점): 명확하고 논리적으로 설명했는가?
3. 세부 사항 (20점): 중요한 세부 내용을 빠짐없이 포함했는가?
4. 답변 완성도 (10점): 답변이 충분히 상세하고 체계적인가?

**점수 기준 (엄격):**
- 0점: 무의미한 답변 (위 1단계 해당)
- 1-49점: 핵심 개념 이해 부족 또는 내용 대부분 누락
- 50-69점: 일부 핵심 개념을 이해했으나 중요한 부분이 누락됨
- 70-89점: 핵심 개념을 이해하고 대부분의 내용을 포함
- 90-100점: 핵심 개념을 완벽히 이해하고 세부사항까지 정확하게 설명

**응답 형식 (JSON만, 다른 텍스트 없이):**
{{
  "score": 0-100 사이의 점수,
  "evaluation": "excellent" (90-100점), "good" (70-89점), "fair" (50-69점), "poor" (0-49점) 중 하나,
  "feedback": "구체적이고 건설적인 피드백 (2-3문장, 한국어)",
  "auto_result": "remembered" (70점 이상) 또는 "forgot" (70점 미만)
}}

**중요:**
- 반드시 유효한 JSON 형식으로만 응답
- **무의미한 답변은 즉시 0점**
- 정확성과 완성도를 엄격하게 평가
- 핵심 개념이 누락되었거나 부정확하면 반드시 감점
- 70점 미만은 "forgot", 70점 이상만 "remembered"로 판단"""
        )


# 싱글톤 인스턴스
ai_answer_evaluator = AnswerEvaluator()
