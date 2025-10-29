"""
AI 기반 주간 시험 문제 생성 서비스
"""
import json
import logging
from typing import Dict, Optional, List
from django.conf import settings
import anthropic
from content.models import Content

logger = logging.getLogger(__name__)


class AIQuestionGenerator:
    """AI를 사용한 주간 시험 문제 생성기"""

    def __init__(self):
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Anthropic Claude API 클라이언트 초기화"""
        try:
            api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)

            if not api_key:
                logger.warning("ANTHROPIC_API_KEY가 설정되지 않았습니다. AI 문제 생성을 사용할 수 없습니다.")
                return

            # API 키 형식 검증
            if not api_key.startswith('sk-ant-api'):
                logger.error("잘못된 Anthropic API 키 형식입니다. 'sk-ant-api'로 시작해야 합니다.")
                return

            if len(api_key) < 20:  # API 키 최소 길이 확인
                logger.error("API 키가 너무 짧습니다. 올바른 Anthropic API 키를 확인하세요.")
                return

            self.client = anthropic.Anthropic(api_key=api_key)
            logger.info("AI 클라이언트 초기화 완료")

            # 간단한 연결 테스트 (선택적)
            # self._test_connection()

        except anthropic.AuthenticationError as e:
            logger.error(f"AI API 인증 실패 - 토큰이 유효하지 않습니다: {e}")
            self.client = None
        except Exception as e:
            logger.error(f"AI 클라이언트 초기화 실패: {e}")
            self.client = None

    def is_available(self) -> bool:
        """AI 서비스 사용 가능 여부"""
        return self.client is not None

    def _test_connection(self) -> bool:
        """AI API 연결 테스트"""
        if not self.client:
            return False

        try:
            # 간단한 테스트 요청
            test_message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )
            logger.info("AI API 연결 테스트 성공")
            return True

        except anthropic.AuthenticationError:
            logger.error("AI API 연결 테스트 실패 - 인증 오류")
            self.client = None
            return False
        except anthropic.RateLimitError:
            logger.warning("AI API 연결 테스트 - 요청 한도 도달 (서비스는 사용 가능)")
            return True  # 한도 도달이지만 토큰은 유효
        except Exception as e:
            logger.error(f"AI API 연결 테스트 실패: {e}")
            return False

    def generate_question(self, content: Content) -> Optional[Dict]:
        """콘텐츠를 기반으로 AI 문제 생성"""
        if not self.is_available():
            logger.warning("AI 서비스가 사용 불가능합니다")
            return None

        try:
            prompt = self._create_prompt(content)
            response = self._call_ai_api(prompt)

            if response:
                question_data = self._parse_response(response)
                if self._validate_question(question_data):
                    logger.info(f"AI 문제 생성 성공: {content.title}")
                    return question_data
                else:
                    logger.warning(f"생성된 문제가 유효하지 않음: {content.title}")

        except Exception as e:
            logger.error(f"AI 문제 생성 실패: {content.title} - {e}")

        return None

    def _create_prompt(self, content: Content) -> str:
        """AI 문제 생성을 위한 프롬프트 생성"""
        category_name = content.category.name if content.category else "기타"

        # AI 검증 정보 포함 (있는 경우)
        validation_info = ""
        if content.is_ai_validated and content.ai_validation_result:
            validation_info = f"\n- AI 검증 점수: {content.ai_validation_score}/100"
            if 'overall_feedback' in content.ai_validation_result:
                validation_info += f"\n- 콘텐츠 품질 평가: {content.ai_validation_result['overall_feedback']}"

        prompt = f"""당신은 교육 전문가입니다. 다음 학습 콘텐츠를 분석하여 학습자의 진정한 이해도를 측정할 수 있는 고품질 문제를 생성해주세요.

**콘텐츠 정보:**
- 제목: {content.title}
- 카테고리: {category_name}{validation_info}
- 내용:
{content.content[:1500]}{"..." if len(content.content) > 1500 else ""}

**문제 생성 원칙:**

1. **이해도 중심 문제 설계**
   - 단순 암기가 아닌 개념의 이해와 적용을 평가
   - "~이 무엇인가?" 보다는 "왜 ~인가?", "어떻게 ~인가?"
   - 실제 상황에 적용할 수 있는지 확인하는 문제 선호

2. **문제 유형 선택 기준**
   - 객관식: 복잡한 개념, 비교/분석, 적용 문제에 적합
   - O/X: 명확한 사실 확인, 오개념 점검에 적합
   - 콘텐츠 특성에 가장 적합한 유형 선택

3. **객관식 문제 작성 시**
   - 4개 선택지 모두 그럴듯하고 관련성 있게 작성
   - 오답은 흔한 오개념이나 혼동하기 쉬운 내용으로 구성
   - "모두 옳다", "없다" 같은 선택지는 지양
   - 정답이 너무 명확하거나 길이로 구분되지 않도록 균형있게 작성

4. **O/X 문제 작성 시**
   - 단순 사실이 아닌 중요한 개념이나 흔한 오개념 확인
   - 문장이 명확하고 애매하지 않게 작성
   - "항상", "절대", "모든" 같은 극단적 표현은 신중하게 사용

5. **해설 작성 원칙**
   - 왜 그것이 정답인지 논리적으로 설명
   - 오답 선택 시 왜 틀렸는지 간단히 언급
   - 추가 학습 포인트가 있다면 간략히 포함
   - 2-3문장 이내로 간결하게 작성

**품질 체크리스트:**
✓ 문제만 보고도 무엇을 묻는지 명확한가?
✓ 정답을 맞히려면 콘텐츠를 제대로 이해해야 하는가?
✓ 추측으로 답을 맞히기 어려운가?
✓ 문제와 선택지에 불필요한 정보가 없는가?
✓ 해설이 학습자에게 실질적 도움이 되는가?

**응답 형식 (JSON만):**
{{
  "question_type": "multiple_choice" 또는 "true_false",
  "question_text": "명확하고 구체적인 문제 내용 (질문 형태 또는 완성 문장)",
  "choices": ["선택지1", "선택지2", "선택지3", "선택지4"] 또는 null (O/X의 경우),
  "correct_answer": "정확한 정답",
  "explanation": "정답 근거와 핵심 개념 설명 (2-3문장)"
}}

**필수 준수사항:**
- 한국어로만 작성
- 반드시 유효한 JSON 형식으로만 응답 (추가 설명 없이)
- 콘텐츠의 가장 핵심적인 내용을 다루는 문제 생성
- 학습 목표 달성 여부를 실질적으로 평가할 수 있는 문제"""

        return prompt

    def _call_ai_api(self, prompt: str) -> Optional[str]:
        """Claude API 호출"""
        try:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",  # 비용 효율적인 모델
                max_tokens=1000,
                temperature=0.3,  # 일관성 있는 응답
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return message.content[0].text if message.content else None

        except anthropic.AuthenticationError as e:
            logger.error(f"AI API 인증 실패 - 토큰이 유효하지 않습니다: {e}")
            return None
        except anthropic.PermissionDeniedError as e:
            logger.error(f"AI API 권한 거부 - 토큰 권한을 확인하세요: {e}")
            return None
        except anthropic.RateLimitError as e:
            logger.error(f"AI API 요청 한도 초과 - 잠시 후 다시 시도하세요: {e}")
            return None
        except anthropic.APIConnectionError as e:
            logger.error(f"AI API 연결 실패 - 네트워크 연결을 확인하세요: {e}")
            return None
        except anthropic.APITimeoutError as e:
            logger.error(f"AI API 요청 시간 초과: {e}")
            return None
        except anthropic.BadRequestError as e:
            logger.error(f"AI API 잘못된 요청: {e}")
            return None
        except anthropic.InternalServerError as e:
            logger.error(f"AI API 서버 오류: {e}")
            return None
        except Exception as e:
            logger.error(f"Claude API 호출 실패 (예상치 못한 오류): {e}")
            return None

    def _parse_response(self, response: str) -> Optional[Dict]:
        """AI 응답을 JSON으로 파싱"""
        try:
            # JSON 블록 추출 (```json...``` 형태로 감싸져 있을 수 있음)
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:-3].strip()
            elif response.startswith('```'):
                response = response[3:-3].strip()

            data = json.loads(response)
            return data

        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e} - 응답: {response[:200]}")
            return None
        except Exception as e:
            logger.error(f"응답 처리 실패: {e}")
            return None

    def _validate_question(self, question_data: Dict) -> bool:
        """생성된 문제 데이터 유효성 검증"""
        if not question_data:
            return False

        required_fields = ['question_type', 'question_text', 'correct_answer', 'explanation']

        # 필수 필드 확인
        for field in required_fields:
            if field not in question_data or not question_data[field]:
                logger.warning(f"필수 필드 누락: {field}")
                return False

        # 문제 유형 검증
        question_type = question_data['question_type']
        if question_type not in ['multiple_choice', 'true_false']:
            logger.warning(f"잘못된 문제 유형: {question_type}")
            return False

        # 객관식 문제의 경우 선택지 검증
        if question_type == 'multiple_choice':
            choices = question_data.get('choices', [])
            if not choices or len(choices) != 4:
                logger.warning(f"객관식 선택지 오류: {len(choices) if choices else 0}개")
                return False

            # 정답이 선택지에 포함되어 있는지 확인
            if question_data['correct_answer'] not in choices:
                logger.warning("정답이 선택지에 없음")
                return False

        # O/X 문제의 경우 정답 검증
        elif question_type == 'true_false':
            correct_answer = question_data['correct_answer'].upper()
            if correct_answer not in ['O', 'X', 'TRUE', 'FALSE']:
                logger.warning(f"O/X 문제의 잘못된 정답: {correct_answer}")
                return False

            # 정답을 O/X 형식으로 통일
            if correct_answer in ['TRUE']:
                question_data['correct_answer'] = 'O'
            elif correct_answer in ['FALSE']:
                question_data['correct_answer'] = 'X'

        return True

    def generate_batch_questions(self, contents: List[Content]) -> List[Dict]:
        """여러 콘텐츠에 대한 일괄 문제 생성"""
        questions = []

        for content in contents:
            question = self.generate_question(content)
            if question:
                question['content_id'] = content.id
                questions.append(question)

        logger.info(f"일괄 문제 생성 완료: {len(questions)}/{len(contents)}개 성공")
        return questions


# 싱글톤 인스턴스
ai_question_generator = AIQuestionGenerator()