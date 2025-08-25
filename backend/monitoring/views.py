"""
API views for monitoring dashboard
"""
import logging
from datetime import timedelta

from django.db import models
from django.db.models import Avg, Count, Max, Min, Q, Sum
from django.db.models.functions import TruncDate, TruncHour
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import (AIMetrics, APIMetrics, DatabaseMetrics, ErrorLog,
                     SystemHealth, UserActivity)
from .utils import (check_system_health, clean_old_metrics,
                    get_performance_insights)
from .permissions import MonitoringPermission

logger = logging.getLogger('monitoring')


@swagger_auto_schema(
    method='get',
    operation_summary="모니터링 대시보드 개요",
    operation_description="""
    지난 24시간 동안의 시스템 상태 개요를 제공합니다.
    
    **관리자 권한 필요**
    
    **응답 데이터:**
    - `api_metrics`: API 요청 메트릭 (총 요청, 평균 응답시간, 에러율 등)
    - `user_activity`: 사용자 활동 요약 (활성 사용자, API 요청, 생성된 콘텐츠 등)
    - `ai_usage`: AI 서비스 사용량 (총 작업, 토큰 사용량, 비용, 성공률)
    - `errors`: 에러 요약 (총 에러, 중요 에러, 미해결 에러)
    - `system_health`: 최신 시스템 상태 (CPU, 메모리, API 상태 등)
    """,
    tags=['Monitoring'],
    responses={
        200: openapi.Response(
            description="모니터링 대시보드 개요",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'timeframe': openapi.Schema(type=openapi.TYPE_STRING, description="분석 기간"),
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, description="조회 시각"),
                    'api_metrics': openapi.Schema(type=openapi.TYPE_OBJECT, description="API 메트릭"),
                    'user_activity': openapi.Schema(type=openapi.TYPE_OBJECT, description="사용자 활동"),
                    'ai_usage': openapi.Schema(type=openapi.TYPE_OBJECT, description="AI 사용량"),
                    'errors': openapi.Schema(type=openapi.TYPE_OBJECT, description="에러 요약"),
                    'system_health': openapi.Schema(type=openapi.TYPE_OBJECT, description="시스템 상태"),
                },
            )
        ),
        401: "인증 필요",
        403: "관리자 권한 필요",
        500: "서버 오류",
    }
)
@api_view(['GET'])
@permission_classes([MonitoringPermission])
def dashboard_overview(request):
    """
    Get high-level dashboard overview for the last 24 hours
    """
    try:
        since = timezone.now() - timedelta(hours=24)
        
        # API metrics summary
        api_metrics = APIMetrics.objects.filter(timestamp__gte=since)
        api_summary = {
            'total_requests': api_metrics.count(),
            'avg_response_time_ms': api_metrics.aggregate(avg=Avg('response_time_ms'))['avg'] or 0,
            'error_rate_percent': (
                api_metrics.filter(status_code__gte=400).count() / 
                max(api_metrics.count(), 1) * 100
            ),
            'slow_requests': api_metrics.filter(response_time_ms__gt=1000).count(),
        }
        
        # User activity summary
        today = timezone.now().date()
        user_activity = UserActivity.objects.filter(date=today)
        user_summary = {
            'active_users_today': user_activity.count(),
            'total_api_requests': user_activity.aggregate(total=Sum('api_requests_count'))['total'] or 0,
            'total_content_created': user_activity.aggregate(total=Sum('content_created_count'))['total'] or 0,
            'total_reviews_completed': user_activity.aggregate(total=Sum('reviews_completed_count'))['total'] or 0,
        }
        
        # AI usage summary
        ai_metrics = AIMetrics.objects.filter(timestamp__gte=since)
        ai_summary = {
            'total_operations': ai_metrics.count(),
            'total_tokens_used': ai_metrics.aggregate(total=Sum('tokens_used'))['total'] or 0,
            'total_cost_usd': float(ai_metrics.aggregate(total=Sum('cost_usd'))['total'] or 0),
            'success_rate_percent': (
                ai_metrics.filter(success=True).count() / 
                max(ai_metrics.count(), 1) * 100
            ),
        }
        
        # Error summary
        errors = ErrorLog.objects.filter(timestamp__gte=since)
        error_summary = {
            'total_errors': errors.count(),
            'critical_errors': errors.filter(level='CRITICAL').count(),
            'unresolved_errors': errors.filter(resolved=False).count(),
        }
        
        # Latest system health
        latest_health = SystemHealth.objects.order_by('-timestamp').first()
        health_summary = {}
        if latest_health:
            health_summary = {
                'cpu_usage_percent': latest_health.cpu_usage_percent,
                'memory_usage_percent': latest_health.memory_usage_percent,
                'api_requests_per_minute': latest_health.api_requests_per_minute,
                'api_error_rate_percent': latest_health.api_error_rate_percent,
                'redis_status': latest_health.redis_status,
                'postgres_status': latest_health.postgres_status,
                'timestamp': latest_health.timestamp.isoformat(),
            }
        
        return Response({
            'timeframe': '24 hours',
            'timestamp': timezone.now().isoformat(),
            'api_metrics': api_summary,
            'user_activity': user_summary,
            'ai_usage': ai_summary,
            'errors': error_summary,
            'system_health': health_summary,
        })
        
    except Exception as e:
        logger.error(f"Error generating dashboard overview: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to generate dashboard overview'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="API 성능 차트 데이터",
    operation_description="""
    API 성능 데이터를 차트 형태로 제공합니다.
    
    **관리자 권한 필요**
    
    **쿼리 파라미터:**
    - `hours`: 분석할 시간 범위 (기본값: 24시간)
    
    **응답 데이터:**
    - `chart_data`: 시간별 API 성능 데이터
    - `slow_endpoints`: 응답시간이 느린 엔드포인트 목록 (500ms 이상)
    """,
    tags=['Monitoring'],
    manual_parameters=[
        openapi.Parameter(
            'hours',
            openapi.IN_QUERY,
            description="분석할 시간 범위 (시간 단위)",
            type=openapi.TYPE_INTEGER,
            default=24
        )
    ],
    responses={
        200: openapi.Response(
            description="API 성능 차트 데이터",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'timeframe_hours': openapi.Schema(type=openapi.TYPE_INTEGER, description="분석 시간 범위"),
                    'chart_data': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'timestamp': openapi.Schema(type=openapi.TYPE_STRING, description="시간"),
                                'avg_response_time_ms': openapi.Schema(type=openapi.TYPE_NUMBER, description="평균 응답시간 (ms)"),
                                'request_count': openapi.Schema(type=openapi.TYPE_INTEGER, description="요청 수"),
                                'error_rate_percent': openapi.Schema(type=openapi.TYPE_NUMBER, description="에러율 (%)"),
                                'avg_query_count': openapi.Schema(type=openapi.TYPE_NUMBER, description="평균 쿼리 수"),
                            }
                        ),
                        description="시간별 성능 데이터"
                    ),
                    'slow_endpoints': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="느린 엔드포인트 목록"),
                },
            )
        ),
        401: "인증 필요",
        403: "관리자 권한 필요",
        500: "서버 오류",
    }
)
@api_view(['GET'])
@permission_classes([MonitoringPermission])
def api_performance_chart(request):
    """
    Get API performance data for charting
    """
    try:
        hours = int(request.GET.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)
        
        # Group by hour for time series data
        hourly_data = (
            APIMetrics.objects
            .filter(timestamp__gte=since)
            .extra(select={'hour': "date_trunc('hour', timestamp)"})
            .values('hour')
            .annotate(
                avg_response_time=Avg('response_time_ms'),
                request_count=Count('id'),
                error_count=Count('id', filter=Q(status_code__gte=400)),
                avg_query_count=Avg('query_count')
            )
            .order_by('hour')
        )
        
        chart_data = []
        for item in hourly_data:
            error_rate = (item['error_count'] / max(item['request_count'], 1)) * 100
            chart_data.append({
                'timestamp': item['hour'].isoformat(),
                'avg_response_time_ms': round(item['avg_response_time'] or 0, 2),
                'request_count': item['request_count'],
                'error_rate_percent': round(error_rate, 2),
                'avg_query_count': round(item['avg_query_count'] or 0, 2),
            })
        
        # Top slow endpoints
        slow_endpoints = (
            APIMetrics.objects
            .filter(timestamp__gte=since)
            .values('endpoint', 'method')
            .annotate(
                avg_response_time=Avg('response_time_ms'),
                request_count=Count('id')
            )
            .filter(avg_response_time__gt=500)
            .order_by('-avg_response_time')[:10]
        )
        
        return Response({
            'timeframe_hours': hours,
            'chart_data': chart_data,
            'slow_endpoints': list(slow_endpoints),
        })
        
    except Exception as e:
        logger.error(f"Error generating API performance chart: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to generate API performance chart'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="에러 분석 및 트렌드",
    operation_description="""
    시스템 에러 분석과 트렌드 데이터를 제공합니다.
    
    **관리자 권한 필요**
    
    **쿼리 파라미터:**
    - `days`: 분석할 일 수 (기본값: 7일)
    
    **응답 데이터:**
    - `daily_trends`: 일별 에러 트렌드
    - `top_error_types`: 빈발 에러 유형 (미해결 에러 우선)
    - `endpoint_errors`: 엔드포인트별 에러 발생률
    """,
    tags=['Monitoring'],
    manual_parameters=[
        openapi.Parameter(
            'days',
            openapi.IN_QUERY,
            description="분석할 일 수",
            type=openapi.TYPE_INTEGER,
            default=7
        )
    ],
    responses={
        200: openapi.Response(
            description="에러 분석 데이터",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'timeframe_days': openapi.Schema(type=openapi.TYPE_INTEGER, description="분석 기간 (일)"),
                    'daily_trends': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="일별 에러 트렌드"),
                    'top_error_types': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="빈발 에러 유형"),
                    'endpoint_errors': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="엔드포인트별 에러"),
                },
            )
        ),
        401: "인증 필요",
        403: "관리자 권한 필요",
        500: "서버 오류",
    }
)
@api_view(['GET'])
@permission_classes([MonitoringPermission])
def error_analysis(request):
    """
    Get error analysis and trending
    """
    try:
        days = int(request.GET.get('days', 7))
        since = timezone.now() - timedelta(days=days)
        
        # Error trends by day
        daily_errors = (
            ErrorLog.objects
            .filter(timestamp__gte=since)
            .extra(select={'date': "date_trunc('day', timestamp)"})
            .values('date')
            .annotate(
                total_errors=Count('id'),
                critical_errors=Count('id', filter=Q(level='CRITICAL')),
                error_errors=Count('id', filter=Q(level='ERROR')),
                warning_errors=Count('id', filter=Q(level='WARNING'))
            )
            .order_by('date')
        )
        
        # Top error types
        top_errors = (
            ErrorLog.objects
            .filter(timestamp__gte=since, resolved=False)
            .values('exception_type', 'endpoint')
            .annotate(
                count=Count('id'),
                latest_occurrence=Max('last_seen')
            )
            .order_by('-count')[:15]
        )
        
        # Endpoint error rates
        endpoint_errors = (
            ErrorLog.objects
            .filter(timestamp__gte=since)
            .exclude(endpoint='')
            .values('endpoint')
            .annotate(
                error_count=Count('id'),
                unique_error_types=Count('exception_type', distinct=True)
            )
            .order_by('-error_count')[:10]
        )
        
        return Response({
            'timeframe_days': days,
            'daily_trends': [
                {
                    'date': item['date'].date().isoformat(),
                    'total_errors': item['total_errors'],
                    'critical_errors': item['critical_errors'],
                    'error_errors': item['error_errors'],
                    'warning_errors': item['warning_errors'],
                }
                for item in daily_errors
            ],
            'top_error_types': [
                {
                    'exception_type': item['exception_type'],
                    'endpoint': item['endpoint'],
                    'count': item['count'],
                    'latest_occurrence': item['latest_occurrence'].isoformat(),
                }
                for item in top_errors
            ],
            'endpoint_errors': list(endpoint_errors),
        })
        
    except Exception as e:
        logger.error(f"Error generating error analysis: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to generate error analysis'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="AI 사용량 분석 및 비용 추적",
    operation_description="""
    AI 서비스 사용량 분석과 비용 추적 데이터를 제공합니다.
    
    **관리자 권한 필요**
    
    **쿼리 파라미터:**
    - `days`: 분석할 일 수 (기본값: 30일)
    
    **응답 데이터:**
    - `daily_usage`: 일별 AI 사용량 (작업 수, 토큰, 비용, 처리시간, 성공률)
    - `operation_stats`: 작업 유형별 통계
    - `subscription_tier_usage`: 구독 티어별 사용량
    - `top_users`: AI 사용량이 많은 상위 사용자
    """,
    tags=['Monitoring'],
    manual_parameters=[
        openapi.Parameter(
            'days',
            openapi.IN_QUERY,
            description="분석할 일 수",
            type=openapi.TYPE_INTEGER,
            default=30
        )
    ],
    responses={
        200: openapi.Response(
            description="AI 사용량 분석 데이터",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'timeframe_days': openapi.Schema(type=openapi.TYPE_INTEGER, description="분석 기간 (일)"),
                    'daily_usage': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="일별 AI 사용량"),
                    'operation_stats': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="작업 유형별 통계"),
                    'subscription_tier_usage': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="구독 티어별 사용량"),
                    'top_users': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="상위 사용자"),
                },
            )
        ),
        401: "인증 필요",
        403: "관리자 권한 필요",
        500: "서버 오류",
    }
)
@api_view(['GET'])
@permission_classes([MonitoringPermission])
def ai_usage_analytics(request):
    """
    Get AI usage analytics and cost tracking
    """
    try:
        days = int(request.GET.get('days', 30))
        since = timezone.now() - timedelta(days=days)
        
        # Daily AI usage
        daily_usage = (
            AIMetrics.objects
            .filter(timestamp__gte=since)
            .extra(select={'date': "date_trunc('day', timestamp)"})
            .values('date')
            .annotate(
                total_operations=Count('id'),
                total_tokens=Sum('tokens_used'),
                total_cost=Sum('cost_usd'),
                avg_processing_time=Avg('processing_time_ms'),
                success_rate=Avg('success') * 100
            )
            .order_by('date')
        )
        
        # Usage by operation type
        operation_stats = (
            AIMetrics.objects
            .filter(timestamp__gte=since)
            .values('operation_type')
            .annotate(
                count=Count('id'),
                total_tokens=Sum('tokens_used'),
                total_cost=Sum('cost_usd'),
                avg_quality=Avg('quality_score')
            )
            .order_by('-count')
        )
        
        # Usage by subscription tier
        tier_usage = (
            AIMetrics.objects
            .filter(timestamp__gte=since)
            .exclude(subscription_tier='')
            .values('subscription_tier')
            .annotate(
                user_count=Count('user', distinct=True),
                operation_count=Count('id'),
                total_cost=Sum('cost_usd')
            )
            .order_by('-operation_count')
        )
        
        # Top users by AI usage
        top_users = (
            AIMetrics.objects
            .filter(timestamp__gte=since)
            .values('user__email', 'subscription_tier')
            .annotate(
                operation_count=Count('id'),
                total_tokens=Sum('tokens_used'),
                total_cost=Sum('cost_usd')
            )
            .order_by('-operation_count')[:10]
        )
        
        return Response({
            'timeframe_days': days,
            'daily_usage': [
                {
                    'date': item['date'].date().isoformat(),
                    'total_operations': item['total_operations'],
                    'total_tokens': item['total_tokens'] or 0,
                    'total_cost_usd': float(item['total_cost'] or 0),
                    'avg_processing_time_ms': round(item['avg_processing_time'] or 0, 2),
                    'success_rate_percent': round(item['success_rate'] or 0, 2),
                }
                for item in daily_usage
            ],
            'operation_stats': [
                {
                    'operation_type': item['operation_type'],
                    'count': item['count'],
                    'total_tokens': item['total_tokens'] or 0,
                    'total_cost_usd': float(item['total_cost'] or 0),
                    'avg_quality_score': round(item['avg_quality'] or 0, 2) if item['avg_quality'] else None,
                }
                for item in operation_stats
            ],
            'subscription_tier_usage': list(tier_usage),
            'top_users': [
                {
                    'email': item['user__email'],
                    'subscription_tier': item['subscription_tier'],
                    'operation_count': item['operation_count'],
                    'total_tokens': item['total_tokens'] or 0,
                    'total_cost_usd': float(item['total_cost'] or 0),
                }
                for item in top_users
            ],
        })
        
    except Exception as e:
        logger.error(f"Error generating AI usage analytics: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to generate AI usage analytics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="시스템 헬스 체크",
    operation_description="""
    공개적으로 접근 가능한 시스템 상태 확인 엔드포인트입니다.
    
    **인증 불필요**
    
    **응답 상태 코드:**
    - `200`: 시스템 정상
    - `206`: 시스템 부분적 문제 (degraded)
    - `503`: 시스템 비정상 (unhealthy)
    
    **상태 확인 항목:**
    - 데이터베이스 연결
    - Redis 연결
    - Celery 작업자 상태
    - API 응답 시간
    """,
    tags=['Monitoring'],
    responses={
        200: openapi.Response(
            description="시스템 정상",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'overall_status': openapi.Schema(type=openapi.TYPE_STRING, description="전체 상태 (healthy/degraded/unhealthy)"),
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, description="체크 시각"),
                    'checks': openapi.Schema(type=openapi.TYPE_OBJECT, description="개별 체크 결과"),
                }
            )
        ),
        206: "시스템 부분적 문제",
        503: "시스템 비정상",
    }
)
@api_view(['GET'])
def health_check(request):
    """
    Public health check endpoint
    """
    try:
        health_data = check_system_health()
        
        status_code = status.HTTP_200_OK
        if health_data['overall_status'] == 'unhealthy':
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif health_data['overall_status'] == 'degraded':
            status_code = status.HTTP_206_PARTIAL_CONTENT
        
        return Response(health_data, status=status_code)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return Response(
            {
                'overall_status': 'unhealthy',
                'error': 'Health check failed',
                'timestamp': timezone.now().isoformat()
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@swagger_auto_schema(
    method='get',
    operation_summary="성능 인사이트 및 추천사항",
    operation_description="""
    시스템 성능 인사이트와 개선 추천사항을 제공합니다.
    
    **관리자 권한 필요**
    
    **쿼리 파라미터:**
    - `hours`: 분석할 시간 범위 (기본값: 24시간)
    
    **응답 데이터:**
    - 성능 병목 지점 식별
    - 최적화 추천사항
    - 리소스 사용률 분석
    - 예상 확장성 문제
    """,
    tags=['Monitoring'],
    manual_parameters=[
        openapi.Parameter(
            'hours',
            openapi.IN_QUERY,
            description="분석할 시간 범위 (시간 단위)",
            type=openapi.TYPE_INTEGER,
            default=24
        )
    ],
    responses={
        200: openapi.Response(
            description="성능 인사이트 데이터",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'insights': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="성능 인사이트"),
                    'recommendations': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="추천사항"),
                    'performance_score': openapi.Schema(type=openapi.TYPE_NUMBER, description="전체 성능 점수"),
                }
            )
        ),
        401: "인증 필요",
        403: "관리자 권한 필요",
        500: "서버 오류",
    }
)
@api_view(['GET'])
@permission_classes([MonitoringPermission])
def performance_insights(request):
    """
    Get performance insights and recommendations
    """
    try:
        hours = int(request.GET.get('hours', 24))
        insights = get_performance_insights(hours)
        
        return Response(insights)
        
    except Exception as e:
        logger.error(f"Error generating performance insights: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to generate performance insights'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_summary="오래된 모니터링 데이터 정리",
    operation_description="""
    지정된 기간보다 오래된 모니터링 데이터를 삭제합니다.
    
    **관리자 권한 필요**
    
    **요청 예시:**
    ```json
    {
      "days_to_keep": 30
    }
    ```
    
    **주의사항:**
    - 이 작업은 되돌릴 수 없습니다
    - 기본값은 30일입니다
    - 중요한 에러 로그는 더 오래 보관될 수 있습니다
    """,
    tags=['Monitoring'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'days_to_keep': openapi.Schema(type=openapi.TYPE_INTEGER, description="보관할 일 수 (기본값: 30일)"),
        }
    ),
    responses={
        200: openapi.Response(
            description="데이터 정리 완료",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="성공 여부"),
                    'deleted_records': openapi.Schema(type=openapi.TYPE_INTEGER, description="삭제된 레코드 수"),
                    'days_kept': openapi.Schema(type=openapi.TYPE_INTEGER, description="보관 기간 (일)"),
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, description="처리 시각"),
                }
            )
        ),
        401: "인증 필요",
        403: "관리자 권한 필요",
        500: "서버 오류",
    }
)
@api_view(['POST'])
@permission_classes([MonitoringPermission])
def cleanup_old_data(request):
    """
    Clean up old monitoring data
    """
    try:
        days_to_keep = int(request.data.get('days_to_keep', 30))
        deleted_count = clean_old_metrics(days_to_keep)
        
        return Response({
            'success': True,
            'deleted_records': deleted_count,
            'days_kept': days_to_keep,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to clean up old data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


"""
API views for alert system
"""
import logging
from datetime import timedelta
from typing import Dict, Any

from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncHour
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.cache import cache

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import AlertRule, AlertHistory
from .serializers import (
    AlertRuleSerializer, AlertRuleCreateSerializer, AlertHistorySerializer,
    AlertHistoryResolveSerializer, AlertStatisticsSerializer,
    TestNotificationSerializer, ManualTriggerSerializer
)
from .alert_services.alert_engine import AlertEngine
from .alert_services.slack_notifier import SlackNotifier
from .alert_services.email_notifier import EmailNotifier
from .tasks import check_specific_alert_rule, test_alert_notifications
from .permissions import (
    MonitoringPermission, AlertRulePermission, AlertHistoryPermission, AdminOnlyPermission
)

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class AlertRuleListCreateView(generics.ListCreateAPIView):
    """
    List all alert rules or create a new one
    """
    queryset = AlertRule.objects.all().select_related('created_by')
    serializer_class = AlertRuleSerializer
    permission_classes = [AlertRulePermission]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AlertRuleCreateSerializer
        return AlertRuleSerializer
    
    def get_queryset(self):
        queryset = AlertRule.objects.all().select_related('created_by')
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by alert type
        alert_type = self.request.query_params.get('alert_type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # Filter by metric name
        metric_name = self.request.query_params.get('metric_name')
        if metric_name:
            queryset = queryset.filter(metric_name=metric_name)
        
        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.order_by('-created_at')

    @swagger_auto_schema(
        operation_summary="List alert rules",
        operation_description="Get a paginated list of all alert rules with filtering options",
        manual_parameters=[
            openapi.Parameter('is_active', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description='Filter by active status'),
            openapi.Parameter('alert_type', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Filter by alert type'),
            openapi.Parameter('severity', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Filter by severity'),
            openapi.Parameter('metric_name', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Filter by metric name'),
            openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Search by rule name'),
        ],
        tags=['Alerts - Rules']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create alert rule",
        operation_description="Create a new alert rule",
        tags=['Alerts - Rules']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AlertRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a specific alert rule
    """
    queryset = AlertRule.objects.all().select_related('created_by')
    serializer_class = AlertRuleSerializer
    permission_classes = [AlertRulePermission]

    @swagger_auto_schema(
        operation_summary="Get alert rule",
        operation_description="Retrieve details of a specific alert rule",
        tags=['Alerts - Rules']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update alert rule",
        operation_description="Update an existing alert rule",
        tags=['Alerts - Rules']
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update alert rule",
        operation_description="Partially update an existing alert rule",
        tags=['Alerts - Rules']
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete alert rule",
        operation_description="Delete an alert rule",
        tags=['Alerts - Rules']
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class AlertHistoryListView(generics.ListAPIView):
    """
    List alert history with filtering
    """
    serializer_class = AlertHistorySerializer
    permission_classes = [AlertHistoryPermission]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = AlertHistory.objects.all().select_related('rule', 'resolved_by')
        
        # Filter by rule
        rule_id = self.request.query_params.get('rule')
        if rule_id:
            queryset = queryset.filter(rule_id=rule_id)
        
        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(rule__severity=severity)
        
        # Filter by resolved status
        resolved = self.request.query_params.get('resolved')
        if resolved is not None:
            if resolved.lower() == 'true':
                queryset = queryset.filter(resolved_at__isnull=False)
            else:
                queryset = queryset.filter(resolved_at__isnull=True)
        
        # Filter by time range
        hours = self.request.query_params.get('hours')
        if hours:
            try:
                hours_int = int(hours)
                since = timezone.now() - timedelta(hours=hours_int)
                queryset = queryset.filter(triggered_at__gte=since)
            except ValueError:
                pass
        
        return queryset.order_by('-triggered_at')

    @swagger_auto_schema(
        operation_summary="List alert history",
        operation_description="Get a paginated list of alert history with filtering options",
        manual_parameters=[
            openapi.Parameter('rule', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Filter by rule ID'),
            openapi.Parameter('severity', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Filter by severity'),
            openapi.Parameter('resolved', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description='Filter by resolved status'),
            openapi.Parameter('hours', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Filter by hours ago'),
        ],
        tags=['Alerts - History']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AlertHistoryDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific alert
    """
    queryset = AlertHistory.objects.all().select_related('rule', 'resolved_by')
    serializer_class = AlertHistorySerializer
    permission_classes = [AlertRulePermission]

    @swagger_auto_schema(
        operation_summary="Get alert history details",
        operation_description="Retrieve details of a specific alert",
        tags=['Alerts - History']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@swagger_auto_schema(
    method='post',
    operation_summary="Resolve alert",
    operation_description="Mark an alert as resolved with optional resolution notes",
    request_body=AlertHistoryResolveSerializer,
    responses={
        200: AlertHistorySerializer,
        404: "Alert not found",
        400: "Invalid input"
    },
    tags=['Alerts - History']
)
@api_view(['POST'])
@permission_classes([AdminOnlyPermission])
def resolve_alert(request, pk):
    """
    Resolve a specific alert
    """
    try:
        alert = get_object_or_404(AlertHistory, pk=pk)
        
        if alert.is_resolved:
            return Response(
                {'detail': 'Alert is already resolved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = AlertHistoryResolveSerializer(
            alert, 
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            updated_alert = serializer.save()
            result_serializer = AlertHistorySerializer(updated_alert)
            
            logger.info(f"Alert {pk} resolved by {request.user.email}")
            
            return Response(result_serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error resolving alert {pk}: {str(e)}")
        return Response(
            {'detail': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Get alert statistics",
    operation_description="Get comprehensive alert statistics and metrics",
    responses={200: AlertStatisticsSerializer},
    tags=['Alerts - Analytics']
)
@api_view(['GET'])
@permission_classes([AdminOnlyPermission])
def alert_statistics(request):
    """
    Get alert statistics and metrics
    """
    try:
        # Check cache first
        cache_key = 'alert_statistics'
        stats = cache.get(cache_key)
        
        if stats is None:
            stats = _calculate_alert_statistics()
            cache.set(cache_key, stats, 300)  # 5 minute cache
        
        serializer = AlertStatisticsSerializer(stats)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting alert statistics: {str(e)}")
        return Response(
            {'detail': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_summary="Test Slack notification",
    operation_description="Send a test message to Slack to verify integration",
    request_body=TestNotificationSerializer,
    responses={
        200: openapi.Response(description="Test message sent successfully"),
        400: "Invalid configuration or input",
        500: "Failed to send test message"
    },
    tags=['Alerts - Testing']
)
@api_view(['POST'])
@permission_classes([AdminOnlyPermission])
def test_slack_notification(request):
    """
    Test Slack notification integration
    """
    try:
        serializer = TestNotificationSerializer(data=request.data)
        
        if serializer.is_valid():
            channel = serializer.validated_data.get('custom_channel') or '#alerts'
            
            slack_notifier = SlackNotifier()
            
            if not slack_notifier.is_configured:
                return Response(
                    {'detail': 'Slack integration is not configured'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = slack_notifier.send_test_message(channel)
            
            if result['success']:
                logger.info(f"Slack test message sent successfully to {channel}")
                return Response(result, status=status.HTTP_200_OK)
            else:
                logger.error(f"Failed to send Slack test message: {result.get('error')}")
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error testing Slack notification: {str(e)}")
        return Response(
            {'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_summary="Test email notification",
    operation_description="Send a test email to verify email integration",
    request_body=TestNotificationSerializer,
    responses={
        200: openapi.Response(description="Test email sent successfully"),
        400: "Invalid configuration or input",
        500: "Failed to send test email"
    },
    tags=['Alerts - Testing']
)
@api_view(['POST'])
@permission_classes([AdminOnlyPermission])
def test_email_notification(request):
    """
    Test email notification integration
    """
    try:
        serializer = TestNotificationSerializer(data=request.data)
        
        if serializer.is_valid():
            recipients = serializer.validated_data.get('custom_recipients')
            
            email_notifier = EmailNotifier()
            
            if not email_notifier.is_configured:
                return Response(
                    {'detail': 'Email integration is not configured'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = email_notifier.send_test_email(recipients)
            
            if result['success']:
                logger.info(f"Test email sent successfully to {len(recipients or [])} recipients")
                return Response(result, status=status.HTTP_200_OK)
            else:
                logger.error(f"Failed to send test email: {result.get('error')}")
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error testing email notification: {str(e)}")
        return Response(
            {'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_summary="Manual trigger check",
    operation_description="Manually trigger alert rule checks",
    request_body=ManualTriggerSerializer,
    responses={
        200: openapi.Response(description="Alert check triggered successfully"),
        400: "Invalid input",
        500: "Failed to trigger alert check"
    },
    tags=['Alerts - Management']
)
@api_view(['POST'])
@permission_classes([AdminOnlyPermission])
def manual_trigger_check(request):
    """
    Manually trigger alert rule checks
    """
    try:
        serializer = ManualTriggerSerializer(data=request.data)
        
        if serializer.is_valid():
            rule_ids = serializer.validated_data.get('rule_ids', [])
            force = serializer.validated_data.get('force', False)
            
            if rule_ids:
                # Check specific rules
                results = []
                for rule_id in rule_ids:
                    try:
                        # Use Celery task for async processing
                        task = check_specific_alert_rule.delay(rule_id)
                        results.append({
                            'rule_id': rule_id,
                            'task_id': task.id,
                            'status': 'queued'
                        })
                    except Exception as e:
                        results.append({
                            'rule_id': rule_id,
                            'error': str(e),
                            'status': 'error'
                        })
                
                logger.info(f"Manual alert check triggered for {len(rule_ids)} rules")
                
                return Response({
                    'detail': f'Alert check triggered for {len(rule_ids)} rules',
                    'results': results
                }, status=status.HTTP_200_OK)
            
            else:
                # Check all rules using the main alert engine
                engine = AlertEngine()
                results = engine.check_all_rules()
                
                logger.info("Manual alert check triggered for all rules")
                
                return Response({
                    'detail': 'Alert check triggered for all rules',
                    'results': results
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error in manual trigger check: {str(e)}")
        return Response(
            {'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _calculate_alert_statistics() -> Dict[str, Any]:
    """
    Calculate comprehensive alert statistics
    """
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_week = now - timedelta(days=7)
    last_month = now - timedelta(days=30)
    
    # Rule statistics
    total_rules = AlertRule.objects.count()
    active_rules = AlertRule.objects.filter(is_active=True).count()
    inactive_rules = total_rules - active_rules
    
    # Alert count statistics
    total_alerts_24h = AlertHistory.objects.filter(triggered_at__gte=last_24h).count()
    total_alerts_week = AlertHistory.objects.filter(triggered_at__gte=last_week).count()
    total_alerts_month = AlertHistory.objects.filter(triggered_at__gte=last_month).count()
    
    # Severity breakdown for last 24h
    severity_counts = AlertHistory.objects.filter(
        triggered_at__gte=last_24h
    ).values('rule__severity').annotate(count=Count('id'))
    
    severity_dict = {item['rule__severity']: item['count'] for item in severity_counts}
    critical_alerts_24h = severity_dict.get('critical', 0)
    high_alerts_24h = severity_dict.get('high', 0)
    medium_alerts_24h = severity_dict.get('medium', 0)
    low_alerts_24h = severity_dict.get('low', 0)
    
    # Resolution statistics
    unresolved_alerts = AlertHistory.objects.filter(resolved_at__isnull=True).count()
    resolved_alerts_24h = AlertHistory.objects.filter(
        triggered_at__gte=last_24h,
        resolved_at__isnull=False
    ).count()
    
    # Notification success rate
    alerts_24h = AlertHistory.objects.filter(triggered_at__gte=last_24h)
    if alerts_24h.exists():
        successful_notifications = alerts_24h.filter(
            Q(slack_sent=True) | Q(email_sent=True)
        ).count()
        notification_success_rate_24h = (successful_notifications / total_alerts_24h) * 100
    else:
        notification_success_rate_24h = 0.0
    
    # Most triggered rule and metric
    most_triggered_rule_data = AlertHistory.objects.filter(
        triggered_at__gte=last_week
    ).values('rule__name').annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    most_triggered_rule = most_triggered_rule_data['rule__name'] if most_triggered_rule_data else 'None'
    
    most_triggered_metric_data = AlertHistory.objects.filter(
        triggered_at__gte=last_week
    ).values('rule__metric_name').annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    most_triggered_metric = most_triggered_metric_data['rule__metric_name'] if most_triggered_metric_data else 'None'
    
    # Hourly breakdown for last 24h
    hourly_data = AlertHistory.objects.filter(
        triggered_at__gte=last_24h
    ).annotate(
        hour=TruncHour('triggered_at')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour')
    
    alerts_by_hour = [
        {
            'hour': item['hour'].strftime('%H:00'),
            'count': item['count']
        } for item in hourly_data
    ]
    
    # Type breakdown
    type_counts = AlertHistory.objects.filter(
        triggered_at__gte=last_24h
    ).values('rule__alert_type').annotate(count=Count('id'))
    
    alerts_by_type = {item['rule__alert_type']: item['count'] for item in type_counts}
    
    return {
        'total_rules': total_rules,
        'active_rules': active_rules,
        'inactive_rules': inactive_rules,
        'total_alerts_24h': total_alerts_24h,
        'total_alerts_week': total_alerts_week,
        'total_alerts_month': total_alerts_month,
        'critical_alerts_24h': critical_alerts_24h,
        'high_alerts_24h': high_alerts_24h,
        'medium_alerts_24h': medium_alerts_24h,
        'low_alerts_24h': low_alerts_24h,
        'unresolved_alerts': unresolved_alerts,
        'resolved_alerts_24h': resolved_alerts_24h,
        'notification_success_rate_24h': round(notification_success_rate_24h, 2),
        'most_triggered_rule': most_triggered_rule,
        'most_triggered_metric': most_triggered_metric,
        'alerts_by_hour': alerts_by_hour,
        'alerts_by_severity': severity_dict,
        'alerts_by_type': alerts_by_type,
    }