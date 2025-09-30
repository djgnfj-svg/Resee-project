"""
Web-based monitoring dashboard views.
"""
import json
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .health_views import health_detailed
from .log_views import log_summary, recent_errors, log_analytics


@staff_member_required
def monitoring_dashboard(request):
    """모니터링 대시보드 메인 페이지"""
    return render(request, 'accounts/monitoring_dashboard.html')


@api_view(['GET'])
@permission_classes([IsAdminUser])
def dashboard_data(request):
    """대시보드에서 사용할 통합 데이터 제공"""
    try:
        # 헬스체크 데이터
        health_response = health_detailed(request)
        health_data = health_response.data if hasattr(health_response, 'data') else {}

        # 로그 요약 데이터
        log_response = log_summary(request)
        log_data = log_response.data if hasattr(log_response, 'data') else {}

        # 최근 에러 데이터
        error_response = recent_errors(request)
        error_data = error_response.data if hasattr(error_response, 'data') else {}

        # 로그 분석 데이터
        analytics_response = log_analytics(request)
        analytics_data = analytics_response.data if hasattr(analytics_response, 'data') else {}

        return Response({
            'health': health_data,
            'logs': log_data,
            'recent_errors': error_data,
            'analytics': analytics_data,
            'timestamp': health_data.get('timestamp', 0)
        })

    except Exception as e:
        return Response({
            'error': str(e),
            'timestamp': 0
        }, status=500)


@staff_member_required
def system_status(request):
    """시스템 상태 간단 페이지"""
    return render(request, 'accounts/system_status.html')


@staff_member_required
def log_viewer(request):
    """로그 뷰어 페이지"""
    return render(request, 'accounts/log_viewer.html')