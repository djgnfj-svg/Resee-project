"""
API views for monitoring dashboard
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Avg, Count, Sum, Max, Min, Q
from django.db.models.functions import TruncDate, TruncHour
from django.db import models
from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from .models import (
    APIMetrics, DatabaseMetrics, AIMetrics, ErrorLog, 
    SystemHealth, UserActivity
)
from .utils import check_system_health, get_performance_insights, clean_old_metrics

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
@permission_classes([IsAdminUser])
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
@permission_classes([IsAdminUser])
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
@permission_classes([IsAdminUser])
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
@permission_classes([IsAdminUser])
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
@permission_classes([IsAdminUser])
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
@permission_classes([IsAdminUser])
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