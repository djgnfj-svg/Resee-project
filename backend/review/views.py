from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import ReviewSchedule, ReviewHistory
from .serializers import ReviewScheduleSerializer, ReviewHistorySerializer
from .utils import get_review_intervals, calculate_success_rate, get_today_reviews_count
from resee.pagination import ReviewPagination, OptimizedPageNumberPagination
import logging

logger = logging.getLogger(__name__)


class ReviewScheduleViewSet(viewsets.ModelViewSet):
    """
    복습 스케줄 관리
    
    에빙하우스 망각곡선 기반 복습 스케줄을 관리합니다.
    """
    queryset = ReviewSchedule.objects.all()
    serializer_class = ReviewScheduleSerializer
    pagination_class = ReviewPagination
    
    def get_queryset(self):
        return ReviewSchedule.objects.filter(user=self.request.user)\
            .select_related('content', 'content__category', 'user')\
            .prefetch_related('content__ai_questions')
    
    @swagger_auto_schema(
        operation_summary="복습 스케줄 목록 조회",
        operation_description="사용자의 모든 복습 스케줄을 조회합니다.",
        responses={200: ReviewScheduleSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ReviewHistoryViewSet(viewsets.ModelViewSet):
    """
    복습 기록 관리
    
    사용자의 복습 기록을 관리하고 조회할 수 있습니다.
    """
    queryset = ReviewHistory.objects.all()
    serializer_class = ReviewHistorySerializer
    pagination_class = ReviewPagination
    
    def get_queryset(self):
        return ReviewHistory.objects.filter(user=self.request.user)\
            .select_related('content', 'content__category', 'user')\
            .order_by('-reviewed_at')
    
    @swagger_auto_schema(
        operation_summary="복습 기록 목록 조회",
        operation_description="사용자의 모든 복습 기록을 조회합니다.",
        responses={200: ReviewHistorySerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TodayReviewView(APIView):
    """
    오늘의 복습
    
    오늘 복습해야 할 콘텐츠 목록을 조회합니다.
    """
    
    @swagger_auto_schema(
        operation_summary="오늘의 복습 목록 조회",
        operation_description="오늘 복습 예정인 모든 콘텐츠를 반환합니다. 카테고리별 필터링 가능합니다.",
        manual_parameters=[
            openapi.Parameter(
                'category_slug', 
                openapi.IN_QUERY, 
                description="특정 카테고리만 필터링", 
                type=openapi.TYPE_STRING
            ),
        ],
        responses={200: ReviewScheduleSerializer(many=True)}
    )
    def get(self, request):
        """Get today's review items (including initial reviews)"""
        today = timezone.now().date()
        schedules = ReviewSchedule.objects.filter(
            user=request.user,
            is_active=True
        ).filter(
            # Include items that are due today OR are initial reviews not yet completed
            Q(next_review_date__date__lte=today) | Q(initial_review_completed=False)
        ).select_related('content', 'content__category').order_by('next_review_date')
        
        # Category filter
        category_slug = request.query_params.get('category_slug', None)
        if category_slug:
            schedules = schedules.filter(content__category__slug=category_slug)
        
        serializer = ReviewScheduleSerializer(schedules, many=True)
        return Response(serializer.data)


class CompleteReviewView(APIView):
    """
    복습 완료
    
    복습 세션을 완료하고 다음 복습 일정을 업데이트합니다.
    """
    
    @swagger_auto_schema(
        operation_summary="복습 완료 처리",
        operation_description="""
        복습 결과를 기록하고 다음 복습 일정을 자동으로 계산합니다.
        
        **결과 옵션:**
        - `remembered`: 완전히 기억함 → 다음 간격으로 진행
        - `partial`: 애매하게 기억함 → 현재 간격 반복  
        - `forgot`: 기억하지 못함 → 첫 번째 간격(1일)으로 리셋
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['content_id', 'result'],
            properties={
                'content_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='콘텐츠 ID'),
                'result': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    enum=['remembered', 'partial', 'forgot'],
                    description='복습 결과'
                ),
                'time_spent': openapi.Schema(type=openapi.TYPE_INTEGER, description='소요 시간(초)', default=0),
                'notes': openapi.Schema(type=openapi.TYPE_STRING, description='복습 메모', default=''),
            }
        ),
        responses={
            200: openapi.Response(
                description="복습 완료 성공",
                examples={
                    "application/json": {
                        "message": "Review completed successfully",
                        "next_review_date": "2025-07-20T09:00:00Z",
                        "interval_index": 1
                    }
                }
            ),
            400: "필수 파라미터 누락",
            404: "복습 스케줄을 찾을 수 없음"
        }
    )
    def post(self, request):
        """Complete a review and update schedule with improved error handling"""
        content_id = request.data.get('content_id')
        result = request.data.get('result')  # 'remembered', 'partial', 'forgot'
        time_spent = request.data.get('time_spent')
        notes = request.data.get('notes', '')
        
        # Validate required fields
        if not content_id or not result:
            return Response(
                {'error': 'content_id and result are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate result value
        valid_results = ['remembered', 'partial', 'forgot']
        if result not in valid_results:
            return Response(
                {'error': f'result must be one of: {", ".join(valid_results)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Get the review schedule
                schedule = ReviewSchedule.objects.select_for_update().get(
                    content_id=content_id,
                    user=request.user,
                    is_active=True
                )
                
                # Create review history
                history = ReviewHistory.objects.create(
                    content=schedule.content,
                    user=request.user,
                    result=result,
                    time_spent=time_spent,
                    notes=notes
                )
                
                # Update schedule based on result
                if result == 'remembered':
                    # Mark initial review as completed if it's the first review
                    if not schedule.initial_review_completed:
                        schedule.initial_review_completed = True
                        schedule.save()
                    # Advance to next interval
                    schedule.advance_schedule()
                elif result == 'partial':
                    # Mark initial review as completed if it's the first review
                    if not schedule.initial_review_completed:
                        schedule.initial_review_completed = True
                        schedule.save()
                    # Stay at current interval but reset date
                    intervals = get_review_intervals()
                    current_interval = intervals[schedule.interval_index]
                    schedule.next_review_date = timezone.now() + timezone.timedelta(days=current_interval)
                    schedule.save()
                else:  # 'forgot'
                    # Mark initial review as completed if it's the first review
                    if not schedule.initial_review_completed:
                        schedule.initial_review_completed = True
                        schedule.save()
                    # Reset to first interval
                    schedule.reset_schedule()
                
                return Response({
                    'message': 'Review completed successfully',
                    'next_review_date': schedule.next_review_date,
                    'interval_index': schedule.interval_index
                })
                
        except ReviewSchedule.DoesNotExist:
            logger.warning(f"Review schedule not found for content_id={content_id}, user={request.user.id}")
            return Response(
                {'error': 'Review schedule not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error completing review: {str(e)}", exc_info=True)
            return Response(
                {'error': '복습 완료 처리 중 오류가 발생했습니다.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CategoryReviewStatsView(APIView):
    """
    카테고리별 복습 통계
    
    각 카테고리별로 복습 현황과 성과를 제공합니다.
    """
    
    @swagger_auto_schema(
        operation_summary="카테고리별 복습 통계 조회",
        operation_description="각 카테고리별 오늘의 복습 수, 전체 콘텐츠 수, 성공률 등을 제공합니다.",
        responses={200: openapi.Response(
            description="카테고리별 복습 통계",
            examples={
                "application/json": {
                    "english": {
                        "category": "영어",
                        "today_reviews": 5,
                        "total_content": 20,
                        "success_rate": 85.3,
                        "total_reviews_30_days": 45
                    },
                    "math": {
                        "category": "수학", 
                        "today_reviews": 3,
                        "total_content": 15,
                        "success_rate": 92.1,
                        "total_reviews_30_days": 38
                    }
                }
            }
        )}
    )
    def get(self, request):
        """Get review stats by category - optimized version"""
        from content.models import Category
        from django.db.models import Q
        
        # Get user-accessible categories
        categories = Category.objects.filter(
            Q(user=None) | Q(user=request.user)
        )
        result = {}
        
        for category in categories:
            # Use utility functions for consistent calculations
            today_reviews = get_today_reviews_count(request.user, category=category)
            total_content = request.user.contents.filter(category=category).count()
            success_rate, total_reviews_30_days, _ = calculate_success_rate(
                request.user, category=category, days=30
            )
            
            # Only include categories with content or reviews
            if total_content > 0 or total_reviews_30_days > 0:
                result[category.slug] = {
                    'category': category.name,
                    'today_reviews': today_reviews,
                    'total_content': total_content,
                    'success_rate': success_rate,
                    'total_reviews_30_days': total_reviews_30_days,
                }
        
        return Response(result)