"""
AI Answer Evaluation Views
"""
import logging

from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response

from ..models import AIQuestion
from ..serializers import (
    ExplanationEvaluationRequestSerializer,
    ExplanationEvaluationResponseSerializer
)
from ..services import AIServiceError
from .base import BaseAIView

logger = logging.getLogger(__name__)


class AIAnswerEvaluationView(BaseAIView):
    """
    Evaluate user answers using AI
    """
    
    @swagger_auto_schema(
        operation_summary="AI 답변 평가",
        operation_description="""
        사용자의 답변을 AI로 평가하여 점수와 피드백을 제공합니다.
        
        **요청 예시:**
        ```json
        {
          "question_id": 123,
          "user_answer": "Python은 해석형 언어입니다."
        }
        ```
        
        **응답 예시:**
        ```json
        {
          "id": 456,
          "score": 0.85,
          "feedback": "정답에 가깝습니다. 하지만 객체지향 특성도 언급하면 더 완전한 답변이 됩니다.",
          "similarity_score": 0.78,
          "evaluation_details": {
            "strengths": ["기본 개념 이해가 정확함"],
            "weaknesses": ["부분적 설명"],
            "suggestions": ["객체지향 프로그래밍 언어라는 점도 추가해보세요"]
          }
        }
        ```
        
        **채점 기준:**
        - 0.9-1.0: 우수 (완벽한 이해)
        - 0.7-0.8: 양호 (대부분 정확)
        - 0.5-0.6: 보통 (부분적 이해)
        - 0.3-0.4: 미흡 (기본 이해 부족)
        - 0.0-0.2: 부족 (이해 부족)
        """,
        tags=['AI Review'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'question_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="평가할 질문 ID"),
                'user_answer': openapi.Schema(type=openapi.TYPE_STRING, description="사용자의 답변"),
            },
            required=['question_id', 'user_answer']
        ),
        responses={
            201: openapi.Response(
                description="답변 평가 완료",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="평가 기록 ID"),
                        'score': openapi.Schema(type=openapi.TYPE_NUMBER, description="AI 평가 점수 (0.0-1.0)"),
                        'feedback': openapi.Schema(type=openapi.TYPE_STRING, description="AI 피드백"),
                        'similarity_score': openapi.Schema(type=openapi.TYPE_NUMBER, description="의미적 유사도 점수"),
                        'evaluation_details': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'strengths': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                                'weaknesses': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                                'suggestions': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                            }
                        ),
                        'processing_time_ms': openapi.Schema(type=openapi.TYPE_INTEGER, description="AI 처리 시간"),
                    }
                )
            ),
            400: '잘못된 요청 - 유효성 검사 실패',
            403: 'AI 기능 사용 불가 - 구독 업그레이드 필요',
            404: '질문을 찾을 수 없음',
            429: '일일 한도 초과',
            503: 'AI 서비스 일시적 사용 불가',
            500: 'AI 서비스 오류'
        }
    )
    def post(self, request):
        """Evaluate user answer with AI"""
        # AI 서비스 미구현 알림
        return Response(
            {
                'error': 'AI 서비스 미구현',
                'detail': 'AI 답변 평가 기능은 현재 개발 중입니다. 곧 제공될 예정이니 조금만 기다려주세요! 🚀',
                'status': 'under_development'
            },
            status=status.HTTP_501_NOT_IMPLEMENTED
        )
        
        # Implementation plan:
        """
        Future implementation will include:
        1. AI feature access validation
        2. Answer evaluation using AI service
        3. Feedback generation and scoring
        4. Usage tracking and analytics
        
        Currently returns not implemented status.
        
        Example implementation structure:
        # Check AI feature access
        access_response = self.check_ai_feature_access(request)
        if access_response:
            return access_response
        
        question_id = request.data.get('question_id')
        user_answer = request.data.get('user_answer')
        
        if not question_id or not user_answer:
            return Response(
                {'error': 'question_id and user_answer are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check daily usage limit
        limit_response = self.check_daily_limit(request, 1)  # 1 evaluation = 1 credit
        if limit_response:
            return limit_response
        
        # Get question and verify ownership through content
        try:
            question = AIQuestion.objects.select_related('content').get(
                id=question_id,
                content__author=request.user,
                is_active=True
            )
        except AIQuestion.DoesNotExist:
            return Response(
                {'error': 'Question not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Evaluate answer using AI service
            evaluation_result = self.ai_service.evaluate_answer(question, user_answer)
            
            # Create evaluation record
            evaluation = AIEvaluation.objects.create(
                question=question,
                user=request.user,
                user_answer=user_answer,
                ai_score=evaluation_result['score'],
                feedback=evaluation_result.get('feedback', ''),
                similarity_score=evaluation_result.get('similarity_score'),
                evaluation_details=evaluation_result.get('evaluation_details'),
                ai_model_used=evaluation_result.get('ai_model_used', ''),
                processing_time_ms=evaluation_result.get('processing_time_ms')
            )
            
            # Track usage
            self.track_usage(request, 1)
            
            logger.info(
                f"AI answer evaluation completed for question {question.id} "
                f"(user: {request.user.email}, score: {evaluation.ai_score})"
            )
            
            # Return evaluation result
            response_data = {
                'id': evaluation.id,
                'score': evaluation.ai_score,
                'feedback': evaluation.feedback,
                'similarity_score': evaluation.similarity_score,
                'evaluation_details': evaluation.evaluation_details,
                'processing_time_ms': evaluation.processing_time_ms,
                'question_id': question.id,
                'user_answer': user_answer
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except AIServiceError as e:
            return self.handle_ai_service_error(e, request.user.email)
        except Exception as e:
            return self.handle_unexpected_error(e, 'Answer evaluation')
        """


class ExplanationEvaluationView(BaseAIView):
    """
    Evaluate user's descriptive explanation using AI
    """
    
    @swagger_auto_schema(
        operation_summary="서술형 설명 평가",
        operation_description="""
        사용자가 작성한 서술형 설명을 AI로 평가하여 점수와 피드백을 제공합니다.
        
        **요청 예시:**
        ```json
        {
          "content_id": 123,
          "user_explanation": "Python은 해석형 언어로서 코드를 한 줄씩 실행합니다..."
        }
        ```
        
        **응답 예시:**
        ```json
        {
          "score": 85,
          "feedback": "핵심 개념을 잘 이해하고 있습니다. 객체지향 특성도 언급하면 더 완전한 설명이 됩니다.",
          "strengths": ["기본 개념 이해가 정확함", "논리적 구조가 좋음"],
          "improvements": ["더 구체적인 예시 추가", "객체지향 특성 언급"],
          "key_concepts_covered": ["해석형 언어", "실행 방식"],
          "missing_concepts": ["객체지향", "동적 타이핑"]
        }
        ```
        
        **평가 기준:**
        - 핵심 개념 이해도 (40%)
        - 설명의 완성도 (30%)
        - 논리적 구조 (20%)
        - 구체적 예시나 세부사항 (10%)
        
        **구독 티어 제한:**
        - Basic 이상 티어에서만 사용 가능
        """,
        tags=['AI Review'],
        request_body=ExplanationEvaluationRequestSerializer,
        responses={
            200: ExplanationEvaluationResponseSerializer,
            400: '잘못된 요청 - 유효성 검사 실패',
            403: '구독 티어 부족 - Basic 이상 필요',
            404: '콘텐츠를 찾을 수 없음',
            429: '일일 한도 초과',
            503: 'AI 서비스 일시적 사용 불가',
            500: 'AI 서비스 오류'
        }
    )
    def post(self, request):
        """Evaluate user's descriptive explanation"""
        # Check AI feature access
        access_response = self.check_ai_feature_access(request, 'explanation_evaluation')
        if access_response:
            return access_response
        
        serializer = ExplanationEvaluationRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        content_id = serializer.validated_data['content_id']
        user_explanation = serializer.validated_data['user_explanation']
        
        # Check daily usage limit
        limit_response = self.check_daily_limit(request, 1)  # 1 evaluation = 1 credit
        if limit_response:
            return limit_response
        
        # Get content
        content = self.get_user_content(request, content_id)
        
        try:
            # Evaluate explanation using AI service
            result = self.ai_service.evaluate_explanation(
                content=content,
                user_explanation=user_explanation
            )
            
            # Track usage
            self.track_usage(request, 1)
            
            logger.info(
                f"AI explanation evaluation for content {content.id} "
                f"(user: {request.user.email}, score: {result['score']})"
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except AIServiceError as e:
            return self.handle_ai_service_error(e, request.user.email)
        except Exception as e:
            return self.handle_unexpected_error(e, 'Explanation evaluation')