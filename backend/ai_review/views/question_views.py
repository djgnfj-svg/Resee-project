"""
AI Question Generation and Management Views
"""
import logging

from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from accounts.models import AIUsageTracking
from content.models import Content
from resee.structured_logging import ai_logger, log_api_call, log_performance

from ..models import AIQuestion, AIQuestionType
from ..serializers import (
    AIQuestionSerializer,
    AIQuestionTypeSerializer,
    BlurRegionsRequestSerializer,
    BlurRegionsResponseSerializer,
    FillBlankRequestSerializer,
    FillBlankResponseSerializer,
    GeneratedQuestionSerializer,
    GenerateQuestionsSerializer
)
from ..services import AIServiceError
from .base import BaseAIView

logger = logging.getLogger(__name__)


class AIQuestionTypeListView(ListAPIView):
    """
    List all active AI question types
    """
    serializer_class = AIQuestionTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return AIQuestionType.objects.filter(is_active=True)


class GenerateQuestionsView(BaseAIView):
    """
    Generate AI questions for given content
    """
    
    @swagger_auto_schema(
        request_body=GenerateQuestionsSerializer,
        responses={
            200: openapi.Response(
                'Success',
                GeneratedQuestionSerializer(many=True)
            ),
            400: 'Bad Request',
            404: 'Content not found',
            500: 'AI service error'
        },
        operation_description="Generate AI questions for content using specified types and difficulty"
    )
    @log_api_call
    @log_performance('ai_question_generation')
    def post(self, request):
        """Generate questions for content"""
        
        serializer = GenerateQuestionsSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get validated data
        content_id = serializer.validated_data['content_id']
        question_types = serializer.validated_data['question_types']
        difficulty = serializer.validated_data['difficulty']
        count = serializer.validated_data['count']
        
        # Check question type availability for user's subscription
        available_features = request.user.get_ai_features_list()
        for qtype in question_types:
            if qtype not in available_features:
                return Response(
                    {
                        'error': 'Question type not available',
                        'detail': f'Question type "{qtype}" is not available in your subscription tier.',
                        'available_features': available_features
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Check daily usage limit
        limit_response = self.check_daily_limit(request, count)
        if limit_response:
            return limit_response
        
        # Get content
        content = self.get_user_content(request, content_id)
        
        try:
            # Log AI question generation attempt
            ai_logger.log_question_generation(
                user_id=request.user.id,
                content_id=content_id,
                question_types=question_types,
                count=count,
                success=False  # Will update to True if successful
            )
            
            # Generate questions using AI service
            generated_questions = self.ai_service.generate_questions(
                content=content,
                question_types=question_types,
                difficulty=difficulty,
                count=count
            )
            
            # Save generated questions to database
            saved_questions = []
            for q_data in generated_questions:
                # Get question type
                question_type = get_object_or_404(
                    AIQuestionType,
                    name=q_data['question_type'],
                    is_active=True
                )
                
                # Create and save question
                ai_question = AIQuestion.objects.create(
                    content=content,
                    question_type=question_type,
                    question_text=q_data['question_text'],
                    correct_answer=q_data['correct_answer'],
                    options=q_data.get('options'),
                    difficulty=difficulty,
                    explanation=q_data.get('explanation', ''),
                    keywords=q_data.get('keywords'),
                    ai_model_used=q_data.get('ai_model_used', ''),
                    generation_prompt=q_data.get('generation_prompt', '')
                )
                saved_questions.append(ai_question)
            
            # Track usage
            self.track_usage(request, len(saved_questions))
            
            # Serialize response
            response_serializer = AIQuestionSerializer(saved_questions, many=True)
            
            # Log successful generation
            ai_logger.log_question_generation(
                user_id=request.user.id,
                content_id=content_id,
                question_types=question_types,
                count=len(saved_questions),
                success=True,
                generated_count=len(saved_questions),
                subscription_tier=request.user.subscription.tier,
                processing_time_ms=sum(q.get('processing_time_ms', 0) for q in generated_questions)
            )
            
            logger.info(
                f"Generated {len(saved_questions)} AI questions for content {content.id} "
                f"(user: {request.user.email}, tier: {request.user.subscription.tier})"
            )
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except AIServiceError as e:
            return self.handle_ai_service_error(e, request.user.email)
        except Exception as e:
            return self.handle_unexpected_error(e, 'Question generation')


class ContentQuestionsView(ListAPIView):
    """
    List AI questions for specific content
    """
    serializer_class = AIQuestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="콘텐츠별 AI 질문 조회",
        operation_description="""
        특정 콘텐츠에 대해 생성된 AI 질문들을 조회합니다.
        
        **응답 데이터:**
        - 해당 콘텐츠에 대해 생성된 모든 AI 질문
        - 질문 유형, 난이도, 생성 시간 등 메타데이터 포함
        - 비활성화된 질문은 제외
        
        **권한:**
        - 본인이 작성한 콘텐츠의 질문만 조회 가능
        """,
        tags=['AI Review'],
        responses={
            200: AIQuestionSerializer(many=True),
            401: "인증 필요",
            404: "콘텐츠를 찾을 수 없음",
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        content_id = self.kwargs['content_id']
        # Ensure user owns the content
        content = get_object_or_404(Content, id=content_id, author=self.request.user)
        
        return AIQuestion.objects.filter(
            content=content,
            is_active=True
        ).select_related('content', 'question_type')\
         .prefetch_related('feedback')\
         .order_by('-created_at')


class GenerateFillBlanksView(BaseAIView):
    """
    Generate fill-in-the-blank questions for content
    """
    
    @swagger_auto_schema(
        operation_summary="빈칸 채우기 문제 생성",
        operation_description="""
        콘텐츠에서 중요한 부분을 뺈칸으로 처리하여 학습 문제를 생성합니다.
        
        **요청 예시:**
        ```json
        {
          "content_id": 123,
          "num_blanks": 3
        }
        ```
        
        **응답 예시:**
        ```json
        {
          "blanked_text": "Python은 _____(빈칸1)이며, _____(빈칸2) 언어입니다.",
          "answers": {
            "빈칸1": "해석형 언어",
            "빈칸2": "객체지향"
          },
          "keywords": ["Python", "해석형", "객체지향"]
        }
        ```
        
        **구독 티어 제한:**
        - Premium 이상 티어에서만 사용 가능
        """,
        tags=['AI Review'],
        request_body=FillBlankRequestSerializer,
        responses={
            200: FillBlankResponseSerializer,
            400: '잘못된 요청 - 유효성 검사 실패',
            403: '구독 티어 부족 - Premium 이상 필요',
            404: '콘텐츠를 찾을 수 없음',
            503: 'AI 서비스 일시적 사용 불가',
            500: 'AI 서비스 오류'
        }
    )
    def post(self, request):
        """Generate fill-in-the-blank exercise"""
        serializer = FillBlankRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        content_id = serializer.validated_data['content_id']
        num_blanks = serializer.validated_data['num_blanks']
        
        # Get content
        content = self.get_user_content(request, content_id)
        
        try:
            # Generate fill blanks using AI service
            result = self.ai_service.generate_fill_blanks(
                content_text=content.content,
                num_blanks=num_blanks
            )
            
            logger.info(
                f"Generated {num_blanks} fill-blanks for content {content.id} "
                f"(user: {request.user.email})"
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except AIServiceError as e:
            return self.handle_ai_service_error(e, request.user.email)
        except Exception as e:
            return self.handle_unexpected_error(e, 'Fill-blank generation')


class IdentifyBlurRegionsView(BaseAIView):
    """
    Identify regions for blur processing in content
    """
    
    @swagger_auto_schema(
        operation_summary="블러 처리 영역 식별",
        operation_description="""
        콘텐츠에서 블러 처리할 중요 영역을 AI로 식별합니다.
        
        **요청 예시:**
        ```json
        {
          "content_id": 123
        }
        ```
        
        **응답 예시:**
        ```json
        {
          "blur_regions": [
            {
              "text": "해석형 언어",
              "start_pos": 15,
              "end_pos": 21,
              "importance": 0.9,
              "concept_type": "definition"
            }
          ],
          "concepts": ["Python", "해석형 언어", "객체지향"]
        }
        ```
        
        **기능 설명:**
        - 중요한 개념, 정의, 예시 등을 자동 식별
        - 중요도 점수를 통한 블러 우선순위 제공
        - 게임형 학습으로 기억 효과 증대
        
        **구독 티어 제한:**
        - Pro 티어에서만 사용 가능
        """,
        tags=['AI Review'],
        request_body=BlurRegionsRequestSerializer,
        responses={
            200: BlurRegionsResponseSerializer,
            400: '잘못된 요청 - 유효성 검사 실패',
            403: '구독 티어 부족 - Pro 티어 필요',
            404: '콘텐츠를 찾을 수 없음',
            503: 'AI 서비스 일시적 사용 불가',
            500: 'AI 서비스 오류'
        }
    )
    def post(self, request):
        """Identify blur regions in content"""
        serializer = BlurRegionsRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        content_id = serializer.validated_data['content_id']
        
        # Get content
        content = self.get_user_content(request, content_id)
        
        try:
            # Identify blur regions using AI service
            result = self.ai_service.identify_blur_regions(
                content_text=content.content
            )
            
            logger.info(
                f"Identified {len(result.get('blur_regions', []))} blur regions for content {content.id} "
                f"(user: {request.user.email})"
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except AIServiceError as e:
            return self.handle_ai_service_error(e, request.user.email)
        except Exception as e:
            return self.handle_unexpected_error(e, 'Blur region identification')