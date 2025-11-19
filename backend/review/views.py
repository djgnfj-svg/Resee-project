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

from accounts.subscription.services import SubscriptionService
from resee.mixins import UserOwnershipMixin
from resee.pagination import ReviewPagination

from .models import ReviewHistory, ReviewSchedule
from .serializers import ReviewHistorySerializer, ReviewScheduleSerializer
from .utils import (
    calculate_success_rate, get_pending_reviews_count, get_review_intervals,
    get_today_reviews_count,
)

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

    @swagger_auto_schema(
        operation_summary="오늘의 복습 목록 조회 (RESTful)",
        operation_description="사용자의 구독 티어에 따라 복습할 콘텐츠를 반환합니다.",
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
    @action(detail=False, methods=['get'], url_path='today')
    def today(self, request):
        """Get review items due today or overdue (RESTful endpoint)"""
        # Delegate to existing TodayReviewView
        from .views import TodayReviewView
        view = TodayReviewView()
        view.request = request
        view.format_kwarg = None
        return view.get(request)

    @swagger_auto_schema(
        operation_summary="복습 완료 처리 (RESTful)",
        operation_description="복습 결과를 기록하고 다음 복습 일정을 계산합니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'result': openapi.Schema(type=openapi.TYPE_STRING, enum=['remembered', 'partial', 'forgot']),
                'time_spent': openapi.Schema(type=openapi.TYPE_INTEGER),
                'notes': openapi.Schema(type=openapi.TYPE_STRING),
                'descriptive_answer': openapi.Schema(type=openapi.TYPE_STRING),
                'selected_choice': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={200: "복습 완료 성공"}
    )
    @action(detail=True, methods=['post'], url_path='completions')
    def completions(self, request, pk=None):
        """Complete a review (RESTful endpoint)"""
        # Get the schedule (ownership checked by UserOwnershipMixin)
        schedule = self.get_object()

        # Create new data dict with content_id added
        data = dict(request.data)
        data['content_id'] = schedule.content.id

        # Replace request._full_data to inject content_id
        request._full_data = data

        # Delegate to existing CompleteReviewView
        from .views import CompleteReviewView
        view = CompleteReviewView()
        view.request = request
        view.format_kwarg = None

        return view.post(request)


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

        **캐싱**: Redis 캐싱 적용 (TTL: 1시간)
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
        # Use timezone-aware date calculation (respects TIME_ZONE setting)
        now = timezone.now()
        today = now.date()

        # Get user's subscription tier and determine overdue limit
        max_overdue_days = SubscriptionService(request.user).get_max_review_interval()
        if not max_overdue_days:
            max_overdue_days = 7  # Default to FREE tier

        # Calculate cutoff date for overdue reviews based on subscription
        # Don't show reviews older than the subscription allows
        cutoff_date = now - timedelta(days=max_overdue_days)

        schedules = ReviewSchedule.objects.filter(
            user=request.user,
            is_active=True
        ).filter(
            # Initial reviews always shown (regardless of date/cutoff)
            Q(initial_review_completed=False) |
            # Completed reviews shown if due today/overdue (within subscription range)
            Q(
                initial_review_completed=True,
                next_review_date__date__lte=today,
                next_review_date__gte=cutoff_date
            )
        )

        schedules = schedules.select_related(
            'content',
            'content__category',
            'content__author',
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

        response_data = {
            'results': serializer.data,
            'count': len(serializer.data),  # 남은 복습 개수
            'total_count': total_schedules,  # 전체 활성 스케줄
            'subscription_tier': request.user.subscription.tier,
            'max_interval_days': SubscriptionService(request.user).get_max_review_interval()
        }

        return Response(response_data)


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
        from django.utils import timezone

        content_id = request.data.get('content_id')
        result = request.data.get('result')  # 'remembered', 'partial', 'forgot'
        time_spent = request.data.get('time_spent')
        notes = request.data.get('notes', '')
        descriptive_answer = request.data.get('descriptive_answer', '')  # descriptive mode
        selected_choice = request.data.get('selected_choice', '')  # multiple_choice mode

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

                # === Mode-specific processing ===
                ai_score = None
                ai_feedback = None
                ai_auto_result = None

                review_mode = schedule.content.review_mode

                # 1. Multiple Choice Mode: User selects from 4 choices
                if review_mode == 'multiple_choice':
                    if not selected_choice:
                        return Response(
                            {'error': '객관식 모드에서는 답변을 선택해야 합니다.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # Verify answer
                    mc_choices = schedule.content.mc_choices
                    if not mc_choices or 'correct_answer' not in mc_choices:
                        return Response(
                            {'error': '객관식 보기가 생성되지 않았습니다.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )

                    is_correct = selected_choice == mc_choices['correct_answer']
                    result = 'remembered' if is_correct else 'forgot'

                    # Set AI evaluation data for consistent response format
                    ai_score = 100.0 if is_correct else 0.0
                    ai_feedback = '정답입니다!' if is_correct else f'오답입니다. 정답은 "{mc_choices["correct_answer"]}"입니다.'
                    ai_auto_result = result

                    logger.info(f"객관식 답변: {selected_choice} (정답: {mc_choices['correct_answer']}) -> {result}")

                # 2. Objective Mode: User self-assesses (remembered/partial/forgot)
                else:  # objective mode
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

                    logger.info(f"기억 확인 모드: 사용자 선택 -> {result}")

                # === 즉시 DB 저장 (ReviewHistory) ===
                ReviewHistory.objects.create(
                    content_id=content_id,
                    user=request.user,
                    result=result,
                    time_spent=time_spent or 0,
                    notes=notes,
                    descriptive_answer=descriptive_answer,
                    selected_choice=selected_choice,
                    ai_score=float(ai_score) if ai_score is not None else None,
                    ai_feedback=ai_feedback,
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
                    user_max_interval = SubscriptionService(request.user).get_max_review_interval()

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
                        'auto_result': ai_auto_result if ai_auto_result else result,
                        'is_correct': ai_score == 100.0  # 객관식용 정답 여부
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
        from datetime import timedelta

        from django.db.models import Avg, Case, Count, IntegerField, When
        from django.utils import timezone

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


class DashboardStatsView(APIView):
    """
    대시보드 통계

    대시보드에 표시할 기본 학습 통계를 제공합니다.
    """

    @swagger_auto_schema(
        operation_summary="대시보드 통계 조회",
        operation_description="""
        대시보드에 표시할 기본 통계를 제공합니다.

        **포함 정보:**
        - today_reviews: 오늘 완료한 복습 수
        - pending_reviews: 대기 중인 복습 수
        - total_content: 총 콘텐츠 수
        - success_rate: 30일 성공률 (%)
        - total_reviews_30_days: 최근 30일간 총 복습 수
        """,
        responses={200: openapi.Response(
            description="대시보드 통계",
            examples={
                "application/json": {
                    "today_reviews": 5,
                    "pending_reviews": 12,
                    "total_content": 45,
                    "success_rate": 87.5,
                    "total_reviews_30_days": 120
                }
            }
        )}
    )
    def get(self, request):
        """Get basic dashboard statistics"""
        from content.models import Content

        user = request.user

        # Basic counts
        today_reviews = get_today_reviews_count(user)
        pending_reviews = get_pending_reviews_count(user)
        total_content = Content.objects.filter(author=user).count()

        # 30-day success rate
        success_rate, total_reviews_30_days, _ = calculate_success_rate(user, days=30)

        return Response({
            'today_reviews': today_reviews,
            'pending_reviews': pending_reviews,
            'total_content': total_content,
            'success_rate': success_rate,
            'total_reviews_30_days': total_reviews_30_days,
        })
