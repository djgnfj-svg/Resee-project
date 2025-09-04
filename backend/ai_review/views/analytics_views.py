"""
AI Analytics Views
"""
from django.conf import settings
from django.db.models import Avg
from datetime import timedelta
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..mock_responses import AIMockResponses


class AIAnalyticsView(APIView):
    """AI Analytics view for learning insights"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Generate AI-powered learning analytics"""
        period_type = request.data.get('period_type', 'weekly')
        
        # Use mock responses if enabled
        if getattr(settings, 'AI_USE_MOCK_RESPONSES', True):
            mock_response = AIMockResponses.get_analytics_response(period_type=period_type)
            return Response(mock_response)
        
        try:
            # Get basic analytics data from review history
            from review.models import ReviewHistory
            from content.models import Content
            
            # Calculate period dates
            now = timezone.now()
            if period_type == 'daily':
                start_date = now - timedelta(days=1)
            elif period_type == 'weekly':
                start_date = now - timedelta(weeks=1)
            elif period_type == 'monthly':
                start_date = now - timedelta(days=30)
            else:  # quarterly
                start_date = now - timedelta(days=90)
            
            # Get review data for the period
            reviews = ReviewHistory.objects.filter(
                user=request.user,
                review_date__gte=start_date
            )
            
            # Calculate basic metrics
            total_reviews = reviews.count()
            if total_reviews > 0:
                success_rate = reviews.filter(result='remembered').count() / total_reviews * 100
                average_time = reviews.aggregate(avg_time=Avg('time_spent'))['avg_time'] or 0
            else:
                success_rate = 0
                average_time = 0
            
            # Get content statistics
            total_contents = Content.objects.filter(author=request.user).count()
            
            # Mock insights
            insights = []
            if success_rate > 80:
                insights.append({
                    'type': 'positive',
                    'message': f'훌륭해요! {period_type} 성공률이 {success_rate:.1f}%입니다.',
                    'recommendation': '현재 학습 패턴을 유지하세요.'
                })
            elif success_rate > 60:
                insights.append({
                    'type': 'neutral',
                    'message': f'{period_type} 성공률이 {success_rate:.1f}%입니다.',
                    'recommendation': '조금 더 자주 복습하면 성과가 개선될 것입니다.'
                })
            else:
                insights.append({
                    'type': 'warning',
                    'message': f'{period_type} 성공률이 {success_rate:.1f}%로 낮습니다.',
                    'recommendation': '학습 간격을 줄이고 집중도를 높여보세요.'
                })
            
            # Add time-based insights
            if average_time > 300:  # 5 minutes
                insights.append({
                    'type': 'positive',
                    'message': '충분한 시간을 들여 학습하고 있습니다.',
                    'recommendation': '깊이 있는 학습이 이루어지고 있어요!'
                })
            
            # Add content-based insights
            if total_contents > 10:
                insights.append({
                    'type': 'info',
                    'message': f'총 {total_contents}개의 학습 콘텐츠를 관리하고 있습니다.',
                    'recommendation': '정기적으로 모든 콘텐츠를 복습하세요.'
                })
            
            return Response({
                'success': True,
                'insights': insights,
                'recommendations': [
                    '매일 10분씩 꾸준히 복습하기',
                    '어려운 내용은 여러 번 반복 학습하기',
                    '학습 직후 바로 복습하여 기억 강화하기'
                ],
                'period_type': period_type,
                'metrics': {
                    'success_rate': success_rate,
                    'average_time_seconds': average_time,
                    'total_reviews': total_reviews,
                    'total_contents': total_contents
                }
            })
            
        except Exception as e:
            return Response({
                'error': f'분석 생성 중 오류: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)