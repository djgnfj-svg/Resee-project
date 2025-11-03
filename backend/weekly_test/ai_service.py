"""
AI 기반 주간 시험 문제 생성 서비스

LangGraph 기반 고품질 Distractor 생성을 사용합니다.

주요 기능:
- 3가지 유형의 교육학적 오답 생성 (Type A, B, C)
- 품질 검증 및 자동 개선
- 길이 균형 및 그럴듯함 보장
"""

import json
import logging
from typing import Dict, Optional, List
from django.conf import settings

from content.models import Content
from ai_services.graphs import generate_quality_choices

logger = logging.getLogger(__name__)


class AIQuestionGenerator:
    """
    AI를 사용한 주간 시험 문제 생성기

    LangGraph 기반 Distractor 생성으로 품질을 크게 향상시켰습니다.
    """

    def __init__(self):
        self._check_availability()

    def _check_availability(self):
        """API 키 확인"""
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)

        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not configured")
            self.available = False
            return

        if not api_key.startswith('sk-ant-api') or len(api_key) < 20:
            logger.error("Invalid ANTHROPIC_API_KEY format")
            self.available = False
            return

        self.available = True
        logger.info("AI Question Generator initialized successfully")

    def is_available(self) -> bool:
        """AI 서비스 사용 가능 여부"""
        return self.available

    def generate_question(self, content: Content) -> Optional[Dict]:
        """
        콘텐츠를 기반으로 AI 문제 생성

        Args:
            content: Content 객체

        Returns:
            {
                'question_type': 'multiple_choice',
                'question_text': str,
                'choices': List[str],  # 4개, 섞여있음
                'correct_answer': str,
                'explanation': str,
                'metadata': dict  # 품질 정보
            }
            또는 None (실패 시)
        """
        if not self.is_available():
            logger.warning("AI service not available")
            return None

        try:
            # 1. 먼저 정답 생성
            correct_answer_data = self._generate_correct_answer(content)

            if not correct_answer_data:
                logger.warning(f"Failed to generate correct answer: {content.title}")
                return None

            # 2. LangGraph로 고품질 Distractor 생성
            choices_result = generate_quality_choices(
                content_title=content.title,
                content_body=content.content,
                correct_answer=correct_answer_data['answer']
            )

            if not choices_result or not choices_result.get('choices'):
                logger.warning(f"Failed to generate choices: {content.title}")
                return None

            # 3. 결과 조합
            question_data = {
                'question_type': 'multiple_choice',
                'question_text': correct_answer_data['question'],
                'choices': choices_result['choices'],
                'correct_answer': choices_result['correct_answer'],
                'explanation': correct_answer_data['explanation'],
                'metadata': {
                    'quality_score': choices_result['metadata'].get('quality_score', 0),
                    'iterations': choices_result['metadata'].get('iterations', 0),
                    'version': 'langgraph'
                }
            }

            logger.info(
                f"Generated question for '{content.title}' "
                f"(quality: {question_data['metadata']['quality_score']:.1f})"
            )

            return question_data

        except Exception as e:
            logger.error(
                f"Failed to generate question for '{content.title}': {e}",
                exc_info=True
            )
            return None

    def _generate_correct_answer(self, content: Content) -> Optional[Dict]:
        """
        정답과 문제 텍스트를 생성합니다.

        Returns:
            {
                'question': str,
                'answer': str,
                'explanation': str
            }
        """
        from langchain_anthropic import ChatAnthropic
        from langchain_core.prompts import ChatPromptTemplate

        llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            temperature=0.3,
            max_tokens=800,
            api_key=settings.ANTHROPIC_API_KEY
        )

        category_name = content.category.name if content.category else "기타"

        prompt = ChatPromptTemplate.from_template("""
다음 학습 콘텐츠를 분석하여 객관식 문제를 생성하세요.

**콘텐츠 정보:**
제목: {title}
카테고리: {category}
내용:
{content}

**문제 생성 원칙:**
1. 핵심 개념을 정확히 이해했는지 평가
2. 단순 암기가 아닌 이해도 평가
3. 명확하고 구체적인 질문
4. 정답은 완전하고 정확하게

**응답 형식 (JSON만, 다른 텍스트 없이):**
{{
  "question": "명확한 질문 또는 빈칸 완성 문장",
  "answer": "완전하고 정확한 정답 (문장 형태)",
  "explanation": "정답 근거와 핵심 개념 설명 (2-3문장)"
}}

예시:
{{
  "question": "Python 리스트의 핵심 특징으로 가장 적절한 것은?",
  "answer": "리스트는 mutable하여 생성 후에도 요소를 자유롭게 추가, 삭제, 수정할 수 있다",
  "explanation": "리스트는 가변(mutable) 자료구조로, 생성 후에도 내용을 변경할 수 있습니다. 이는 튜플(immutable)과 구분되는 핵심 특징입니다."
}}
""")

        try:
            response = llm.invoke(prompt.format(
                title=content.title,
                category=category_name,
                content=content.content[:1500]
            ))

            # JSON 파싱 - 응답에서 JSON 객체 추출
            response_text = response.content.strip()

            # 코드 블록 제거
            if response_text.startswith('```json'):
                response_text = response_text[7:]
                if '```' in response_text:
                    response_text = response_text[:response_text.index('```')]
            elif response_text.startswith('```'):
                response_text = response_text[3:]
                if '```' in response_text:
                    response_text = response_text[:response_text.index('```')]

            response_text = response_text.strip()

            # JSON 객체 경계 찾기 (중괄호로 시작하고 끝나는 첫 번째 완전한 객체)
            if response_text.startswith('{'):
                brace_count = 0
                for i, char in enumerate(response_text):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            response_text = response_text[:i+1]
                            break

            result = json.loads(response_text)

            # 필수 필드 확인
            required = ['question', 'answer', 'explanation']
            if all(field in result for field in required):
                return result
            else:
                logger.warning("Missing required fields in correct answer")
                return None

        except Exception as e:
            logger.error(f"Failed to generate correct answer: {e}", exc_info=True)
            return None

    def generate_batch_questions(
        self,
        contents: List[Content]
    ) -> List[Dict]:
        """
        여러 콘텐츠에 대한 일괄 문제 생성

        Args:
            contents: Content 객체 리스트

        Returns:
            생성된 문제 리스트
        """
        questions = []

        for content in contents:
            question = self.generate_question(content)
            if question:
                question['content_id'] = content.id
                questions.append(question)

        logger.info(
            f"Batch generation complete: {len(questions)}/{len(contents)} successful"
        )

        return questions


# 싱글톤 인스턴스
ai_question_generator = AIQuestionGenerator()
