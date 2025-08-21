"""
AI Review API views
"""
import logging

from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import AIUsageTracking
from content.models import Content
from resee.structured_logging import ai_logger, log_api_call, log_performance
from resee.throttling import AIEndpointThrottle
from resee.permissions import AIFeaturesRequired

from .models import (AIAdaptiveDifficultyTest, AIQuestion, AIQuestionType, AIReviewSession, AIStudyMate,
                     AISummaryNote, InstantContentCheck, LearningAnalytics,
                     WeeklyTest, WeeklyTestQuestion)
from .serializers import (AIChatRequestSerializer,  # 새로운 시리얼라이저들
                          AIChatResponseSerializer, AIQuestionSerializer,
                          AIQuestionTypeSerializer, AIReviewSessionSerializer,
                          AIStudyMateSerializer, AISummaryNoteSerializer,
                          AdaptiveTestStartSerializer, AdaptiveTestAnswerSerializer,
                          AnalyticsRequestSerializer,
                          BlurRegionsRequestSerializer,
                          BlurRegionsResponseSerializer,
                          ExplanationEvaluationRequestSerializer,
                          ExplanationEvaluationResponseSerializer,
                          FillBlankRequestSerializer,
                          FillBlankResponseSerializer,
                          GeneratedQuestionSerializer,
                          GenerateQuestionsSerializer,
                          InstantCheckRequestSerializer,
                          InstantContentCheckSerializer,
                          LearningAnalyticsSerializer,
                          StudyMateRequestSerializer,
                          SummaryNoteRequestSerializer,
                          WeeklyTestAnswerSerializer,
                          WeeklyTestCreateSerializer,
                          WeeklyTestQuestionSerializer, WeeklyTestSerializer,
                          WeeklyTestStartSerializer)
from .services import AIServiceError, question_generator, answer_evaluator, QuestionGeneratorService
from .serializers import GenerateQuestionsSerializer

logger = logging.getLogger(__name__)

# Initialize AI service
from .services.question_generator import QuestionGeneratorService
ai_service = QuestionGeneratorService()


class AIQuestionTypeListView(ListAPIView):
    """
    List all active AI question types
    """
    serializer_class = AIQuestionTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return AIQuestionType.objects.filter(is_active=True)


class GenerateQuestionsView(APIView):
    """
    Generate AI questions for given content
    """
    permission_classes = [permissions.IsAuthenticated, AIFeaturesRequired]
    throttle_classes = [AIEndpointThrottle]
    
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
        usage_record = AIUsageTracking.get_or_create_for_today(request.user)
        if not usage_record.can_generate_questions(count):
            daily_limit = request.user.get_ai_question_limit()
            remaining = daily_limit - usage_record.questions_generated
            return Response(
                {
                    'error': 'Daily limit exceeded',
                    'detail': f'You have reached your daily limit of {daily_limit} questions. '
                             f'You have {max(0, remaining)} questions remaining today.',
                    'daily_limit': daily_limit,
                    'used_today': usage_record.questions_generated,
                    'remaining_today': max(0, remaining)
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Get content
        content = get_object_or_404(Content, id=content_id, author=request.user)
        
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
            generated_questions = ai_service.generate_questions(
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
            usage_record.increment_questions(len(saved_questions))
            
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
            logger.error(f"AI service error for user {request.user.email}: {str(e)}")
            return Response(
                {'error': 'AI service temporarily unavailable', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Unexpected error generating questions: {str(e)}")
            return Response(
                {'error': 'Failed to generate questions'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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



class AIReviewSessionListView(ListAPIView):
    """
    List user's AI review sessions
    """
    serializer_class = AIReviewSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="AI 복습 세션 목록 조회",
        operation_description="""
        사용자의 AI 복습 세션 목록을 조회합니다.
        
        **응답 데이터:**
        - AI 복습 세션 내역 (생성된 질문 수, 답변한 질문 수 등)
        - 세션 지속 시간 및 AI 처리 시간
        - 평균 점수 및 완료율
        - 관련 콘텐츠 및 카테고리 정보
        
        **정렬:**
        - 최근 세션부터 정렬 (생성 시간 역순)
        """,
        tags=['AI Review'],
        responses={
            200: AIReviewSessionSerializer(many=True),
            401: "인증 필요",
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        return AIReviewSession.objects.filter(
            review_history__user=self.request.user
        ).select_related(
            'review_history', 
            'review_history__content',
            'review_history__content__category',
            'review_history__user'
        ).prefetch_related(
            'review_history__content__ai_questions'
        ).order_by('-created_at')

class GenerateFillBlanksView(APIView):
    """
    Generate fill-in-the-blank questions for content
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIEndpointThrottle]
    
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
        content = get_object_or_404(Content, id=content_id, author=request.user)
        
        try:
            # Generate fill blanks using AI service
            result = ai_service.generate_fill_blanks(
                content_text=content.content,
                num_blanks=num_blanks
            )
            
            logger.info(
                f"Generated {num_blanks} fill-blanks for content {content.id} "
                f"(user: {request.user.email})"
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except AIServiceError as e:
            logger.error(f"AI fill-blank error for user {request.user.email}: {str(e)}")
            return Response(
                {'error': 'AI service temporarily unavailable', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Unexpected error generating fill-blanks: {str(e)}")
            return Response(
                {'error': 'Failed to generate fill-blanks'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IdentifyBlurRegionsView(APIView):
    """
    Identify regions for blur processing in content
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIEndpointThrottle]
    
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
        content = get_object_or_404(Content, id=content_id, author=request.user)
        
        try:
            # Identify blur regions using AI service
            result = ai_service.identify_blur_regions(
                content_text=content.content
            )
            
            logger.info(
                f"Identified {len(result.get('blur_regions', []))} blur regions for content {content.id} "
                f"(user: {request.user.email})"
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except AIServiceError as e:
            logger.error(f"AI blur regions error for user {request.user.email}: {str(e)}")
            return Response(
                {'error': 'AI service temporarily unavailable', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Unexpected error identifying blur regions: {str(e)}")
            return Response(
                {'error': 'Failed to identify blur regions'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@swagger_auto_schema(
    method='get',
    responses={200: 'AI Review system status'},
    operation_description="Check AI Review system health"
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ai_review_health(request):
    """Check AI review system health"""
    try:
        # Simple check - count question types
        question_types_count = AIQuestionType.objects.filter(is_active=True).count()
        
        return Response({
            'status': 'healthy',
            'active_question_types': question_types_count,
            'ai_service_available': hasattr(ai_service, 'client')
        })
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIAnswerEvaluationView(APIView):
    """
    Evaluate user answers using AI
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIEndpointThrottle]
    
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
        
        # 아래는 추후 구현 시 활성화할 코드
        """
        # Check AI feature access
        if not request.user.can_use_ai_features():
            return Response(
                {
                    'error': 'AI features not available',
                    'detail': 'Please upgrade your subscription and verify your email to access AI features.',
                    'requires_subscription': True
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        question_id = request.data.get('question_id')
        user_answer = request.data.get('user_answer')
        
        if not question_id or not user_answer:
            return Response(
                {'error': 'question_id and user_answer are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check daily usage limit
        usage_record = AIUsageTracking.get_or_create_for_today(request.user)
        if not usage_record.can_generate_questions(1):  # 1 evaluation = 1 credit
            daily_limit = request.user.get_ai_question_limit()
            remaining = daily_limit - usage_record.questions_generated
            return Response(
                {
                    'error': 'Daily limit exceeded',
                    'detail': f'You have reached your daily limit of {daily_limit} AI interactions. '
                             f'You have {max(0, remaining)} interactions remaining today.',
                    'daily_limit': daily_limit,
                    'used_today': usage_record.questions_generated,
                    'remaining_today': max(0, remaining)
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
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
            evaluation_result = ai_service.evaluate_answer(question, user_answer)
            
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
            
            # Track usage (1 evaluation = 1 credit)
            usage_record.increment_questions(1)
            
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
            logger.error(f"AI evaluation error for user {request.user.email}: {str(e)}")
            return Response(
                {'error': 'AI service temporarily unavailable', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Unexpected error in AI evaluation: {str(e)}")
            return Response(
                {'error': 'Answer evaluation failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        """


class AIChatView(APIView):
    """
    AI chat for learning content
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIEndpointThrottle]
    
    @swagger_auto_schema(
        request_body=AIChatRequestSerializer,
        responses={
            200: AIChatResponseSerializer,
            400: 'Bad Request',
            403: 'Forbidden',
            404: 'Content not found',
            429: 'Rate limit exceeded',
            500: 'AI service error'
        }
    )
    def post(self, request):
        """Chat with AI about learning content"""
        # Check AI feature access
        if not request.user.can_use_ai_features():
            return Response(
                {
                    'error': 'AI features not available',
                    'detail': 'Please upgrade your subscription and verify your email to access AI features.',
                    'requires_subscription': True
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if ai_chat is in available features
        available_features = request.user.get_ai_features_list()
        if 'ai_chat' not in available_features:
            return Response(
                {
                    'error': 'AI chat not available',
                    'detail': 'AI chat is not available in your subscription tier.',
                    'available_features': available_features
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AIChatRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        content_id = serializer.validated_data['content_id']
        message = serializer.validated_data['message']
        
        # Check daily usage limit (reuse question limit for chat)
        usage_record = AIUsageTracking.get_or_create_for_today(request.user)
        if not usage_record.can_generate_questions(1):  # 1 chat = 1 question credit
            daily_limit = request.user.get_ai_question_limit()
            remaining = daily_limit - usage_record.questions_generated
            return Response(
                {
                    'error': 'Daily limit exceeded',
                    'detail': f'You have reached your daily limit of {daily_limit} AI interactions. '
                             f'You have {max(0, remaining)} interactions remaining today.',
                    'daily_limit': daily_limit,
                    'used_today': usage_record.questions_generated,
                    'remaining_today': max(0, remaining)
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Get content
        content = get_object_or_404(Content, id=content_id, author=request.user)
        
        try:
            # Get AI response
            result = ai_service.chat_about_content(
                content_text=content.content,
                content_title=content.title,
                user_message=message
            )
            
            # Track usage (1 chat = 1 credit)
            usage_record.increment_questions(1)
            
            logger.info(
                f"AI chat interaction for content {content.id} "
                f"(user: {request.user.email}, tier: {request.user.subscription.tier})"
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except AIServiceError as e:
            logger.error(f"AI chat error for user {request.user.email}: {str(e)}")
            return Response(
                {'error': 'AI service temporarily unavailable', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Unexpected error in AI chat: {str(e)}")
            return Response(
                {'error': 'AI chat failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExplanationEvaluationView(APIView):
    """
    Evaluate user's descriptive explanation using AI
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIEndpointThrottle]
    
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
        if not request.user.can_use_ai_features():
            return Response(
                {
                    'error': 'AI features not available',
                    'detail': 'Please upgrade your subscription and verify your email to access AI features.',
                    'requires_subscription': True
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if explanation evaluation is in available features
        available_features = request.user.get_ai_features_list()
        if 'explanation_evaluation' not in available_features:
            return Response(
                {
                    'error': 'Explanation evaluation not available',
                    'detail': 'Explanation evaluation is not available in your subscription tier. Please upgrade to Basic or higher.',
                    'available_features': available_features
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
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
        
        # Check daily usage limit (reuse question limit for explanation evaluation)
        usage_record = AIUsageTracking.get_or_create_for_today(request.user)
        if not usage_record.can_generate_questions(1):  # 1 evaluation = 1 credit
            daily_limit = request.user.get_ai_question_limit()
            remaining = daily_limit - usage_record.questions_generated
            return Response(
                {
                    'error': 'Daily limit exceeded',
                    'detail': f'You have reached your daily limit of {daily_limit} AI interactions. '
                             f'You have {max(0, remaining)} interactions remaining today.',
                    'daily_limit': daily_limit,
                    'used_today': usage_record.questions_generated,
                    'remaining_today': max(0, remaining)
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Get content
        content = get_object_or_404(Content, id=content_id, author=request.user)
        
        try:
            # Evaluate explanation using AI service
            result = ai_service.evaluate_explanation(
                content=content,
                user_explanation=user_explanation
            )
            
            # Track usage (1 evaluation = 1 credit)
            usage_record.increment_questions(1)
            
            logger.info(
                f"AI explanation evaluation for content {content.id} "
                f"(user: {request.user.email}, score: {result['score']})"
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except AIServiceError as e:
            logger.error(f"AI explanation evaluation error for user {request.user.email}: {str(e)}")
            return Response(
                {'error': 'AI service temporarily unavailable', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Unexpected error in explanation evaluation: {str(e)}")
            return Response(
                {'error': 'Explanation evaluation failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# 새로운 AI 기능 뷰들
class WeeklyTestView(APIView):
    """주간 시험 관리 뷰"""
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIEndpointThrottle]
    
    @swagger_auto_schema(
        operation_summary="주간 시험 목록 조회",
        responses={
            200: WeeklyTestSerializer(many=True),
            401: "인증 필요"
        }
    )
    def get(self, request):
        """사용자의 주간 시험 목록 조회"""
        tests = WeeklyTest.objects.filter(user=request.user)[:10]
        serializer = WeeklyTestSerializer(tests, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        request_body=WeeklyTestCreateSerializer,
        operation_summary="주간 시험 생성",
        responses={
            201: WeeklyTestSerializer,
            400: "잘못된 요청",
            403: "AI 기능 접근 불가"
        }
    )
    @log_api_call
    @log_performance('weekly_test_creation')
    def post(self, request):
        """새로운 주간 시험 생성"""
        if not request.user.can_use_ai_features():
            return Response(
                {'error': 'AI features not available'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = WeeklyTestCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 이번 주 학습한 콘텐츠 조회
            from datetime import datetime, timedelta

            from django.utils import timezone
            
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            
            # 이번 주 복습한 콘텐츠들 조회
            from review.models import ReviewHistory
            week_contents = Content.objects.filter(
                review_histories__user=request.user,
                review_histories__completed_at__date__gte=week_start,
                review_histories__completed_at__date__lte=week_end
            ).distinct()[:10]
            
            if len(week_contents) < 3:
                return Response(
                    {'error': 'Not enough content for weekly test', 
                     'detail': f'최소 3개 이상의 콘텐츠가 필요합니다. 현재: {len(week_contents)}개'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 주간 시험 생성
            weekly_test = WeeklyTest.objects.create(
                user=request.user,
                week_start_date=week_start,
                week_end_date=week_end,
                time_limit_minutes=serializer.validated_data['time_limit_minutes'],
                difficulty_distribution=serializer.validated_data.get('difficulty_distribution', {
                    'easy': 5, 'medium': 8, 'hard': 2
                }),
                content_coverage=[content.id for content in week_contents],
                status='ready'
            )
            
            logger.info(f"Weekly test created for user {request.user.email}")
            return Response(
                WeeklyTestSerializer(weekly_test).data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Weekly test creation failed: {str(e)}")
            return Response(
                {'error': 'Failed to create weekly test'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WeeklyTestStartView(APIView):
    """주간 시험 시작 뷰"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=WeeklyTestStartSerializer,
        responses={
            200: "시험 시작 성공",
            400: "잘못된 요청"
        }
    )
    def post(self, request):
        """주간 시험 시작"""
        serializer = WeeklyTestStartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        test_id = serializer.validated_data['test_id']
        
        try:
            weekly_test = get_object_or_404(
                WeeklyTest, 
                id=test_id, 
                user=request.user,
                status='ready'
            )
            
            # 시험 시작 처리
            weekly_test.status = 'in_progress'
            weekly_test.started_at = timezone.now()
            weekly_test.save()
            
            # TODO: AI로 문제 생성하여 WeeklyTestQuestion 생성
            
            return Response({
                'message': '주간 시험이 시작되었습니다',
                'test': WeeklyTestSerializer(weekly_test).data
            })
            
        except Exception as e:
            logger.error(f"Weekly test start failed: {str(e)}")
            return Response(
                {'error': 'Failed to start weekly test'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InstantContentCheckView(APIView):
    """실시간 내용 검토 뷰"""
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIEndpointThrottle]
    
    @swagger_auto_schema(
        request_body=InstantCheckRequestSerializer,
        responses={
            200: "검토 완료",
            403: "AI 기능 접근 불가"
        }
    )
    @log_api_call
    @log_performance('instant_content_check')
    def post(self, request):
        """실시간 내용 검토 수행"""
        if not request.user.can_use_ai_features():
            return Response(
                {'error': 'AI features not available'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = InstantCheckRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        content_id = serializer.validated_data['content_id']
        check_point = serializer.validated_data['check_point']
        question_count = serializer.validated_data['question_count']
        
        try:
            content = get_object_or_404(Content, id=content_id, author=request.user)
            
            # AI 서비스로 즉시 검토 수행
            result = ai_service.perform_instant_check(
                content=content,
                check_point=check_point,
                question_count=question_count
            )
            
            # 검토 결과 저장
            instant_check = InstantContentCheck.objects.create(
                user=request.user,
                content=content,
                check_point=check_point,
                questions_count=len(result['questions']),
                understanding_score=75,  # TODO: 실제 점수 계산
                weak_points=[],
                feedback=result['indicators'].get('recommended_action', ''),
                duration_seconds=60  # TODO: 실제 소요 시간
            )
            
            response_data = {
                'check_id': instant_check.id,
                'questions': result['questions'],
                'indicators': result['indicators'],
                'recommendations': result['indicators'].get('recommended_action', '')
            }
            
            return Response(response_data)
            
        except AIServiceError as e:
            return Response(
                {'error': 'AI service error', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Instant check failed: {str(e)}")
            return Response(
                {'error': 'Failed to perform instant check'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LearningAnalyticsView(APIView):
    """학습 분석 뷰"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        query_serializer=AnalyticsRequestSerializer,
        responses={
            200: LearningAnalyticsSerializer,
            403: "AI 기능 접근 불가"
        }
    )
    def get(self, request):
        """학습 분석 데이터 조회"""
        if not request.user.can_use_ai_features():
            return Response(
                {'error': 'AI features not available'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AnalyticsRequestSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        period_type = serializer.validated_data['period_type']
        
        try:
            # 기존 분석 데이터 조회
            analytics = LearningAnalytics.objects.filter(
                user=request.user,
                period_type=period_type
            ).first()
            
            if analytics:
                return Response(LearningAnalyticsSerializer(analytics).data)
            
            # 새 분석 생성 (간단한 예시)
            from datetime import datetime, timedelta
            today = timezone.now().date()
            
            if period_type == 'monthly':
                start_date = today.replace(day=1)
                end_date = today
            else:
                start_date = today - timedelta(days=7)
                end_date = today
            
            analytics = LearningAnalytics.objects.create(
                user=request.user,
                period_type=period_type,
                period_start=start_date,
                period_end=end_date,
                total_study_minutes=120,  # TODO: 실제 데이터
                average_daily_minutes=17,
                peak_study_hour=14,
                efficiency_score=78.5,
                retention_rate=85.2
            )
            
            return Response(LearningAnalyticsSerializer(analytics).data)
            
        except Exception as e:
            logger.error(f"Analytics generation failed: {str(e)}")
            return Response(
                {'error': 'Failed to generate analytics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AIStudyMateView(APIView):
    """AI 스터디 메이트 뷰"""
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIEndpointThrottle]
    
    @swagger_auto_schema(
        request_body=StudyMateRequestSerializer,
        responses={
            200: "스터디 가이드 제공",
            403: "AI 기능 접근 불가"
        }
    )
    @log_api_call
    @log_performance('ai_study_mate')
    def post(self, request):
        """AI 스터디 메이트 가이드 제공"""
        if not request.user.can_use_ai_features():
            return Response(
                {'error': 'AI features not available'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = StudyMateRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        content_id = serializer.validated_data['content_id']
        struggle_point = serializer.validated_data['struggle_point']
        user_level = serializer.validated_data['user_level']
        session_type = serializer.validated_data['session_type']
        
        try:
            content = get_object_or_404(Content, id=content_id, author=request.user)
            
            # AI 스터디 메이트 세션 시작
            study_mate = AIStudyMate.objects.create(
                user=request.user,
                content=content,
                session_type=session_type,
                user_level=user_level
            )
            
            # AI 서비스로 가이드 생성
            result = ai_service.provide_study_mate_guidance(
                user=request.user,
                content=content,
                struggle_point=struggle_point,
                user_level=user_level
            )
            
            # 세션 업데이트
            study_mate.adapted_explanations = [result]
            study_mate.interaction_count = 1
            study_mate.save()
            
            return Response({
                'session_id': study_mate.id,
                'guidance': result,
                'user_level': user_level,
                'session_type': session_type
            })
            
        except AIServiceError as e:
            return Response(
                {'error': 'AI service error', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Study mate guidance failed: {str(e)}")
            return Response(
                {'error': 'Failed to provide study guidance'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AISummaryNoteView(APIView):
    """AI 요약 노트 뷰"""
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIEndpointThrottle]
    
    @swagger_auto_schema(
        request_body=SummaryNoteRequestSerializer,
        responses={
            201: AISummaryNoteSerializer,
            403: "AI 기능 접근 불가"
        }
    )
    @log_api_call 
    @log_performance('ai_summary_note')
    def post(self, request):
        """AI 요약 노트 생성"""
        if not request.user.can_use_ai_features():
            return Response(
                {'error': 'AI features not available'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = SummaryNoteRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        content_id = serializer.validated_data['content_id']
        summary_type = serializer.validated_data['summary_type']
        user_preferences = serializer.validated_data.get('user_preferences')
        
        try:
            content = get_object_or_404(Content, id=content_id, author=request.user)
            
            # 기존 요약 노트 확인
            existing_summary = AISummaryNote.objects.filter(
                content=content,
                user=request.user,
                summary_type=summary_type
            ).first()
            
            if existing_summary:
                return Response(
                    AISummaryNoteSerializer(existing_summary).data,
                    status=status.HTTP_200_OK
                )
            
            # AI 서비스로 요약 생성
            result = ai_service.generate_summary_note(
                content=content,
                summary_type=summary_type,
                user_preferences=user_preferences
            )
            
            # 요약 노트 저장
            summary_note = AISummaryNote.objects.create(
                content=content,
                user=request.user,
                summary_type=summary_type,
                summary_content=result['summary']['main_content'],
                key_concepts=result['key_concepts'],
                important_terms=result.get('important_terms', []),
                visual_elements=result.get('visual_elements', {}),
                study_questions=result.get('study_questions', []),
                word_count=result['metadata']['word_count'],
                compression_ratio=result['metadata']['compression_ratio'],
                ai_model_used=result['metadata']['ai_model_used']
            )
            
            return Response(
                AISummaryNoteSerializer(summary_note).data,
                status=status.HTTP_201_CREATED
            )
            
        except AIServiceError as e:
            return Response(
                {'error': 'AI service error', 'detail': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Summary note generation failed: {str(e)}")
            return Response(
                {'error': 'Failed to generate summary note'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdaptiveTestStartView(APIView):
    """
    Start a new adaptive test
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Start an adaptive test session"""
        # 입력 데이터 검증
        serializer = AdaptiveTestStartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        content_area = serializer.validated_data['content_area']
        target_questions = serializer.validated_data['target_questions']
        
        # AI 기능 사용 가능 여부 확인
        if not request.user.can_use_ai_features():
            return Response(
                {
                    'error': 'AI features not available',
                    'detail': '적응형 시험은 AI 기능입니다. 이메일 인증과 구독 업그레이드가 필요합니다.',
                    'requires_subscription': True
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # 새로운 적응형 시험 생성
            adaptive_test = AIAdaptiveDifficultyTest.objects.create(
                user=request.user,
                content_area=content_area,
                target_questions=target_questions,
                current_difficulty='medium'
            )
            
            # 첫 번째 질문 생성
            first_question = self._generate_question_for_difficulty(adaptive_test.current_difficulty, content_area)
            
            return Response({
                'test': {
                    'id': adaptive_test.id,
                    'content_area': adaptive_test.content_area,
                    'target_questions': adaptive_test.target_questions,
                    'current_difficulty': adaptive_test.current_difficulty,
                    'consecutive_correct': adaptive_test.consecutive_correct,
                    'consecutive_wrong': adaptive_test.consecutive_wrong,
                    'total_questions': adaptive_test.total_questions,
                    'correct_answers': adaptive_test.correct_answers,
                    'started_at': adaptive_test.started_at.isoformat()
                },
                'first_question': first_question
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error starting adaptive test for user {request.user.email}: {e}")
            return Response(
                {'error': '시험 시작 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generate_question_for_difficulty(self, difficulty, content_area):
        """주어진 난이도에 맞는 질문 생성"""
        difficulty_map = {'easy': 1, 'medium': 3, 'hard': 5}
        difficulty_level = difficulty_map.get(difficulty, 3)
        
        try:
            # AI 서비스로 질문 생성 시도
            ai_service = QuestionGeneratorService()
            questions = ai_service.generate_questions(
                content=None,  # 일반적인 질문
                question_types=['multiple_choice'],
                difficulty=difficulty_level,
                count=1
            )
            
            if questions and len(questions) > 0:
                question = questions[0]
                return {
                    'question_text': question.get('question_text', f'{content_area}에 대한 질문입니다.'),
                    'question_type': 'multiple_choice',
                    'options': question.get('options', ['옵션 1', '옵션 2', '옵션 3', '옵션 4']),
                    'correct_answer': question.get('correct_answer', '옵션 1'),
                    'difficulty': difficulty,
                    'explanation': question.get('explanation', ''),
                    'estimated_time': '60'
                }
        except Exception as e:
            logger.warning(f"Failed to generate AI question, using fallback: {e}")
        
        # AI 서비스 실패 시 기본 질문 반환
        return self._get_fallback_question(difficulty, content_area)
    
    def _get_fallback_question(self, difficulty, content_area):
        """AI 서비스 실패 시 사용할 기본 질문"""
        questions_by_difficulty = {
            'easy': {
                'question_text': f'{content_area} 기초: 다음 중 가장 기본적인 개념은 무엇입니까?',
                'options': ['기초 개념 A', '기초 개념 B', '기초 개념 C', '기초 개념 D'],
                'correct_answer': '기초 개념 A',
                'estimated_time': '30'
            },
            'medium': {
                'question_text': f'{content_area} 응용: 다음 상황에서 가장 적절한 접근 방법은?',
                'options': ['방법 A', '방법 B', '방법 C', '방법 D'],
                'correct_answer': '방법 A',
                'estimated_time': '60'
            },
            'hard': {
                'question_text': f'{content_area} 고급: 복잡한 상황에서 최적의 해결책을 분석해보세요.',
                'options': ['복합 해결책 A', '복합 해결책 B', '복합 해결책 C', '복합 해결책 D'],
                'correct_answer': '복합 해결책 A',
                'estimated_time': '90'
            }
        }
        
        base_question = questions_by_difficulty.get(difficulty, questions_by_difficulty['medium'])
        return {
            'question_text': base_question['question_text'],
            'question_type': 'multiple_choice',
            'options': base_question['options'],
            'correct_answer': base_question['correct_answer'],
            'difficulty': difficulty,
            'explanation': f'이것은 {difficulty} 난이도의 {content_area} 문제입니다.',
            'estimated_time': base_question['estimated_time']
        }


class AdaptiveTestAnswerView(APIView):
    """
    Submit an answer for adaptive test
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, test_id):
        """Submit answer and get next question"""
        # 입력 데이터 검증
        user_answer = request.data.get('user_answer')
        time_spent_seconds = request.data.get('time_spent_seconds', 0)
        
        if not user_answer:
            return Response(
                {'error': 'user_answer is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 적응형 시험 조회 및 소유권 확인
            adaptive_test = get_object_or_404(
                AIAdaptiveDifficultyTest,
                id=test_id,
                user=request.user,
                completed_at__isnull=True  # 완료되지 않은 시험만
            )
            
            # 답안의 정확성 판단 (실제로는 AI 평가나 정답 비교)
            # 현재는 간단한 로직으로 처리
            is_correct = self._evaluate_answer(user_answer, adaptive_test.content_area)
            
            # 난이도 조절 로직
            old_difficulty = adaptive_test.current_difficulty
            adaptive_test = self._update_test_state(adaptive_test, is_correct)
            difficulty_changed = old_difficulty != adaptive_test.current_difficulty
            
            # 시험 완료 여부 확인
            is_completed = adaptive_test.total_questions >= adaptive_test.target_questions
            
            if is_completed:
                # 시험 완료 처리
                adaptive_test.completed_at = timezone.now()
                adaptive_test.final_difficulty_level = adaptive_test.current_difficulty
                adaptive_test.estimated_proficiency = self._calculate_proficiency(adaptive_test)
                adaptive_test.save()
                
                return Response({
                    'test': self._serialize_test(adaptive_test),
                    'is_completed': True,
                    'final_results': {
                        'accuracy_rate': adaptive_test.accuracy_rate,
                        'final_difficulty': adaptive_test.final_difficulty_level,
                        'estimated_proficiency': adaptive_test.estimated_proficiency
                    }
                })
            else:
                # 다음 질문 생성
                next_question = self._generate_question_for_difficulty(
                    adaptive_test.current_difficulty,
                    adaptive_test.content_area
                )
                
                return Response({
                    'test': self._serialize_test(adaptive_test),
                    'next_question': next_question,
                    'is_completed': False,
                    'difficulty_changed': difficulty_changed,
                    'is_correct': is_correct
                })
                
        except Exception as e:
            logger.error(f"Error in adaptive test answer submission: {e}")
            return Response(
                {'error': '답안 처리 중 오류가 발생했습니다.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _evaluate_answer(self, user_answer, content_area):
        """답안 평가 (간단한 로직, 추후 AI 평가로 대체 가능)"""
        # 현재는 간단한 규칙 기반 평가
        # 실제로는 AI 서비스를 통해 더 정교한 평가를 수행
        
        # 임시 로직: 특정 키워드가 포함되어 있으면 정답으로 간주
        positive_keywords = ['A', '방법 A', '기초 개념 A', '복합 해결책 A']
        return any(keyword in user_answer for keyword in positive_keywords)
    
    def _update_test_state(self, adaptive_test, is_correct):
        """시험 상태 업데이트 및 난이도 조절"""
        # 문제 수 및 정답 수 업데이트
        adaptive_test.total_questions += 1
        if is_correct:
            adaptive_test.correct_answers += 1
            adaptive_test.consecutive_correct += 1
            adaptive_test.consecutive_wrong = 0
        else:
            adaptive_test.consecutive_correct = 0
            adaptive_test.consecutive_wrong += 1
        
        # 난이도 조절 로직
        if adaptive_test.consecutive_correct >= 3:
            # 3개 연속 정답 → 난이도 상승
            if adaptive_test.current_difficulty == 'easy':
                adaptive_test.current_difficulty = 'medium'
            elif adaptive_test.current_difficulty == 'medium':
                adaptive_test.current_difficulty = 'hard'
            adaptive_test.consecutive_correct = 0
            
        elif adaptive_test.consecutive_wrong >= 2:
            # 2개 연속 오답 → 난이도 하락
            if adaptive_test.current_difficulty == 'hard':
                adaptive_test.current_difficulty = 'medium'
            elif adaptive_test.current_difficulty == 'medium':
                adaptive_test.current_difficulty = 'easy'
            adaptive_test.consecutive_wrong = 0
        
        adaptive_test.save()
        return adaptive_test
    
    def _calculate_proficiency(self, adaptive_test):
        """숙련도 계산"""
        accuracy_rate = adaptive_test.accuracy_rate
        difficulty_bonus = {
            'easy': 0,
            'medium': 10,
            'hard': 20
        }.get(adaptive_test.final_difficulty_level, 0)
        
        # 정확도 + 최종 난이도 보너스
        proficiency = min(100, accuracy_rate + difficulty_bonus)
        return proficiency
    
    def _serialize_test(self, adaptive_test):
        """시험 데이터 시리얼라이즈"""
        return {
            'id': adaptive_test.id,
            'content_area': adaptive_test.content_area,
            'target_questions': adaptive_test.target_questions,
            'current_difficulty': adaptive_test.current_difficulty,
            'consecutive_correct': adaptive_test.consecutive_correct,
            'consecutive_wrong': adaptive_test.consecutive_wrong,
            'total_questions': adaptive_test.total_questions,
            'correct_answers': adaptive_test.correct_answers,
            'estimated_proficiency': adaptive_test.estimated_proficiency,
            'started_at': adaptive_test.started_at.isoformat()
        }
    
    def _generate_question_for_difficulty(self, difficulty, content_area):
        """AdaptiveTestStartView와 동일한 로직"""
        difficulty_map = {'easy': 1, 'medium': 3, 'hard': 5}
        difficulty_level = difficulty_map.get(difficulty, 3)
        
        try:
            ai_service = QuestionGeneratorService()
            questions = ai_service.generate_questions(
                content=None,
                question_types=['multiple_choice'],
                difficulty=difficulty_level,
                count=1
            )
            
            if questions and len(questions) > 0:
                question = questions[0]
                return {
                    'question_text': question.get('question_text', f'{content_area}에 대한 질문입니다.'),
                    'question_type': 'multiple_choice',
                    'options': question.get('options', ['옵션 1', '옵션 2', '옵션 3', '옵션 4']),
                    'correct_answer': question.get('correct_answer', '옵션 1'),
                    'difficulty': difficulty,
                    'explanation': question.get('explanation', ''),
                    'estimated_time': '60'
                }
        except Exception as e:
            logger.warning(f"Failed to generate AI question, using fallback: {e}")
        
        # AI 서비스 실패 시 기본 질문 반환
        return self._get_fallback_question(difficulty, content_area)
    
    def _get_fallback_question(self, difficulty, content_area):
        """기본 질문 생성"""
        questions_by_difficulty = {
            'easy': {
                'question_text': f'{content_area} 기초: 다음 중 가장 기본적인 개념은 무엇입니까?',
                'options': ['기초 개념 A', '기초 개념 B', '기초 개념 C', '기초 개념 D'],
                'correct_answer': '기초 개념 A',
                'estimated_time': '30'
            },
            'medium': {
                'question_text': f'{content_area} 응용: 다음 상황에서 가장 적절한 접근 방법은?',
                'options': ['방법 A', '방법 B', '방법 C', '방법 D'],
                'correct_answer': '방법 A',
                'estimated_time': '60'
            },
            'hard': {
                'question_text': f'{content_area} 고급: 복잡한 상황에서 최적의 해결책을 분석해보세요.',
                'options': ['복합 해결책 A', '복합 해결책 B', '복합 해결책 C', '복합 해결책 D'],
                'correct_answer': '복합 해결책 A',
                'estimated_time': '90'
            }
        }
        
        base_question = questions_by_difficulty.get(difficulty, questions_by_difficulty['medium'])
        return {
            'question_text': base_question['question_text'],
            'question_type': 'multiple_choice',
            'options': base_question['options'],
            'correct_answer': base_question['correct_answer'],
            'difficulty': difficulty,
            'explanation': f'이것은 {difficulty} 난이도의 {content_area} 문제입니다.',
            'estimated_time': base_question['estimated_time']
        }
