import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from resee.mixins import UserOwnershipMixin
from resee.pagination import OptimizedPageNumberPagination, ReviewPagination

from .models import ReviewHistory, ReviewSchedule
from .serializers import ReviewHistorySerializer, ReviewScheduleSerializer
from .utils import (calculate_success_rate, get_review_intervals,
                    get_today_reviews_count)

logger = logging.getLogger(__name__)


class ReviewScheduleViewSet(UserOwnershipMixin, viewsets.ModelViewSet):
    """
    복습 스케줄 관리
    
    에빙하우스 망각곡선 기반 복습 스케줄을 관리합니다.
    """
    queryset = ReviewSchedule.objects.all()
    serializer_class = ReviewScheduleSerializer
    pagination_class = ReviewPagination
    
    # Query optimization configuration
    select_related_fields = ['content', 'content__category', 'user']
    prefetch_related_fields = ['content__ai_questions']
    
    @swagger_auto_schema(
        operation_summary="복습 스케줄 목록 조회",
        operation_description="사용자의 모든 복습 스케줄을 조회합니다.",
        responses={200: ReviewScheduleSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ReviewHistoryViewSet(UserOwnershipMixin, viewsets.ModelViewSet):
    """
    복습 기록 관리
    
    사용자의 복습 기록을 관리하고 조회할 수 있습니다.
    """
    queryset = ReviewHistory.objects.all()
    serializer_class = ReviewHistorySerializer
    pagination_class = ReviewPagination
    
    # Query optimization configuration
    select_related_fields = ['content', 'content__category', 'user']
    
    def get_queryset(self):
        return super().get_queryset().order_by('-reviewed_at')
    
    @swagger_auto_schema(
        operation_summary="복습 기록 목록 조회",
        operation_description="사용자의 모든 복습 기록을 조회합니다.",
        responses={200: ReviewHistorySerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    


class TodayReviewView(APIView):
    """
    오늘의 복습
    
    오늘 복습해야 할 콘텐츠 목록을 조회합니다.
    """
    
    @swagger_auto_schema(
        operation_summary="구독 티어별 복습 목록 조회",
        operation_description="""
        사용자의 구독 티어에 따라 복습할 콘텐츠를 반환합니다.
        
        **구독 티어별 복습 범위:**
        - FREE: 최대 7일 전까지의 밀린 복습
        - BASIC: 최대 30일 전까지의 밀린 복습  
        - PREMIUM: 최대 60일 전까지의 밀린 복습
        - PRO: 최대 180일 전까지의 밀린 복습
        
        초기 복습이 완료되지 않은 콘텐츠는 항상 포함됩니다.
        """,
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
        """Get review items due today or overdue (within subscription limits)"""
        today = timezone.now().date()
        
        # Get user's subscription tier and determine overdue limit
        max_overdue_days = request.user.get_max_review_interval()
        if not max_overdue_days:
            max_overdue_days = 7  # Default to FREE tier
        
        # Calculate cutoff date for overdue reviews based on subscription
        # Don't show reviews older than the subscription allows
        cutoff_date = timezone.now() - timedelta(days=max_overdue_days)
        
        schedules = ReviewSchedule.objects.filter(
            user=request.user,
            is_active=True
        ).filter(
            # Only include reviews that are due TODAY or overdue (but within subscription range)
            # OR initial reviews not yet completed
            Q(next_review_date__date__lte=today, next_review_date__gte=cutoff_date) | 
            Q(initial_review_completed=False)
        ).select_related('content', 'content__category').order_by('next_review_date')
        
        # Category filter
        category_slug = request.query_params.get('category_slug', None)
        if category_slug:
            schedules = schedules.filter(content__category__slug=category_slug)
        
        # Get total active schedules for progress display
        total_schedules = ReviewSchedule.objects.filter(
            user=request.user,
            is_active=True
        ).count()
        
        # Apply category filter to total count if specified
        if category_slug:
            total_schedules = ReviewSchedule.objects.filter(
                user=request.user,
                is_active=True,
                content__category__slug=category_slug
            ).count()
        
        serializer = ReviewScheduleSerializer(schedules, many=True)
        
        return Response({
            'results': serializer.data,
            'count': len(serializer.data),  # Today's reviews count
            'total_count': total_schedules,  # Total active schedules
            'subscription_tier': request.user.subscription.tier,
            'max_interval_days': request.user.get_max_review_interval()
        })


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
                
                # Update schedule based on result with subscription limits
                if result == 'remembered':
                    # Mark initial review as completed if it's the first review
                    if not schedule.initial_review_completed:
                        schedule.initial_review_completed = True
                        schedule.save()
                    # Advance to next interval (advance_schedule now includes subscription limits)
                    schedule.advance_schedule()
                elif result == 'partial':
                    # Mark initial review as completed if it's the first review
                    if not schedule.initial_review_completed:
                        schedule.initial_review_completed = True
                        schedule.save()
                    # Stay at current interval but reset date with subscription validation
                    intervals = get_review_intervals(request.user)
                    user_max_interval = request.user.get_max_review_interval()
                    
                    # Ensure current interval doesn't exceed subscription limits
                    if schedule.interval_index >= len(intervals):
                        schedule.interval_index = len(intervals) - 1
                    
                    current_interval = intervals[schedule.interval_index]
                    
                    # Additional check: ensure interval respects subscription tier
                    if current_interval > user_max_interval:
                        # Find the highest allowed interval
                        allowed_intervals = [i for i in intervals if i <= user_max_interval]
                        if allowed_intervals:
                            current_interval = max(allowed_intervals)
                            try:
                                schedule.interval_index = intervals.index(current_interval)
                            except ValueError:
                                schedule.interval_index = len(allowed_intervals) - 1
                                current_interval = allowed_intervals[-1]
                        else:
                            current_interval = intervals[0]
                            schedule.interval_index = 0
                    
                    schedule.next_review_date = timezone.now() + timezone.timedelta(days=current_interval)
                    schedule.save()
                else:  # 'forgot'
                    # Mark initial review as completed if it's the first review
                    if not schedule.initial_review_completed:
                        schedule.initial_review_completed = True
                        schedule.save()
                    # Reset to first interval (reset_schedule uses get_review_intervals which respects subscription)
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
        from django.db.models import Q

        from content.models import Category

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