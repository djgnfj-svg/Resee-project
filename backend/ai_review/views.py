"""
AI Review API views
"""
import logging
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from content.models import Content
from accounts.models import AIUsageTracking
from .models import AIQuestionType, AIQuestion, AIReviewSession
from .serializers import (
    AIQuestionTypeSerializer,
    AIQuestionSerializer, 
    GenerateQuestionsSerializer,
    GeneratedQuestionSerializer,
    AIReviewSessionSerializer,
    FillBlankRequestSerializer,
    FillBlankResponseSerializer,
    BlurRegionsRequestSerializer,
    BlurRegionsResponseSerializer,
    AIChatRequestSerializer,
    AIChatResponseSerializer
)
from .services import ai_service, AIServiceError


logger = logging.getLogger(__name__)


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
    permission_classes = [permissions.IsAuthenticated]
    
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
    def post(self, request):
        """Generate questions for content"""
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
    
    def get_queryset(self):
        content_id = self.kwargs['content_id']
        # Ensure user owns the content
        content = get_object_or_404(Content, id=content_id, author=self.request.user)
        
        return AIQuestion.objects.filter(
            content=content,
            is_active=True
        ).order_by('-created_at')




class AIReviewSessionListView(ListAPIView):
    """
    List user's AI review sessions
    """
    serializer_class = AIReviewSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return AIReviewSession.objects.filter(
            review_history__user=self.request.user
        ).select_related(
            'review_history', 'review_history__content'
        ).order_by('-created_at')


class GenerateFillBlanksView(APIView):
    """
    Generate fill-in-the-blank questions for content
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        request_body=FillBlankRequestSerializer,
        responses={
            200: FillBlankResponseSerializer,
            400: 'Bad Request',
            404: 'Content not found',
            500: 'AI service error'
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
    
    @swagger_auto_schema(
        request_body=BlurRegionsRequestSerializer,
        responses={
            200: BlurRegionsResponseSerializer,
            400: 'Bad Request',
            404: 'Content not found',
            500: 'AI service error'
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


class AIChatView(APIView):
    """
    AI chat for learning content
    """
    permission_classes = [permissions.IsAuthenticated]
    
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
