"""
AI Question Generation Service
"""
import json
import logging
from typing import Dict, List, Optional

from django.core.cache import cache

from content.models import Content
from ..models import AIQuestion, AIQuestionType
from .base_ai_service import BaseAIService, AIServiceError

logger = logging.getLogger(__name__)


class QuestionGeneratorService(BaseAIService):
    """
    Service for generating AI questions for content
    """
    
    def generate_questions(self, content: Content, question_types: List[str], 
                          difficulty: int = 3, count: int = 1) -> List[Dict]:
        """
        Generate AI questions for given content
        
        Args:
            content: Content object to generate questions for
            question_types: List of question type names
            difficulty: Difficulty level (1-5)
            count: Number of questions to generate
            
        Returns:
            List of generated question dictionaries
        """
        cache_key = f"ai_questions_{content.id}_{hash(tuple(question_types))}_{difficulty}_{count}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Get question type objects
        type_objects = AIQuestionType.objects.filter(
            name__in=question_types, 
            is_active=True
        )
        
        if not type_objects.exists():
            raise AIServiceError("No valid question types found")
        
        generated_questions = []
        
        for question_type in type_objects:
            try:
                questions = self._generate_questions_for_type(
                    content, question_type, difficulty, count
                )
                generated_questions.extend(questions)
            except Exception as e:
                logger.error(f"Failed to generate {question_type.name} questions: {str(e)}")
                continue
        
        # Cache the result
        cache.set(cache_key, generated_questions, self.cache_timeout)
        return generated_questions
    
    def _generate_questions_for_type(self, content: Content, question_type: AIQuestionType, 
                                   difficulty: int, count: int) -> List[Dict]:
        """
        Generate questions for a specific type
        """
        prompt = self._build_generation_prompt(content, question_type, difficulty, count)
        
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        response_text, processing_time = self._make_api_call(messages)
        
        try:
            response_data = self._parse_json_response(response_text)
            questions = self._process_generated_questions(
                response_data, content, question_type, processing_time
            )
            return questions
        except Exception as e:
            logger.error(f"Failed to process generated questions: {str(e)}")
            return []
    
    def _build_generation_prompt(self, content: Content, question_type: AIQuestionType, 
                               difficulty: int, count: int) -> str:
        """
        Build the prompt for question generation
        """
        difficulty_map = {
            1: "매우 쉬움",
            2: "쉬움", 
            3: "보통",
            4: "어려움",
            5: "매우 어려움"
        }
        
        prompt = f"""
다음 학습 콘텐츠를 바탕으로 {question_type.display_name} 문제를 {count}개 생성해주세요.

**콘텐츠 정보:**
제목: {content.title}
내용: {content.content}

**요구사항:**
- 문제 유형: {question_type.display_name}
- 난이도: {difficulty_map.get(difficulty, '보통')} (1-5 척도에서 {difficulty})
- 문제 수: {count}개

**응답 형식 (JSON):**
"""
        
        if question_type.name == 'multiple_choice':
            prompt += """
{
  "questions": [
    {
      "question_text": "문제 내용",
      "options": ["선택지1", "선택지2", "선택지3", "선택지4"],
      "correct_answer": "정답",
      "explanation": "정답 해설",
      "keywords": ["키워드1", "키워드2"],
      "difficulty": 3
    }
  ]
}
"""
        elif question_type.name == 'fill_blank':
            prompt += """
{
  "questions": [
    {
      "question_text": "빈 칸을 채워주세요: ___는 중요한 개념입니다.",
      "correct_answer": "정답",
      "explanation": "정답 해설",
      "keywords": ["키워드1", "키워드2"],
      "difficulty": 3
    }
  ]
}
"""
        else:
            prompt += """
{
  "questions": [
    {
      "question_text": "문제 내용",
      "correct_answer": "정답 또는 예시 답안",
      "explanation": "정답 해설",
      "keywords": ["키워드1", "키워드2"],
      "difficulty": 3
    }
  ]
}
"""
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for question generation
        """
        return """
당신은 교육 콘텐츠 전문가입니다. 주어진 학습 자료를 바탕으로 학습자의 이해도를 평가할 수 있는 양질의 문제를 생성합니다.

**문제 생성 원칙:**
1. 콘텐츠의 핵심 개념을 다루어야 합니다
2. 명확하고 모호하지 않은 문제를 만들어야 합니다
3. 지정된 난이도에 적합해야 합니다
4. 학습 목표에 부합해야 합니다
5. 객관식의 경우 매력적인 오답지를 포함해야 합니다

반드시 지정된 JSON 형식으로 응답하세요.
"""
    
    def _process_generated_questions(self, response_data: Dict, content: Content, 
                                   question_type: AIQuestionType, processing_time: int) -> List[Dict]:
        """
        Process and validate generated questions
        """
        if 'questions' not in response_data:
            raise AIServiceError("No questions found in AI response")
        
        processed_questions = []
        
        for q_data in response_data['questions']:
            try:
                # Validate required fields
                required_fields = ['question_text', 'correct_answer']
                self._validate_response_structure(q_data, required_fields)
                
                # Quality check
                if not self._validate_question_quality(q_data, question_type):
                    continue
                
                processed_question = {
                    'question_text': q_data['question_text'],
                    'correct_answer': q_data['correct_answer'],
                    'explanation': q_data.get('explanation', ''),
                    'keywords': q_data.get('keywords', []),
                    'difficulty': q_data.get('difficulty', 3),
                    'options': q_data.get('options'),
                    'question_type': question_type.name,
                    'content_id': content.id,
                    'processing_time_ms': processing_time,
                }
                
                processed_questions.append(processed_question)
                
            except Exception as e:
                logger.warning(f"Skipping invalid question: {str(e)}")
                continue
        
        return processed_questions
    
    def _validate_question_quality(self, question_data: Dict, question_type: AIQuestionType) -> bool:
        """
        Validate the quality of a generated question
        """
        # Basic validation
        question_text = question_data.get('question_text', '').strip()
        correct_answer = question_data.get('correct_answer', '').strip()
        
        if len(question_text) < 10 or len(correct_answer) < 1:
            logger.warning("Question rejected due to insufficient length")
            return False
        
        # Type-specific validation
        if question_type.name == 'multiple_choice':
            options = question_data.get('options', [])
            if not options or len(options) < 2:
                logger.warning("Multiple choice question rejected: insufficient options")
                return False
            
            if correct_answer not in options:
                logger.warning("Multiple choice question rejected: correct answer not in options")
                return False
        
        return True
    
    def save_generated_questions(self, questions_data: List[Dict], user) -> List[AIQuestion]:
        """
        Save generated questions to database
        """
        saved_questions = []
        
        for q_data in questions_data:
            try:
                content = Content.objects.get(id=q_data['content_id'])
                question_type = AIQuestionType.objects.get(name=q_data['question_type'])
                
                ai_question = AIQuestion.objects.create(
                    content=content,
                    question_type=question_type,
                    question_text=q_data['question_text'],
                    correct_answer=q_data['correct_answer'],
                    options=q_data.get('options'),
                    difficulty=q_data.get('difficulty', 3),
                    explanation=q_data.get('explanation', ''),
                    keywords=q_data.get('keywords', []),
                    ai_model_used=self.model,
                )
                
                saved_questions.append(ai_question)
                
            except Exception as e:
                logger.error(f"Failed to save question: {str(e)}")
                continue
        
        return saved_questions