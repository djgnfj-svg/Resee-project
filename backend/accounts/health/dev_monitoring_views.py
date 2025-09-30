"""
Development-only monitoring views (no authentication required).
"""
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .health_views import health_detailed
from .log_views import log_summary, recent_errors, log_analytics


def dev_monitoring_dashboard(request):
    """개발 환경용 모니터링 대시보드 (인증 불필요)"""
    if not settings.DEBUG:
        return JsonResponse({'error': 'Development only'}, status=403)

    return render(request, 'accounts/dev_monitoring_dashboard.html')


@api_view(['GET'])
@permission_classes([AllowAny])
def dev_dashboard_data(request):
    """개발 환경용 대시보드 데이터 (인증 불필요)"""
    if not settings.DEBUG:
        return Response({'error': 'Development only'}, status=403)

    try:
        # 헬스체크 데이터를 직접 구현 (간단 버전)
        import time
        from django.db import connection

        start_time = time.time()
        health_data = {
            'status': 'healthy',
            'timestamp': int(start_time),
            'services': {}
        }

        # Database check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            health_data['services']['database'] = {
                'status': 'healthy',
                'response_time_ms': round((time.time() - start_time) * 1000, 2)
            }
        except Exception as e:
            health_data['services']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_data['status'] = 'degraded'

        # 간단한 디스크 체크
        try:
            import shutil
            disk_usage = shutil.disk_usage('/')
            total_gb = disk_usage.total / (1024**3)
            free_gb = disk_usage.free / (1024**3)
            used_gb = (disk_usage.total - disk_usage.free) / (1024**3)
            usage_percent = (used_gb / total_gb) * 100

            health_data['services']['disk'] = {
                'status': 'healthy' if usage_percent < 80 else 'warning',
                'usage_percent': round(usage_percent, 2),
                'free_gb': round(free_gb, 2)
            }
        except Exception as e:
            health_data['services']['disk'] = {
                'status': 'unhealthy',
                'error': str(e)
            }

        health_data['total_response_time_ms'] = round((time.time() - start_time) * 1000, 2)

        # 로그 요약 데이터 (Django HttpRequest로 직접 호출)
        try:
            from django.http import HttpRequest
            django_request = HttpRequest()
            django_request.method = 'GET'
            django_request.META = request.META.copy()
            django_request.user = request.user

            from ..log_views import get_log_directory, ensure_log_directory
            import os
            import glob
            from datetime import datetime

            log_dir = get_log_directory()
            if os.path.exists(log_dir):
                log_files = []
                for ext in ['*.log', '*.log.*']:
                    log_files.extend(glob.glob(os.path.join(log_dir, ext)))

                files_info = []
                total_size = 0
                for log_file in sorted(log_files):
                    try:
                        stat = os.stat(log_file)
                        file_size = stat.st_size
                        total_size += file_size
                        files_info.append({
                            'name': os.path.basename(log_file),
                            'size_bytes': file_size,
                            'size_mb': round(file_size / (1024 * 1024), 2),
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        })
                    except OSError:
                        continue

                log_data = {
                    'status': 'success',
                    'total_files': len(files_info),
                    'total_size_mb': round(total_size / (1024 * 1024), 2),
                    'files': files_info
                }
            else:
                log_data = {'status': 'no_logs', 'message': 'Log directory does not exist'}
        except Exception as e:
            log_data = {'status': 'error', 'message': f'Log access error: {str(e)}'}

        # 최근 에러 데이터 (간단한 구현)
        try:
            error_data = {'status': 'unavailable', 'message': 'Error log parsing not available in dev mode'}
        except Exception as e:
            error_data = {'status': 'error', 'message': f'Error log access error: {str(e)}'}

        # 로그 분석 데이터 (간단한 구현)
        try:
            analytics_data = {'status': 'unavailable', 'message': 'Analytics not available in dev mode'}
        except Exception as e:
            analytics_data = {'status': 'error', 'message': f'Analytics access error: {str(e)}'}

        return Response({
            'health': health_data,
            'logs': log_data,
            'recent_errors': error_data,
            'analytics': analytics_data,
            'timestamp': health_data.get('timestamp', 0),
            'environment': 'development'
        })

    except Exception as e:
        return Response({
            'error': str(e),
            'timestamp': 0,
            'environment': 'development'
        }, status=500)


def dev_log_viewer(request):
    """개발 환경용 로그 뷰어 (인증 불필요)"""
    if not settings.DEBUG:
        return JsonResponse({'error': 'Development only'}, status=403)

    return render(request, 'accounts/dev_log_viewer.html')


@api_view(['GET'])
@permission_classes([AllowAny])
def dev_log_summary(request):
    """개발 환경용 로그 요약 (인증 불필요)"""
    if not settings.DEBUG:
        return Response({'error': 'Development only'}, status=403)

    try:
        return log_summary(request)
    except Exception as e:
        return Response({
            'status': 'error',
            'error': f'Log access error: {str(e)}',
            'development_note': 'This endpoint requires proper log file permissions'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def dev_log_file_content(request, filename):
    """개발 환경용 로그 파일 내용 (인증 불필요)"""
    if not settings.DEBUG:
        return Response({'error': 'Development only'}, status=403)

    from .log_views import log_file_content
    try:
        return log_file_content(request, filename)
    except Exception as e:
        return Response({
            'status': 'error',
            'error': f'Log file access error: {str(e)}',
            'development_note': 'This endpoint requires proper log file permissions'
        }, status=500)