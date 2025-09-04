"""
Base classes and common utilities for AI Review views
"""
import logging

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import AIUsageTracking
from content.models import Content
from resee.structured_logging import ai_logger, log_api_call, log_performance
from resee.throttling import AIEndpointThrottle
from resee.permissions import AIFeaturesRequired

from ..services import AIServiceError, QuestionGeneratorService, AIChatService

logger = logging.getLogger(__name__)


class BaseAIView(APIView):
    """
    Base view class for AI-related endpoints with common functionality
    """
    permission_classes = [permissions.IsAuthenticated, AIFeaturesRequired]
    throttle_classes = [AIEndpointThrottle]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai_service = QuestionGeneratorService()
        self.chat_service = AIChatService()
    
    def check_ai_feature_access(self, request, feature_name=None):
        """Check if user can access AI features"""
        if not request.user.can_use_ai_features():
            return Response(
                {
                    'error': 'AI features not available',
                    'detail': 'Please upgrade your subscription and verify your email to access AI features.',
                    'requires_subscription': True
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        if feature_name:
            available_features = request.user.get_ai_features_list()
            if feature_name not in available_features:
                return Response(
                    {
                        'error': f'{feature_name} not available',
                        'detail': f'{feature_name} is not available in your subscription tier.',
                        'available_features': available_features
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return None
    
    def check_daily_limit(self, request, credit_count=1):
        """Check daily usage limit"""
        usage_record = AIUsageTracking.get_or_create_for_today(request.user)
        if not usage_record.can_generate_questions(credit_count):
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
        return None
    
    def get_user_content(self, request, content_id):
        """Get content owned by the current user"""
        return get_object_or_404(Content, id=content_id, author=request.user)
    
    def handle_ai_service_error(self, e, user_email):
        """Handle AI service errors consistently"""
        logger.error(f"AI service error for user {user_email}: {str(e)}")
        return Response(
            {'error': 'AI service temporarily unavailable', 'detail': str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    def handle_unexpected_error(self, e, operation):
        """Handle unexpected errors consistently"""
        logger.error(f"Unexpected error in {operation}: {str(e)}")
        return Response(
            {'error': f'{operation} failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    def track_usage(self, request, credit_count=1):
        """Track AI usage"""
        usage_record = AIUsageTracking.get_or_create_for_today(request.user)
        usage_record.increment_questions(credit_count)
        return usage_record