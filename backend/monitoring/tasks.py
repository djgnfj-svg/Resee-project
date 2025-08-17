"""
Celery tasks for monitoring data collection and processing
"""
import logging

import psutil
from celery import shared_task
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from .models import APIMetrics, SystemHealth
from .utils import (batch_insert_metrics, clean_old_metrics, get_cache_stats,
                    get_database_stats)

logger = logging.getLogger('monitoring')


@shared_task(name='monitoring.collect_system_health')
def collect_system_health():
    """
    Collect system health metrics and store in database
    """
    try:
        # Get system resource usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get cache stats
        cache_stats = get_cache_stats()
        
        # Get database stats
        db_stats = get_database_stats()
        
        # Calculate API metrics for the last minute
        one_minute_ago = timezone.now() - timezone.timedelta(minutes=1)
        recent_api_metrics = APIMetrics.objects.filter(timestamp__gte=one_minute_ago)
        
        api_requests_count = recent_api_metrics.count()
        api_error_count = recent_api_metrics.filter(status_code__gte=400).count()
        api_avg_response_time = 0
        
        if api_requests_count > 0:
            total_response_time = sum(
                metric.response_time_ms for metric in recent_api_metrics
            )
            api_avg_response_time = total_response_time / api_requests_count
            api_error_rate = (api_error_count / api_requests_count) * 100
        else:
            api_error_rate = 0
        
        # Check service status
        redis_status = cache_stats.get('uptime_seconds', 0) > 0
        postgres_status = db_stats.get('status') == 'healthy'
        
        # Check Celery workers
        celery_workers_active = 0
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            active_workers = inspect.active()
            celery_workers_active = len(active_workers) if active_workers else 0
        except Exception as e:
            logger.warning(f"Failed to check Celery workers: {e}")
        
        # Create system health record
        system_health = SystemHealth.objects.create(
            cpu_usage_percent=cpu_percent,
            memory_usage_percent=memory.percent,
            disk_usage_percent=(disk.used / disk.total) * 100,
            db_connection_count=db_stats.get('active_connections', 0),
            db_query_avg_time_ms=db_stats.get('avg_query_time_ms', 0),
            cache_hit_rate_percent=cache_stats.get('hit_rate_percent', 0),
            cache_memory_usage_mb=cache_stats.get('memory_usage_mb', 0),
            celery_workers_active=celery_workers_active,
            redis_status=redis_status,
            postgres_status=postgres_status,
            api_requests_per_minute=api_requests_count,
            api_error_rate_percent=api_error_rate,
            api_avg_response_time_ms=api_avg_response_time,
        )
        
        logger.info(f"Collected system health metrics: {system_health.id}")
        
        # Log warnings for high resource usage
        if cpu_percent > 80:
            logger.warning(f"High CPU usage detected: {cpu_percent}%")
        
        if memory.percent > 80:
            logger.warning(f"High memory usage detected: {memory.percent}%")
        
        if api_error_rate > 10:
            logger.warning(f"High API error rate detected: {api_error_rate}%")
        
        return {
            'success': True,
            'health_id': system_health.id,
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'api_requests_per_minute': api_requests_count,
        }
        
    except Exception as e:
        logger.error(f"Failed to collect system health: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


@shared_task(name='monitoring.process_batched_metrics')
def process_batched_metrics():
    """
    Process batched API metrics from cache and insert into database
    """
    try:
        processed_batches = 0
        total_metrics = 0
        
        # Get all cache keys for metric batches
        cache_pattern = "api_metrics_batch_*"
        
        # Since we can't pattern match in Django cache, we'll check recent hours
        current_time = timezone.now()
        
        for hours_back in range(2):  # Check last 2 hours
            check_time = current_time - timezone.timedelta(hours=hours_back)
            cache_key = f"api_metrics_batch_{check_time.strftime('%Y%m%d_%H')}"
            
            cached_metrics = cache.get(cache_key)
            if cached_metrics:
                try:
                    # Use batch_insert_metrics utility
                    batch_insert_metrics(APIMetrics, cached_metrics)
                    
                    # Clear the cache
                    cache.delete(cache_key)
                    
                    processed_batches += 1
                    total_metrics += len(cached_metrics)
                    
                    logger.info(f"Processed batch {cache_key}: {len(cached_metrics)} metrics")
                    
                except Exception as e:
                    logger.error(f"Failed to process batch {cache_key}: {e}")
        
        return {
            'success': True,
            'processed_batches': processed_batches,
            'total_metrics': total_metrics,
        }
        
    except Exception as e:
        logger.error(f"Failed to process batched metrics: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


@shared_task(name='monitoring.cleanup_old_monitoring_data')
def cleanup_old_monitoring_data(days_to_keep=30):
    """
    Clean up old monitoring data to prevent database bloat
    """
    try:
        deleted_count = clean_old_metrics(days_to_keep)
        
        logger.info(f"Cleaned up {deleted_count} old monitoring records")
        
        return {
            'success': True,
            'deleted_count': deleted_count,
            'days_kept': days_to_keep,
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup old monitoring data: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


@shared_task(name='monitoring.generate_performance_report')
def generate_performance_report():
    """
    Generate daily performance report and detect anomalies
    """
    try:
        from .utils import (calculate_performance_score,
                            get_performance_insights)

        # Get insights for the last 24 hours
        insights = get_performance_insights(24)
        
        # Calculate performance score
        latest_health = SystemHealth.objects.order_by('-timestamp').first()
        
        metrics = {}
        if latest_health:
            metrics = {
                'avg_response_time_ms': insights['api_insights'].get('avg_response_time_ms', 0),
                'error_rate_percent': latest_health.api_error_rate_percent,
                'avg_query_time_ms': latest_health.db_query_avg_time_ms,
                'cache_hit_rate_percent': latest_health.cache_hit_rate_percent,
            }
        
        performance_score = calculate_performance_score(metrics)
        
        # Log performance summary
        logger.info(
            f"Daily performance report generated",
            extra={
                'event_type': 'performance_report',
                'performance_score': performance_score,
                'insights': insights,
                'metrics': metrics,
            }
        )
        
        # Alert if performance is poor
        if performance_score < 60:
            logger.warning(
                f"Poor system performance detected: Score {performance_score}/100",
                extra={
                    'event_type': 'performance_alert',
                    'performance_score': performance_score,
                    'recommendations': insights.get('recommendations', []),
                }
            )
        
        return {
            'success': True,
            'performance_score': performance_score,
            'insights': insights,
        }
        
    except Exception as e:
        logger.error(f"Failed to generate performance report: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


@shared_task(name='monitoring.alert_on_errors')
def alert_on_errors():
    """
    Check for critical errors and send alerts
    """
    try:
        from .models import ErrorLog

        # Check for critical errors in the last hour
        one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
        critical_errors = ErrorLog.objects.filter(
            timestamp__gte=one_hour_ago,
            level='CRITICAL',
            resolved=False
        )
        
        if critical_errors.exists():
            error_count = critical_errors.count()
            
            # Log alert
            logger.critical(
                f"Critical errors detected: {error_count} unresolved errors in the last hour",
                extra={
                    'event_type': 'critical_error_alert',
                    'error_count': error_count,
                    'errors': [
                        {
                            'exception_type': error.exception_type,
                            'endpoint': error.endpoint,
                            'message': error.message[:100],
                            'timestamp': error.timestamp.isoformat(),
                        }
                        for error in critical_errors[:5]  # Limit to 5 examples
                    ]
                }
            )
            
            # Here you could integrate with external alerting services
            # like PagerDuty, Slack, email notifications, etc.
            
            return {
                'success': True,
                'alerts_sent': True,
                'critical_error_count': error_count,
            }
        
        return {
            'success': True,
            'alerts_sent': False,
            'critical_error_count': 0,
        }
        
    except Exception as e:
        logger.error(f"Failed to check for critical errors: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}