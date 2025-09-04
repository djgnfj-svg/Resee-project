"""
AI Answer Evaluation Service
"""
import logging
from typing import Dict, List, Optional

from ..models import AIEvaluation, AIQuestion
from .base_ai_service import BaseAIService, AIServiceError
from ..mock_responses import AIMockResponses

logger = logging.getLogger(__name__)


class AnswerEvaluatorService(BaseAIService):
    """
    Service for evaluating user answers using AI
    """
    
    def evaluate_answer(self, question: AIQuestion, user_answer: str, user) -> Dict:
        """
        Evaluate a user's answer to an AI question
        
        Args:
            question: AIQuestion object
            user_answer: User's answer text
            user: User who provided the answer
            
        Returns:
            Dictionary with evaluation results
        """
        try:
            # Use mock responses if enabled
            if self.use_mock_responses:
                logger.info("Using mock responses for answer evaluation")
                mock_response = AIMockResponses.get_answer_evaluation_response(
                    question_text=question.question_text,
                    correct_answer=question.correct_answer,
                    user_answer=user_answer,
                    question_type=question.question_type.name
                )
                
                evaluation_result = self._process_evaluation_result(
                    mock_response, question, user_answer, user, 120  # Mock processing time
                )
                return evaluation_result
            
            # Real AI implementation
            prompt = self._build_evaluation_prompt(question, user_answer)
            
            messages = [
                {"role": "system", "content": self._get_evaluation_system_prompt()},
                {"role": "user", "content": prompt}
            ]
            
            response_text, processing_time = self._make_api_call(messages)
            evaluation_data = self._parse_json_response(response_text)
            
            # Validate and process evaluation
            evaluation_result = self._process_evaluation_result(
                evaluation_data, question, user_answer, user, processing_time
            )
            
            return evaluation_result
            
        except Exception as e:
            logger.error(f"Failed to evaluate answer: {str(e)}")
            raise AIServiceError(f"Answer evaluation failed: {str(e)}")
    
    def _build_evaluation_prompt(self, question: AIQuestion, user_answer: str) -> str:
        """
        Build prompt for answer evaluation
        """
        return f"""
다음 문제에 대한 사용자의 답변을 평가해주세요.

**문제 정보:**
문제: {question.question_text}
정답: {question.correct_answer}
문제 유형: {question.question_type.display_name}
설명: {question.explanation}

**사용자 답변:**
{user_answer}

**평가 요청:**
사용자의 답변을 0.0에서 1.0 사이의 점수로 평가하고, 상세한 피드백을 제공해주세요.

**응답 형식 (JSON):**
{{
  "score": 0.85,
  "feedback": "답변이 대부분 정확하지만 일부 개선이 필요합니다. ...",
  "similarity_score": 0.80,
  "evaluation_details": {{
    "strengths": ["정확한 핵심 개념 이해", "논리적 설명"],
    "weaknesses": ["구체적 예시 부족", "일부 용어 오용"],
    "suggestions": ["더 구체적인 예시 추가", "정확한 용어 사용"]
  }}
}}
"""
    
    def _get_evaluation_system_prompt(self) -> str:
        """
        Get system prompt for answer evaluation
        """
        return """
당신은 교육 평가 전문가입니다. 학습자의 답변을 공정하고 건설적으로 평가합니다.

**평가 기준:**
1. 정확성 (40%): 답변이 얼마나 정확한가?
2. 완성도 (30%): 답변이 얼마나 완전한가?
3. 이해도 (20%): 핵심 개념을 얼마나 잘 이해하고 있는가?
4. 설명력 (10%): 답변이 얼마나 명확하게 설명되어 있는가?

**점수 기준:**
- 1.0: 완벽한 답변
- 0.8-0.9: 우수한 답변 (소소한 개선점 있음)
- 0.6-0.7: 양호한 답변 (일부 오류나 누락 있음)
- 0.4-0.5: 보통 답변 (상당한 개선 필요)
- 0.2-0.3: 미흡한 답변 (대부분 틀림)
- 0.0-0.1: 매우 미흡한 답변 (거의 틀림 또는 무관한 답변)

피드백은 건설적이고 구체적으로 작성하며, 학습자가 개선할 수 있는 방향을 제시해주세요.
반드시 지정된 JSON 형식으로 응답하세요.
"""
    
    def _process_evaluation_result(self, evaluation_data: Dict, question: AIQuestion, 
                                 user_answer: str, user, processing_time: int) -> Dict:
        """
        Process and save evaluation result
        """
        # Validate evaluation data
        required_fields = ['score', 'feedback']
        self._validate_response_structure(evaluation_data, required_fields)
        
        score = float(evaluation_data['score'])
        if not 0.0 <= score <= 1.0:
            raise AIServiceError("Score must be between 0.0 and 1.0")
        
        # Create evaluation record
        ai_evaluation = AIEvaluation.objects.create(
            question=question,
            user=user,
            user_answer=user_answer,
            ai_score=score,
            feedback=evaluation_data['feedback'],
            similarity_score=evaluation_data.get('similarity_score'),
            evaluation_details=evaluation_data.get('evaluation_details', {}),
            ai_model_used=self.model,
            processing_time_ms=processing_time,
        )
        
        return {
            'evaluation_id': ai_evaluation.id,
            'score': score,
            'feedback': evaluation_data['feedback'],
            'similarity_score': evaluation_data.get('similarity_score'),
            'evaluation_details': evaluation_data.get('evaluation_details', {}),
            'processing_time_ms': processing_time,
        }
    
    def get_evaluation_summary(self, user, content=None, days=30) -> Dict:
        """
        Get evaluation summary for a user
        """
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Avg, Count
        
        since_date = timezone.now() - timedelta(days=days)
        evaluations = AIEvaluation.objects.filter(
            user=user,
            created_at__gte=since_date
        )
        
        if content:
            evaluations = evaluations.filter(question__content=content)
        
        summary = evaluations.aggregate(
            total_evaluations=Count('id'),
            average_score=Avg('ai_score'),
            average_similarity=Avg('similarity_score'),
        )
        
        # Calculate score distribution
        score_ranges = {
            'excellent': evaluations.filter(ai_score__gte=0.9).count(),
            'good': evaluations.filter(ai_score__gte=0.7, ai_score__lt=0.9).count(),
            'fair': evaluations.filter(ai_score__gte=0.5, ai_score__lt=0.7).count(),
            'poor': evaluations.filter(ai_score__lt=0.5).count(),
        }
        
        return {
            'summary': summary,
            'score_distribution': score_ranges,
            'period_days': days,
        }
    
    def get_weak_areas(self, user, content=None, min_evaluations=3) -> List[Dict]:
        """
        Identify weak areas based on evaluation results
        """
        from django.db.models import Avg, Count
        
        evaluations = AIEvaluation.objects.filter(user=user)
        if content:
            evaluations = evaluations.filter(question__content=content)
        
        # Group by question keywords and analyze performance
        weak_areas = []
        
        # This is a simplified version - you might want to implement
        # more sophisticated analysis based on keywords, topics, etc.
        low_score_evaluations = evaluations.filter(ai_score__lt=0.6)
        
        for evaluation in low_score_evaluations.select_related('question'):
            if evaluation.question.keywords:
                for keyword in evaluation.question.keywords:
                    weak_areas.append({
                        'keyword': keyword,
                        'score': evaluation.ai_score,
                        'question_type': evaluation.question.question_type.name,
                    })
        
        return weak_areas