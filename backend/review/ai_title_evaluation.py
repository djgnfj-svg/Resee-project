"""
AI-powered subjective title evaluation module.
Evaluates user's title guess based on content.
"""

import json
import logging
from typing import Dict, Optional
from django.conf import settings
import anthropic

logger = logging.getLogger(__name__)


class AITitleEvaluator:
    """AI를 사용한 주관식 제목 유추 평가기"""

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
            logger.info("AI 제목 평가 클라이언트 초기화 완료")
        except Exception as e:
            logger.error(f"AI 클라이언트 초기화 실패: {e}")
            self.client = None

    def is_available(self) -> bool:
        """AI 서비스 사용 가능 여부"""
        return self.client is not None

    def evaluate_title(self, content: str, user_title: str, actual_title: str) -> Optional[Dict]:
        """
        사용자가 유추한 제목을 AI로 평가

        Args:
            content: 학습 콘텐츠 내용
            user_title: 사용자가 유추한 제목
            actual_title: 실제 제목 (정답)

        Returns:
            {
                'score': float (0-100),
                'feedback': str,
                'is_correct': bool,
                'auto_result': str ('remembered' or 'forgot')
            }
        """
        if not self.is_available():
            logger.warning("AI 서비스가 사용 불가능합니다")
            return None

        if not user_title or len(user_title.strip()) < 2:
            return {
                'score': 0,
                'feedback': '제목이 너무 짧습니다. 내용에 맞는 제목을 작성해주세요.',
                'is_correct': False,
                'auto_result': 'forgot'
            }

        try:
            prompt = self._create_evaluation_prompt(content, user_title, actual_title)
            response = self._call_ai_api(prompt)

            if response:
                evaluation_data = self._parse_response(response)
                if evaluation_data:
                    logger.info(f"AI 제목 평가 완료: {user_title} (정답: {actual_title}) - {evaluation_data['score']}점")
                    return evaluation_data

        except Exception as e:
            logger.error(f"AI 제목 평가 실패: {user_title} - {e}", exc_info=True)

        return None

    def _create_evaluation_prompt(self, content: str, user_title: str, actual_title: str) -> str:
        """AI 제목 평가를 위한 프롬프트 생성"""
        prompt = f"""다음 학습 콘텐츠의 내용을 읽고, 사용자가 유추한 제목이 적절한지 평가해주세요.

**학습 콘텐츠 내용**:
{content[:1500]}{"..." if len(content) > 1500 else ""}

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
  "score": 0-100 사이의 점수,
  "is_correct": true (70점 이상) 또는 false (70점 미만),
  "feedback": "구체적이고 건설적인 피드백 (2-3문장, 한국어)",
  "auto_result": "remembered" (70점 이상) 또는 "forgot" (70점 미만)
}}

**중요**:
- 반드시 유효한 JSON 형식으로만 응답
- 의미가 비슷하면 표현이 달라도 높은 점수
- 핵심을 잘못 파악했으면 반드시 감점
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
            logger.error(f"AI API 인증 실패: {e}", exc_info=True)
            return None
        except anthropic.RateLimitError as e:
            logger.warning(f"AI API 요청 한도 초과 (일시적 제한): {e}")
            return None
        except anthropic.APIConnectionError as e:
            logger.error(f"AI API 연결 실패 (네트워크 문제): {e}")
            return None
        except anthropic.APITimeoutError as e:
            logger.warning(f"AI API 타임아웃 (서버 응답 지연): {e}")
            return None
        except Exception as e:
            logger.error(f"Claude API 호출 실패: {e}", exc_info=True)
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
            if 'score' not in data or 'is_correct' not in data or 'feedback' not in data:
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

            # is_correct 검증 (점수와 일치해야 함)
            is_correct = score >= 70

            return {
                'score': score,
                'is_correct': is_correct,
                'feedback': data['feedback'],
                'auto_result': auto_result
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e} - 응답: {response[:200]}", exc_info=True)
            return None
        except (ValueError, KeyError) as e:
            logger.error(f"응답 데이터 검증 실패: {e}")
            return None
        except Exception as e:
            logger.error(f"응답 처리 실패: {e}")
            return None


# 싱글톤 인스턴스
ai_title_evaluator = AITitleEvaluator()
