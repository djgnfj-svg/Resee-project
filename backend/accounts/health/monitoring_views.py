"""
Monitoring dashboard API - 통합 모니터링 데이터 제공
"""
import os
import glob
import time
import shutil
from datetime import datetime, timedelta
from django.conf import settings
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status as http_status


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_data(request):
    """통합 대시보드 데이터 (개발 환경에서는 인증 불필요)"""
    # Production에서는 관리자 권한 체크
    if not settings.DEBUG and not request.user.is_staff:
        return Response({'error': 'Permission denied'}, status=http_status.HTTP_403_FORBIDDEN)

    try:
        start_time = time.time()

        # 1. 기본 헬스체크
        health_data = {
            'status': 'healthy',
            'timestamp': int(start_time)
        }

        # 2. 데이터베이스 체크
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            health_data['database'] = 'healthy'
        except Exception:
            health_data['database'] = 'unhealthy'
            health_data['status'] = 'degraded'

        # 3. 디스크 체크
        try:
            disk_usage = shutil.disk_usage('/')
            usage_percent = ((disk_usage.total - disk_usage.free) / disk_usage.total) * 100
            health_data['disk_usage_percent'] = round(usage_percent, 2)
            health_data['disk_free_gb'] = round(disk_usage.free / (1024**3), 2)
        except Exception:
            health_data['disk_usage_percent'] = None

        # 4. 로그 파일 정보
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        log_info = {'total_files': 0, 'total_size_mb': 0}

        if os.path.exists(log_dir):
            log_files = []
            for ext in ['*.log', '*.log.*']:
                log_files.extend(glob.glob(os.path.join(log_dir, ext)))

            total_size = sum(os.path.getsize(f) for f in log_files if os.path.exists(f))
            log_info = {
                'total_files': len(log_files),
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }

        return Response({
            'health': health_data,
            'logs': log_info,
            'environment': 'development' if settings.DEBUG else 'production',
            'response_time_ms': round((time.time() - start_time) * 1000, 2)
        })

    except Exception as e:
        return Response({
            'error': str(e),
            'timestamp': int(time.time())
        }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)