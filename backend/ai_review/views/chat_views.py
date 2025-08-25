"""
AI Chat Views
"""
import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response

from ..serializers import (
    AIChatRequestSerializer,
    AIChatResponseSerializer
)
from ..services import AIServiceError
from .base import BaseAIView

logger = logging.getLogger(__name__)


class AIChatView(BaseAIView):
    """
    AI chat for learning content
    """
    
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
        access_response = self.check_ai_feature_access(request, 'ai_chat')
        if access_response:
            return access_response
        
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
        limit_response = self.check_daily_limit(request, 1)  # 1 chat = 1 question credit
        if limit_response:
            return limit_response
        
        # Get content
        content = self.get_user_content(request, content_id)
        
        try:
            # Get AI response
            result = self.ai_service.chat_about_content(
                content_text=content.content,
                content_title=content.title,
                user_message=message
            )
            
            # Track usage
            self.track_usage(request, 1)
            
            logger.info(
                f"AI chat interaction for content {content.id} "
                f"(user: {request.user.email}, tier: {request.user.subscription.tier})"
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except AIServiceError as e:
            return self.handle_ai_service_error(e, request.user.email)
        except Exception as e:
            return self.handle_unexpected_error(e, 'AI chat')