"""
AI 기반 서술형 답변 평가 서비스

LangChain 기반으로 구현됨
"""
import json
import logging
from typing import Dict, Optional
from django.conf import settings
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


class AIAnswerEvaluator:
    """AI를 사용한 서술형 답변 평가기 (LangChain 기반)"""

    def __init__(self):
        self.llm = None
        self._initialize_client()

    def _initialize_client(self):
        """LangChain ChatAnthropic 클라이언트 초기화"""
        try:
            api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)

            if not api_key:
                logger.warning("ANTHROPIC_API_KEY가 설정되지 않았습니다. AI 평가를 사용할 수 없습니다.")
                return

            if not api_key.startswith('sk-ant-api'):
                logger.error("잘못된 Anthropic API 키 형식입니다.")
                return

            self.llm = ChatAnthropic(
                model="claude-3-haiku-20240307",
                temperature=0.3,
                max_tokens=500,
                api_key=api_key
            )
            logger.info("AI 답변 평가 클라이언트 초기화 완료 (LangChain)")
        except Exception as e:
            logger.error(f"AI 클라이언트 초기화 실패: {e}")
            self.llm = None

    def is_available(self) -> bool:
        """AI 서비스 사용 가능 여부"""
        return self.llm is not None

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
            prompt_template = self._get_evaluation_prompt_template()
            response = self.llm.invoke(
                prompt_template.format(
                    title=content_title,
                    content=content_body[:1500] + ("..." if len(content_body) > 1500 else ""),
                    answer=user_answer
                )
            )

            if response:
                evaluation_data = self._parse_response(response.content)
                if evaluation_data:
                    logger.info(f"AI 답변 평가 완료: {content_title} - {evaluation_data['score']}점")
                    return evaluation_data

        except Exception as e:
            logger.error(f"AI 답변 평가 실패: {content_title} - {e}", exc_info=True)

        return None

    def _get_evaluation_prompt_template(self) -> ChatPromptTemplate:
        """AI 답변 평가를 위한 프롬프트 템플릿 (LangChain)"""
        return ChatPromptTemplate.from_template("""다음 학습 콘텐츠에 대한 사용자의 서술형 답변을 **깐깐하게** 평가해주세요.

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

**응답 형식:**
반드시 다음 JSON 형식으로만 응답하세요 (다른 텍스트 없이):

score: 0-100 사이의 숫자
evaluation: excellent, good, fair, poor 중 하나
feedback: 구체적이고 건설적인 피드백 (2-3문장, 한국어)
auto_result: remembered (70점 이상) 또는 forgot (70점 미만)

예시:
{{"score": 85, "evaluation": "good", "feedback": "핵심 개념을 잘 이해하고 있습니다.", "auto_result": "remembered"}}

**중요:**
- 반드시 유효한 JSON 형식으로만 응답 (코드 블록 없이 순수 JSON)
- **무의미한 답변은 즉시 0점**
- 정확성과 완성도를 엄격하게 평가
- 핵심 개념이 누락되었거나 부정확하면 반드시 감점
- 70점 미만은 "forgot", 70점 이상만 "remembered"로 판단""")

    def _parse_response(self, response: str) -> Optional[Dict]:
        """
        AI 응답을 JSON으로 파싱 (개선된 중괄호 카운팅 방식)
        """
        try:
            text = response.strip()

            # 코드 블록 제거
            if text.startswith('```json'):
                text = text[7:].strip()
                if '```' in text:
                    text = text[:text.index('```')].strip()
            elif text.startswith('```'):
                text = text[3:].strip()
                if '```' in text:
                    text = text[:text.index('```')].strip()

            # JSON 객체 경계 찾기 (중괄호 카운팅)
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

            data = json.loads(text)

            # 필수 필드 검증
            required_fields = ['score', 'evaluation', 'feedback']
            if not all(field in data for field in required_fields):
                logger.warning(f"AI 응답에 필수 필드 누락. Got: {list(data.keys())}")
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
            logger.error(f"JSON 파싱 실패: {e}")
            logger.error(f"응답 내용: {response[:500]}...")  # DEBUG → ERROR로 변경
            return None
        except (ValueError, KeyError) as e:
            logger.error(f"응답 데이터 검증 실패: {e}")
            return None
        except Exception as e:
            logger.error(f"응답 처리 실패: {e}", exc_info=True)
            return None


# 싱글톤 인스턴스
ai_answer_evaluator = AIAnswerEvaluator()
