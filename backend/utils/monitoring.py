"""
Monitoring utilities for Resee
Tracks system metrics and sends alerts when thresholds are exceeded
"""
import time
import logging
from typing import Dict, Any, Optional
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from utils.slack_notifications import slack_notifier

logger = logging.getLogger(__name__)


class MetricsMonitor:
    """
    Monitor system metrics and send alerts
    """

    # Alert thresholds
    ERROR_RATE_THRESHOLD = 5.0  # 5%
    PAYMENT_FAILURE_THRESHOLD = 10  # 10 failures per hour
    CELERY_QUEUE_THRESHOLD = 100  # 100 tasks in queue
    API_RESPONSE_THRESHOLD = 2.0  # 2 seconds (p95)

    # Alert throttling (prevent spam)
    ALERT_THROTTLE_SECONDS = 600  # 10 minutes

    def __init__(self):
        self.cache_prefix = 'monitoring:'

    def _get_cache_key(self, metric: str) -> str:
        """Generate cache key for metric"""
        return f"{self.cache_prefix}{metric}"

    def _should_send_alert(self, alert_key: str) -> bool:
        """
        Check if alert should be sent (throttling)

        Args:
            alert_key: Unique identifier for the alert

        Returns:
            bool: True if alert should be sent
        """
        cache_key = self._get_cache_key(f"alert:{alert_key}")
        if cache.get(cache_key):
            return False  # Alert was sent recently

        # Set cache to throttle future alerts
        cache.set(cache_key, True, self.ALERT_THROTTLE_SECONDS)
        return True

    def track_api_request(self, endpoint: str, response_time: float, status_code: int):
        """
        Track API request metrics

        Args:
            endpoint: API endpoint path
            response_time: Response time in seconds
            status_code: HTTP status code
        """
        try:
            # Store metrics in cache (sliding window)
            metrics_key = self._get_cache_key(f"api:{endpoint}:metrics")
            metrics = cache.get(metrics_key, [])

            # Add current request
            metrics.append({
                'timestamp': time.time(),
                'response_time': response_time,
                'status_code': status_code,
                'is_error': status_code >= 400
            })

            # Keep only last hour of data
            one_hour_ago = time.time() - 3600
            metrics = [m for m in metrics if m['timestamp'] > one_hour_ago]

            # Store updated metrics
            cache.set(metrics_key, metrics, 3600)

            # Check thresholds
            self._check_api_metrics(endpoint, metrics)

        except Exception as e:
            logger.error(f"Error tracking API request: {e}")

    def _check_api_metrics(self, endpoint: str, metrics: list):
        """
        Check API metrics and send alerts if thresholds exceeded

        Args:
            endpoint: API endpoint path
            metrics: List of request metrics
        """
        if not metrics:
            return

        # Calculate error rate
        total_requests = len(metrics)
        error_requests = sum(1 for m in metrics if m['is_error'])
        error_rate = (error_requests / total_requests) * 100

        # Alert if error rate exceeds threshold
        if error_rate > self.ERROR_RATE_THRESHOLD:
            alert_key = f"error_rate:{endpoint}"
            if self._should_send_alert(alert_key):
                slack_notifier.send_error_rate_alert(
                    error_rate=error_rate,
                    threshold=self.ERROR_RATE_THRESHOLD,
                    time_window='1 hour'
                )

        # Calculate p95 response time
        response_times = sorted([m['response_time'] for m in metrics])
        p95_index = int(len(response_times) * 0.95)
        p95_response_time = response_times[p95_index] if response_times else 0

        # Alert if p95 exceeds threshold
        if p95_response_time > self.API_RESPONSE_THRESHOLD:
            alert_key = f"api_performance:{endpoint}"
            if self._should_send_alert(alert_key):
                slack_notifier.send_api_performance_alert(
                    endpoint=endpoint,
                    response_time=p95_response_time,
                    threshold=self.API_RESPONSE_THRESHOLD
                )

    def track_payment_failure(self, reason: str, amount: Optional[float] = None):
        """
        Track payment failure

        Args:
            reason: Failure reason
            amount: Payment amount (optional)
        """
        try:
            # Store failure in cache
            failures_key = self._get_cache_key("payment:failures")
            failures = cache.get(failures_key, [])

            failures.append({
                'timestamp': time.time(),
                'reason': reason,
                'amount': amount
            })

            # Keep only last hour of data
            one_hour_ago = time.time() - 3600
            failures = [f for f in failures if f['timestamp'] > one_hour_ago]

            # Store updated failures
            cache.set(failures_key, failures, 3600)

            # Check threshold
            if len(failures) >= self.PAYMENT_FAILURE_THRESHOLD:
                alert_key = "payment_failures"
                if self._should_send_alert(alert_key):
                    slack_notifier.send_payment_alert(
                        alert_type='failure_spike',
                        count=len(failures),
                        details={
                            'time_window': '1 hour',
                            'threshold': self.PAYMENT_FAILURE_THRESHOLD
                        }
                    )

        except Exception as e:
            logger.error(f"Error tracking payment failure: {e}")

    def check_celery_queue(self, queue_name: str, queue_length: int):
        """
        Check Celery queue length and alert if threshold exceeded

        Args:
            queue_name: Name of the queue
            queue_length: Current queue length
        """
        try:
            if queue_length >= self.CELERY_QUEUE_THRESHOLD:
                alert_key = f"celery_queue:{queue_name}"
                if self._should_send_alert(alert_key):
                    slack_notifier.send_celery_alert(
                        queue_name=queue_name,
                        queue_length=queue_length,
                        threshold=self.CELERY_QUEUE_THRESHOLD
                    )
        except Exception as e:
            logger.error(f"Error checking Celery queue: {e}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary of current metrics

        Returns:
            Dict containing metrics summary
        """
        summary = {
            'timestamp': time.time(),
            'api': {},
            'payments': {},
            'celery': {}
        }

        try:
            # Get payment failures
            failures_key = self._get_cache_key("payment:failures")
            failures = cache.get(failures_key, [])
            summary['payments']['failures_last_hour'] = len(failures)

            # Get API metrics (example for a few key endpoints)
            key_endpoints = ['/api/review/today/', '/api/content/', '/api/accounts/login/']
            for endpoint in key_endpoints:
                metrics_key = self._get_cache_key(f"api:{endpoint}:metrics")
                metrics = cache.get(metrics_key, [])
                if metrics:
                    error_count = sum(1 for m in metrics if m['is_error'])
                    error_rate = (error_count / len(metrics)) * 100 if metrics else 0
                    avg_response_time = sum(m['response_time'] for m in metrics) / len(metrics)

                    summary['api'][endpoint] = {
                        'total_requests': len(metrics),
                        'error_rate': round(error_rate, 2),
                        'avg_response_time': round(avg_response_time, 3)
                    }

        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")

        return summary


# Global instance
metrics_monitor = MetricsMonitor()


# Convenience functions
def track_api_request(endpoint: str, response_time: float, status_code: int):
    """Track API request (convenience function)"""
    metrics_monitor.track_api_request(endpoint, response_time, status_code)


def track_payment_failure(reason: str, amount: Optional[float] = None):
    """Track payment failure (convenience function)"""
    metrics_monitor.track_payment_failure(reason, amount)


def check_celery_queue(queue_name: str, queue_length: int):
    """Check Celery queue (convenience function)"""
    metrics_monitor.check_celery_queue(queue_name, queue_length)


def get_metrics_summary() -> Dict[str, Any]:
    """Get metrics summary (convenience function)"""
    return metrics_monitor.get_metrics_summary()
