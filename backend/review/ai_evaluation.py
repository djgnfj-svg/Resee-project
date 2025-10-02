"""
AI 기반 서술형 답변 평가 서비스 (v0.4)
"""
import json
import logging
from typing import Dict, Optional
from django.conf import settings
import anthropic

logger = logging.getLogger(__name__)


class AIAnswerEvaluator:
    """AI를 사용한 서술형 답변 평가기"""

    def __init__(self):
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Anthropic Claude API 클라이언트 초기화"""
        try:
            api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)

            if not api_key:
                logger.warning("ANTHROPIC_API_KEY가 설정되지 않았습니다. AI 평가를 사용할 수 없습니다.")
                return

            if not api_key.startswith('sk-ant-api'):
                logger.error("잘못된 Anthropic API 키 형식입니다.")
                return

            self.client = anthropic.Anthropic(api_key=api_key)
            logger.info("AI 답변 평가 클라이언트 초기화 완료")
        except Exception as e:
            logger.error(f"AI 클라이언트 초기화 실패: {e}")
            self.client = None

    def is_available(self) -> bool:
        """AI 서비스 사용 가능 여부"""
        return self.client is not None

    def evaluate_answer(self, content_title: str, content_body: str, user_answer: str) -> Optional[Dict]:
        """
        사용자 답변을 AI로 평가

        Args:
            content_title: 학습 콘텐츠 제목
            content_body: 학습 콘텐츠 내용
            user_answer: 사용자 서술형 답변

        Returns:
            {
                'score': float (0-100),
                'feedback': str,
                'evaluation': str ('excellent', 'good', 'fair', 'poor')
            }
        """
        if not self.is_available():
            logger.warning("AI 서비스가 사용 불가능합니다")
            return None

        if not user_answer or len(user_answer.strip()) < 10:
            return {
                'score': 0,
                'feedback': '답변이 너무 짧습니다. 학습한 내용을 더 자세히 설명해주세요.',
                'evaluation': 'poor'
            }

        try:
            prompt = self._create_evaluation_prompt(content_title, content_body, user_answer)
            response = self._call_ai_api(prompt)

            if response:
                evaluation_data = self._parse_response(response)
                if evaluation_data:
                    logger.info(f"AI 답변 평가 완료: {content_title} - {evaluation_data['score']}점")
                    return evaluation_data

        except Exception as e:
            logger.error(f"AI 답변 평가 실패: {content_title} - {e}")

        return None

    def _create_evaluation_prompt(self, title: str, content: str, answer: str) -> str:
        """AI 답변 평가를 위한 프롬프트 생성"""
        prompt = f"""다음 학습 콘텐츠에 대한 사용자의 서술형 답변을 **깐깐하게** 평가해주세요.

**학습 콘텐츠:**
제목: {title}
내용: {content[:1500]}{"..." if len(content) > 1500 else ""}

**사용자 답변:**
{answer}

**평가 기준 (엄격 적용):**
1. 핵심 개념 이해도 (40점): 주요 내용을 정확하고 완전하게 이해했는가?
2. 설명의 명확성 (30점): 명확하고 논리적으로 설명했는가?
3. 세부 사항 (20점): 중요한 세부 내용을 빠짐없이 포함했는가?
4. 답변 완성도 (10점): 답변이 충분히 상세하고 체계적인가?

**점수 기준 (엄격):**
- 90-100점: 핵심 개념을 완벽히 이해하고 세부사항까지 정확하게 설명
- 70-89점: 핵심 개념을 이해하고 대부분의 내용을 포함
- 50-69점: 일부 핵심 개념을 이해했으나 중요한 부분이 누락됨
- 0-49점: 핵심 개념 이해 부족 또는 내용 대부분 누락

**응답 형식 (JSON):**
{{
  "score": 0-100 사이의 점수,
  "evaluation": "excellent" (90-100점), "good" (70-89점), "fair" (50-69점), "poor" (0-49점) 중 하나,
  "feedback": "구체적이고 건설적인 피드백 (2-3문장, 한국어)",
  "auto_result": "remembered" (70점 이상) 또는 "forgot" (70점 미만)
}}

**중요:**
- 반드시 유효한 JSON 형식으로만 응답
- **정확성과 완성도를 엄격하게 평가**
- 핵심 개념이 누락되었거나 부정확하면 반드시 감점
- 70점 미만은 "forgot", 70점 이상만 "remembered"로 판단"""

        return prompt

    def _call_ai_api(self, prompt: str) -> Optional[str]:
        """Claude API 호출"""
        try:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return message.content[0].text if message.content else None

        except anthropic.AuthenticationError as e:
            logger.error(f"AI API 인증 실패: {e}")
            return None
        except anthropic.RateLimitError as e:
            logger.error(f"AI API 요청 한도 초과: {e}")
            return None
        except Exception as e:
            logger.error(f"Claude API 호출 실패: {e}")
            return None

    def _parse_response(self, response: str) -> Optional[Dict]:
        """AI 응답을 JSON으로 파싱"""
        try:
            # JSON 블록 추출
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:-3].strip()
            elif response.startswith('```'):
                response = response[3:-3].strip()

            data = json.loads(response)

            # 필수 필드 검증
            if 'score' not in data or 'evaluation' not in data or 'feedback' not in data:
                logger.warning("AI 응답에 필수 필드 누락")
                return None

            # 점수 범위 검증
            score = float(data['score'])
            if not (0 <= score <= 100):
                logger.warning(f"잘못된 점수 범위: {score}")
                score = max(0, min(100, score))

            # auto_result 자동 생성 (AI가 제공하지 않은 경우 점수 기반 판단)
            auto_result = data.get('auto_result')
            if not auto_result:
                auto_result = 'remembered' if score >= 70 else 'forgot'

            return {
                'score': score,
                'evaluation': data['evaluation'],
                'feedback': data['feedback'],
                'auto_result': auto_result
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e} - 응답: {response[:200]}")
            return None
        except Exception as e:
            logger.error(f"응답 처리 실패: {e}")
            return None


# 싱글톤 인스턴스
ai_answer_evaluator = AIAnswerEvaluator()
