"""
AI-powered weekly test question generator.

Generates high-quality multiple choice questions using:
- LangChain: For correct answer generation
- LangGraph: For pedagogically meaningful distractor generation

Uses Claude 3 Haiku for cost-efficient generation.
"""

import logging
from typing import Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate

from ai_services.base import BaseAIService
from ai_services.graphs import generate_quality_choices

logger = logging.getLogger(__name__)


class QuestionGenerator(BaseAIService):
    """
    Generates weekly test questions with high-quality distractors.

    Uses LangGraph workflow for pedagogically meaningful wrong answers.
    """

    def __init__(self):
        # Use Claude 3 Haiku for cost-efficient generation
        super().__init__(
            model="claude-3-haiku-20240307",
            use_langchain=True
        )

    def _get_temperature(self) -> float:
        return 0.3

    def _get_max_tokens(self) -> int:
        return 800

    def generate_question(self, content) -> Optional[Dict]:
        """
        Generate AI question based on content.

        Args:
            content: Content model instance (from content.models.Content)

        Returns:
            {
                'question_type': 'multiple_choice',
                'question_text': str,
                'choices': List[str],  # 4 choices, shuffled
                'correct_answer': str,
                'explanation': str,
                'metadata': dict  # Quality info
            }
            or None if generation fails
        """
        if not self.is_available():
            logger.warning("AI service not available")
            return None

        try:
            # Step 1: Generate correct answer
            correct_answer_data = self._generate_correct_answer(content)

            if not correct_answer_data:
                logger.warning(f"Failed to generate correct answer: {content.title}")
                return None

            # Step 2: Generate high-quality distractors using LangGraph
            choices_result = generate_quality_choices(
                content_title=content.title,
                content_body=content.content,
                correct_answer=correct_answer_data['answer']
            )

            if not choices_result or not choices_result.get('choices'):
                logger.warning(f"Failed to generate choices: {content.title}")
                return None

            # Step 3: Combine results
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

    def _generate_correct_answer(self, content) -> Optional[Dict]:
        """
        Generate correct answer and question text.

        Returns:
            {
                'question': str,
                'answer': str,
                'explanation': str
            }
        """
        category_name = content.category.name if content.category else "기타"

        prompt_template = self._create_correct_answer_prompt()
        response_text = self.call_langchain(
            prompt_template,
            title=content.title,
            category=category_name,
            content=content.content[:1500]
        )

        if not response_text:
            logger.warning(f"No response for correct answer generation: {content.title}")
            return None

        result = self.parse_json_response(response_text)
        if not result:
            return None

        # Validate required fields
        required = ['question', 'answer', 'explanation']
        if not self.validate_required_fields(result, required):
            logger.warning("Missing required fields in correct answer")
            return None

        return result

    def _create_correct_answer_prompt(self) -> ChatPromptTemplate:
        """Create prompt for correct answer generation."""
        return ChatPromptTemplate.from_template("""
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

    def generate_batch_questions(self, contents: List) -> List[Dict]:
        """
        Generate questions for multiple contents.

        Args:
            contents: List of Content model instances

        Returns:
            List of generated question dicts
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


# Singleton instance
ai_question_generator = QuestionGenerator()
