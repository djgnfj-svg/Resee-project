"""
AI Review Views - Legacy compatibility module

This module maintains backward compatibility while the views are being reorganized.
All new view implementations are in the views/ package.
"""

# Import all views from the new modular structure for backward compatibility
from .views import *

# The following imports ensure that existing URLs continue to work
from .views.question_views import (
    AIQuestionTypeListView,
    GenerateQuestionsView,
    ContentQuestionsView,
    GenerateFillBlanksView,
    IdentifyBlurRegionsView
)

from .views.evaluation_views import (
    AIAnswerEvaluationView,
    ExplanationEvaluationView
)

from .views.chat_views import AIChatView

from .views.health_views import ai_review_health

from .views.test_views import (
    WeeklyTestView,
    WeeklyTestStartView,
    WeeklyTestAnswerView,
    InstantContentCheckView,
    ContentQualityCheckView,
    AdaptiveTestStartView,
    AdaptiveTestAnswerView
)

# Import remaining views from backup file temporarily
import logging
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

# Views that need to be refactored and moved to appropriate modules

# Import statements for temporary views
from accounts.models import AIUsageTracking
from content.models import Content
from resee.structured_logging import ai_logger, log_api_call, log_performance
from resee.throttling import AIEndpointThrottle
from resee.permissions import AIFeaturesRequired

from .models import (
    AIAdaptiveDifficultyTest, AIQuestion, AIQuestionType, AIReviewSession, AIStudyMate,
    AISummaryNote, InstantContentCheck, LearningAnalytics,
    WeeklyTest, WeeklyTestQuestion
)
from .serializers import (
    AIReviewSessionSerializer, AIStudyMateSerializer, AISummaryNoteSerializer,
    AdaptiveTestStartSerializer, AdaptiveTestAnswerSerializer,
    AnalyticsRequestSerializer, InstantCheckRequestSerializer,
    InstantContentCheckSerializer, LearningAnalyticsSerializer,
    StudyMateRequestSerializer, SummaryNoteRequestSerializer,
    WeeklyTestAnswerSerializer, WeeklyTestCreateSerializer,
    WeeklyTestQuestionSerializer, WeeklyTestSerializer,
    WeeklyTestStartSerializer
)
from .services import AIServiceError, QuestionGeneratorService

logger = logging.getLogger(__name__)

# Initialize AI service
ai_service = QuestionGeneratorService()


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


# Note: These views have been moved to separate view modules
class WeeklyTestView(APIView):
    """주간 시험 관리 뷰"""
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIEndpointThrottle]
    
    def get(self, request):
        """사용자의 주간 시험 목록 조회"""
        from django.conf import settings
        from .mock_responses import AIMockResponses
        
        # Use mock responses if enabled
        if getattr(settings, 'AI_USE_MOCK_RESPONSES', True):
            mock_response = AIMockResponses.get_weekly_test_list_response()
            return Response(mock_response)
            
        tests = WeeklyTest.objects.filter(user=request.user)[:10]
        serializer = WeeklyTestSerializer(tests, many=True)
        return Response(serializer.data)
    
    @log_api_call
    @log_performance('weekly_test_creation')
    def post(self, request):
        """새로운 주간 시험 생성"""
        from django.conf import settings
        from .mock_responses import AIMockResponses
        
        # Use mock responses if enabled
        if getattr(settings, 'AI_USE_MOCK_RESPONSES', True):
            mock_response = AIMockResponses.get_weekly_test_response(test_type="create")
            return Response(mock_response, status=status.HTTP_201_CREATED)
        
        if not request.user.can_use_ai_features():
            return Response(
                {'error': 'AI features not available'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = WeeklyTestCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from datetime import datetime, timedelta
            from django.utils import timezone
            from review.models import ReviewHistory
            
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            
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
    
    def post(self, request):
        """주간 시험 시작"""
        from django.conf import settings
        from .mock_responses import AIMockResponses
        
        # Use mock responses if enabled
        if getattr(settings, 'AI_USE_MOCK_RESPONSES', True):
            mock_response = AIMockResponses.get_weekly_test_response(test_type="start")
            return Response(mock_response)
        
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
            
            weekly_test.status = 'in_progress'
            weekly_test.started_at = timezone.now()
            weekly_test.save()
            
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


# Placeholder classes for the remaining complex views
# These should be moved to appropriate modules later

class AdaptiveTestStartView(APIView):
    """Start adaptive test - simplified version"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        from django.conf import settings
        from .mock_responses import AIMockResponses
        
        # Use mock responses if enabled
        if getattr(settings, 'AI_USE_MOCK_RESPONSES', True):
            difficulty = request.data.get('difficulty', 'medium')
            mock_response = AIMockResponses.get_adaptive_test_response(test_type="start", difficulty=difficulty)
            return Response(mock_response)
        
        return Response({
            'message': '적응형 테스트 기능은 현재 개발 중입니다.',
            'status': 'under_development'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


class AdaptiveTestAnswerView(APIView):
    """Submit adaptive test answer - simplified version"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, test_id):
        from django.conf import settings
        from .mock_responses import AIMockResponses
        
        # Use mock responses if enabled
        if getattr(settings, 'AI_USE_MOCK_RESPONSES', True):
            mock_response = AIMockResponses.get_adaptive_test_response(test_type="answer")
            return Response(mock_response)
        
        return Response({
            'message': '적응형 테스트 답변 제출 기능은 현재 개발 중입니다.',
            'status': 'under_development'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


class InstantContentCheckView(APIView):
    """Instant content check - simplified version"""
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIEndpointThrottle]
    
    def post(self, request):
        return Response({
            'message': '실시간 내용 검토 기능은 현재 개발 중입니다.',
            'status': 'under_development'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


class LearningAnalyticsView(APIView):
    """Learning analytics - simplified version"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        return Response({
            'message': '학습 분석 기능은 현재 개발 중입니다.',
            'status': 'under_development'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


class AIStudyMateView(APIView):
    """AI study mate - simplified version"""
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIEndpointThrottle]
    
    def post(self, request):
        return Response({
            'message': 'AI 스터디 메이트 기능은 현재 개발 중입니다.',
            'status': 'under_development'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


class AISummaryNoteView(APIView):
    """AI summary note - simplified version"""
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIEndpointThrottle]
    
    def post(self, request):
        return Response({
            'message': 'AI 요약 노트 기능은 현재 개발 중입니다.',
            'status': 'under_development'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


