"""
Log management and monitoring views for centralized log collection.
"""
import os
import glob
import json
from datetime import datetime, timedelta
from pathlib import Path
from django.conf import settings
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


def check_permission(request):
    """개발 환경에서는 모든 접근 허용, 운영 환경에서는 관리자만 허용"""
    if not settings.DEBUG and not request.user.is_staff:
        return False
    return True


def get_log_directory():
    """Get the log directory path"""
    return os.path.join(settings.BASE_DIR, 'logs')


def ensure_log_directory():
    """Ensure log directory exists"""
    log_dir = get_log_directory()
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


@api_view(['GET'])
@permission_classes([AllowAny])
def log_summary(request):
    """Get summary of log files and recent errors"""
    if not check_permission(request):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    try:
        log_dir = get_log_directory()

        if not os.path.exists(log_dir):
            return Response({
                'status': 'no_logs',
                'message': 'Log directory does not exist',
                'log_directory': log_dir
            })

        # Get all log files
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
                    'path': log_file,
                    'size_bytes': file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
            except OSError:
                continue

        return Response({
            'status': 'success',
            'log_directory': log_dir,
            'total_files': len(files_info),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'files': files_info
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def recent_errors(request):
    """Get recent error logs"""
    if not check_permission(request):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    try:
        log_dir = get_log_directory()
        hours = int(request.GET.get('hours', 24))
        cutoff_time = datetime.now() - timedelta(hours=hours)

        error_logs = []

        # Check error log file
        error_log_path = os.path.join(log_dir, 'django_error.log')
        if os.path.exists(error_log_path):
            with open(error_log_path, 'r') as f:
                lines = f.readlines()
                for line in reversed(lines[-1000:]):  # Last 1000 lines
                    if '[ERROR]' in line or '[CRITICAL]' in line:
                        try:
                            # Parse timestamp from log line
                            if line.startswith('['):
                                timestamp_str = line.split('] ')[1].split(' [')[0]
                                log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

                                if log_time >= cutoff_time:
                                    error_logs.append({
                                        'timestamp': log_time.isoformat(),
                                        'level': 'ERROR' if '[ERROR]' in line else 'CRITICAL',
                                        'message': line.strip(),
                                        'source': 'django_error.log'
                                    })
                        except (ValueError, IndexError):
                            # Skip malformed log lines
                            continue

        return Response({
            'status': 'success',
            'hours_searched': hours,
            'error_count': len(error_logs),
            'errors': sorted(error_logs, key=lambda x: x['timestamp'], reverse=True)[:100]  # Last 100 errors
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def log_file_content(request, filename):
    """Get content of a specific log file"""
    if not check_permission(request):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    try:
        log_dir = get_log_directory()
        file_path = os.path.join(log_dir, filename)

        # Security check - ensure file is within log directory
        if not os.path.abspath(file_path).startswith(os.path.abspath(log_dir)):
            return Response({
                'status': 'error',
                'error': 'Invalid file path'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not os.path.exists(file_path):
            return Response({
                'status': 'error',
                'error': 'File not found'
            }, status=status.HTTP_404_NOT_FOUND)

        lines = int(request.GET.get('lines', 100))
        level_filter = request.GET.get('level', None)  # ERROR, WARNING, INFO, etc.

        content_lines = []
        with open(file_path, 'r') as f:
            all_lines = f.readlines()

            # Filter by level if specified
            if level_filter:
                filtered_lines = [line for line in all_lines if f'[{level_filter.upper()}]' in line]
                content_lines = filtered_lines[-lines:] if filtered_lines else []
            else:
                content_lines = all_lines[-lines:]

        return Response({
            'status': 'success',
            'filename': filename,
            'lines_returned': len(content_lines),
            'level_filter': level_filter,
            'content': [line.strip() for line in content_lines]
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def cleanup_old_logs(request):
    """Clean up old log files"""
    if not check_permission(request):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    try:
        log_dir = get_log_directory()
        days = int(request.GET.get('days', 7))
        cutoff_time = datetime.now() - timedelta(days=days)

        deleted_files = []
        total_size_freed = 0

        log_files = glob.glob(os.path.join(log_dir, '*.log.*'))  # Rotated logs only

        for log_file in log_files:
            try:
                stat = os.stat(log_file)
                if datetime.fromtimestamp(stat.st_mtime) < cutoff_time:
                    file_size = stat.st_size
                    os.remove(log_file)
                    deleted_files.append({
                        'name': os.path.basename(log_file),
                        'size_mb': round(file_size / (1024 * 1024), 2)
                    })
                    total_size_freed += file_size
            except OSError:
                continue

        return Response({
            'status': 'success',
            'days_cutoff': days,
            'deleted_files_count': len(deleted_files),
            'total_size_freed_mb': round(total_size_freed / (1024 * 1024), 2),
            'deleted_files': deleted_files
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def log_analytics(request):
    """Get analytics on log patterns and errors"""
    if not check_permission(request):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    try:
        log_dir = get_log_directory()
        hours = int(request.GET.get('hours', 24))
        cutoff_time = datetime.now() - timedelta(hours=hours)

        analytics = {
            'error_counts_by_level': {'ERROR': 0, 'WARNING': 0, 'CRITICAL': 0, 'INFO': 0},
            'error_patterns': {},
            'hourly_distribution': {},
            'top_error_sources': {}
        }

        # Analyze main log files
        for log_name in ['django.log', 'django_error.log', 'celery.log']:
            log_path = os.path.join(log_dir, log_name)
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    lines = f.readlines()

                    for line in reversed(lines[-5000:]):  # Last 5000 lines
                        try:
                            # Count by level
                            for level in analytics['error_counts_by_level'].keys():
                                if f'[{level}]' in line:
                                    analytics['error_counts_by_level'][level] += 1

                                    # Extract hour for distribution
                                    if line.startswith('['):
                                        timestamp_str = line.split('] ')[1].split(' [')[0]
                                        log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                        if log_time >= cutoff_time:
                                            hour_key = log_time.strftime('%Y-%m-%d %H:00')
                                            analytics['hourly_distribution'][hour_key] = analytics['hourly_distribution'].get(hour_key, 0) + 1
                                    break
                        except (ValueError, IndexError):
                            continue

        return Response({
            'status': 'success',
            'hours_analyzed': hours,
            'analytics': analytics
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)