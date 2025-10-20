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
    prefetch_related_fields = []
    
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
        return super().get_queryset().order_by('-review_date')
    
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
        ).select_related(
            'content',
            'content__category',
            'user'
        ).order_by('next_review_date')
        
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
        descriptive_answer = request.data.get('descriptive_answer', '')  # v0.4: AI 평가용 서술형 답변

        # === Input Validation ===
        # 1. content_id validation
        if not content_id:
            return Response(
                {'error': 'content_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            content_id = int(content_id)
        except (ValueError, TypeError):
            return Response(
                {'error': 'content_id must be a valid integer'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. time_spent validation
        if time_spent is not None:
            try:
                time_spent = int(time_spent)
                if time_spent < 0:
                    return Response(
                        {'error': 'time_spent cannot be negative'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if time_spent > 86400:  # 24 hours in seconds
                    return Response(
                        {'error': 'time_spent cannot exceed 24 hours (86400 seconds)'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                return Response(
                    {'error': 'time_spent must be a valid integer (seconds)'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 3. notes length validation (DoS prevention)
        if notes and len(notes) > 5000:
            return Response(
                {'error': 'notes cannot exceed 5000 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. descriptive_answer length validation (DoS prevention)
        if descriptive_answer and len(descriptive_answer) > 10000:
            return Response(
                {'error': 'descriptive_answer cannot exceed 10000 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                # Get the review schedule (also verifies content ownership)
                try:
                    schedule = ReviewSchedule.objects.select_for_update().get(
                        content_id=content_id,
                        user=request.user,
                        is_active=True
                    )
                except ReviewSchedule.DoesNotExist:
                    logger.warning(
                        f"Review schedule not found or access denied: "
                        f"user={request.user.email}, content_id={content_id}"
                    )
                    return Response(
                        {'error': 'Review schedule not found or you do not have permission to access it'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # v0.5: 주관식 모드 - AI 자동 평가 및 result 판단
                ai_score = None
                ai_feedback = None
                ai_auto_result = None

                if schedule.content.review_mode == 'subjective':
                    # 주관식: 반드시 답변을 작성해야 함
                    if not descriptive_answer or len(descriptive_answer.strip()) < 10:
                        return Response(
                            {'error': '주관식 모드에서는 최소 10자 이상의 답변을 작성해야 합니다.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # AI 평가 수행
                    from .ai_evaluation import ai_answer_evaluator
                    if not ai_answer_evaluator.is_available():
                        return Response(
                            {'error': 'AI 평가 서비스를 사용할 수 없습니다.'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE
                        )

                    evaluation = ai_answer_evaluator.evaluate_answer(
                        content_title=schedule.content.title,
                        content_body=schedule.content.content,
                        user_answer=descriptive_answer
                    )

                    if not evaluation:
                        return Response(
                            {'error': 'AI 평가에 실패했습니다. 다시 시도해주세요.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )

                    ai_score = evaluation['score']
                    ai_feedback = evaluation['feedback']
                    ai_auto_result = evaluation.get('auto_result', 'remembered' if ai_score >= 70 else 'forgot')
                    result = ai_auto_result  # AI 자동 판단으로 result 덮어쓰기
                    logger.info(f"AI 자동 평가 완료: {schedule.content.title} - {ai_score}점 -> {result}")

                else:
                    # 객관식: 기존 방식 (선택적 AI 평가)
                    if not result:
                        return Response(
                            {'error': 'result is required for objective mode'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # Validate result value
                    valid_results = ['remembered', 'partial', 'forgot']
                    if result not in valid_results:
                        return Response(
                            {'error': f'result must be one of: {", ".join(valid_results)}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # 선택적 AI 평가 (답변이 있는 경우)
                    if descriptive_answer and len(descriptive_answer.strip()) >= 10:
                        from .ai_evaluation import ai_answer_evaluator
                        if ai_answer_evaluator.is_available():
                            evaluation = ai_answer_evaluator.evaluate_answer(
                                content_title=schedule.content.title,
                                content_body=schedule.content.content,
                                user_answer=descriptive_answer
                            )
                            if evaluation:
                                ai_score = evaluation['score']
                                ai_feedback = evaluation['feedback']
                                logger.info(f"AI 평가 완료: {schedule.content.title} - {ai_score}점")

                # Create review history with AI evaluation
                history = ReviewHistory.objects.create(
                    content=schedule.content,
                    user=request.user,
                    result=result,
                    time_spent=time_spent,
                    notes=notes,
                    descriptive_answer=descriptive_answer,
                    ai_score=ai_score,
                    ai_feedback=ai_feedback
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
                    # For 'forgot': Reset interval index to 0 (restart from beginning)
                    # but keep next_review_date unchanged so it remains in today's review list
                    schedule.interval_index = 0
                    # Don't change next_review_date - keep it available for immediate retry in same session
                    schedule.save()
                
                response_data = {
                    'message': 'Review completed successfully',
                    'next_review_date': schedule.next_review_date,
                    'interval_index': schedule.interval_index,
                    'final_result': result  # AI가 자동 판단한 최종 result
                }

                # v0.5: AI 평가 결과 포함 (auto_result 추가)
                if ai_score is not None:
                    response_data['ai_evaluation'] = {
                        'score': ai_score,
                        'feedback': ai_feedback,
                        'auto_result': ai_auto_result if ai_auto_result else result
                    }

                return Response(response_data)

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
        
        # Import additional Django aggregation functions
        from django.db.models import Count, Avg, Case, When, IntegerField
        from django.utils import timezone
        from datetime import timedelta

        # Get user-accessible categories with content count in one query
        categories = categories.annotate(
            total_content=Count(
                'content',
                filter=Q(content__author=request.user)
            )
        )

        # Get today's reviews aggregated by category
        today = timezone.now().date()
        today_reviews_by_category = ReviewSchedule.objects.filter(
            user=request.user,
            is_active=True,
            next_review_date__date=today
        ).values('content__category').annotate(
            today_count=Count('id')
        )
        today_reviews_dict = {
            item['content__category']: item['today_count']
            for item in today_reviews_by_category
        }

        # Get 30-day review history aggregated by category
        thirty_days_ago = timezone.now() - timedelta(days=30)
        reviews_30_days = ReviewHistory.objects.filter(
            user=request.user,
            review_date__gte=thirty_days_ago
        ).values('content__category').annotate(
            total_reviews=Count('id'),
            success_rate=Avg(
                Case(
                    When(result='remembered', then=100),
                    When(result='partial', then=50),
                    When(result='forgot', then=0),
                    output_field=IntegerField()
                )
            )
        )

        reviews_30_days_dict = {}
        for item in reviews_30_days:
            category_id = item['content__category']
            reviews_30_days_dict[category_id] = {
                'total_reviews': item['total_reviews'],
                'success_rate': round(item['success_rate'] or 0, 1)
            }

        # Build optimized result
        for category in categories:
            # Get aggregated data
            today_reviews = today_reviews_dict.get(category.id, 0)
            total_content = category.total_content
            reviews_data = reviews_30_days_dict.get(category.id, {})
            total_reviews_30_days = reviews_data.get('total_reviews', 0)
            success_rate = reviews_data.get('success_rate', 0.0)

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