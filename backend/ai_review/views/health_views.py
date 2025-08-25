"""
Health Check Views for AI Review System
"""
import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from ..models import AIQuestionType
from ..services import QuestionGeneratorService

logger = logging.getLogger(__name__)


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
        
        # Initialize AI service to test availability
        ai_service = QuestionGeneratorService()
        ai_service_available = hasattr(ai_service, 'client')
        
        return Response({
            'status': 'healthy',
            'active_question_types': question_types_count,
            'ai_service_available': ai_service_available
        })
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)