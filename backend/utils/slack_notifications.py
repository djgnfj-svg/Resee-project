"""
Slack notification utility for Resee
Sends alerts to Slack for critical system events
"""
import logging
from typing import Any, Dict, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class SlackNotifier:
    """
    Slack notification service for system alerts
    """

    def __init__(self):
        self.webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', None)
        self.default_channel = getattr(settings, 'SLACK_DEFAULT_CHANNEL', '#alerts')
        self.bot_name = getattr(settings, 'SLACK_BOT_NAME', 'Resee Alert Bot')
        self.enabled = bool(self.webhook_url)

    def send_alert(
        self,
        message: str,
        level: str = 'error',
        title: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        channel: Optional[str] = None
    ) -> bool:
        """
        Send an alert to Slack

        Args:
            message: Main alert message
            level: Alert level ('error', 'warning', 'info', 'success')
            title: Optional title for the alert
            fields: Optional dictionary of additional fields
            channel: Optional channel override

        Returns:
            bool: True if alert was sent successfully
        """
        if not self.enabled:
            logger.debug("Slack notifications are disabled (no webhook URL configured)")
            return False

        try:
            # Choose emoji and color based on level
            emoji_map = {
                'error': '🔴',
                'warning': '⚠️',
                'info': 'ℹ️',
                'success': '✅'
            }
            color_map = {
                'error': '#DC2626',    # red-600
                'warning': '#F59E0B',  # amber-500
                'info': '#3B82F6',     # blue-500
                'success': '#10B981'   # green-500
            }

            emoji = emoji_map.get(level, '📢')
            color = color_map.get(level, '#6B7280')

            # Build Slack message
            payload = {
                'username': self.bot_name,
                'channel': channel or self.default_channel,
                'text': f"{emoji} {title or 'System Alert'}",
                'attachments': [{
                    'color': color,
                    'text': message,
                    'footer': 'Resee Monitoring',
                    'footer_icon': 'https://platform.slack-edge.com/img/default_application_icon.png',
                    'ts': self._get_timestamp()
                }]
            }

            # Add fields if provided
            if fields:
                payload['attachments'][0]['fields'] = [
                    {'title': key, 'value': str(value), 'short': True}
                    for key, value in fields.items()
                ]

            # Send to Slack
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()

            logger.info(f"Slack alert sent successfully: {title or message[:50]}")
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Slack alert: {e}")
            return False

    def send_error_alert(self, error: Exception, context: Optional[str] = None) -> bool:
        """
        Send an error alert

        Args:
            error: Exception object
            context: Optional context information

        Returns:
            bool: True if alert was sent successfully
        """
        message = f"**Error Type:** {type(error).__name__}\n"
        message += f"**Message:** {str(error)}\n"
        if context:
            message += f"**Context:** {context}\n"

        return self.send_alert(
            message=message,
            level='error',
            title='Application Error Detected'
        )

    def send_health_alert(
        self,
        service: str,
        status: str,
        details: Optional[str] = None
    ) -> bool:
        """
        Send a health check alert

        Args:
            service: Service name (e.g., 'database', 'celery', 'api')
            status: Status ('down', 'degraded', 'recovered')
            details: Optional details about the issue

        Returns:
            bool: True if alert was sent successfully
        """
        level_map = {
            'down': 'error',
            'degraded': 'warning',
            'recovered': 'success'
        }
        level = level_map.get(status, 'warning')

        message = f"**Service:** {service}\n"
        message += f"**Status:** {status.upper()}\n"
        if details:
            message += f"**Details:** {details}\n"

        return self.send_alert(
            message=message,
            level=level,
            title=f'Health Check Alert: {service}'
        )

    def send_payment_alert(
        self,
        alert_type: str,
        count: int,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a payment-related alert

        Args:
            alert_type: Type of alert ('failure_spike', 'refund_spike', etc.)
            count: Number of incidents
            details: Optional additional details

        Returns:
            bool: True if alert was sent successfully
        """
        message = f"**Alert Type:** {alert_type}\n"
        message += f"**Incident Count:** {count}\n"

        fields = details or {}

        return self.send_alert(
            message=message,
            level='error',
            title='Payment System Alert',
            fields=fields
        )

    def send_celery_alert(
        self,
        queue_name: str,
        queue_length: int,
        threshold: int
    ) -> bool:
        """
        Send a Celery queue alert

        Args:
            queue_name: Name of the queue
            queue_length: Current queue length
            threshold: Threshold that was exceeded

        Returns:
            bool: True if alert was sent successfully
        """
        message = f"**Queue:** {queue_name}\n"
        message += f"**Current Length:** {queue_length}\n"
        message += f"**Threshold:** {threshold}\n"

        return self.send_alert(
            message=message,
            level='warning',
            title='Celery Queue Alert'
        )

    def send_api_performance_alert(
        self,
        endpoint: str,
        response_time: float,
        threshold: float
    ) -> bool:
        """
        Send an API performance alert

        Args:
            endpoint: API endpoint
            response_time: Average response time (seconds)
            threshold: Threshold that was exceeded (seconds)

        Returns:
            bool: True if alert was sent successfully
        """
        message = f"**Endpoint:** {endpoint}\n"
        message += f"**Response Time:** {response_time:.2f}s\n"
        message += f"**Threshold:** {threshold:.2f}s\n"

        return self.send_alert(
            message=message,
            level='warning',
            title='API Performance Alert'
        )

    def send_error_rate_alert(
        self,
        error_rate: float,
        threshold: float,
        time_window: str = '1 hour'
    ) -> bool:
        """
        Send an error rate alert

        Args:
            error_rate: Current error rate (percentage)
            threshold: Threshold that was exceeded (percentage)
            time_window: Time window for the error rate

        Returns:
            bool: True if alert was sent successfully
        """
        message = f"**Error Rate:** {error_rate:.2f}%\n"
        message += f"**Threshold:** {threshold:.2f}%\n"
        message += f"**Time Window:** {time_window}\n"

        return self.send_alert(
            message=message,
            level='error',
            title='High Error Rate Detected'
        )

    @staticmethod
    def _get_timestamp() -> int:
        """Get current Unix timestamp"""
        import time
        return int(time.time())


# Global instance
slack_notifier = SlackNotifier()


# Convenience functions
def send_slack_alert(message: str, level: str = 'error', **kwargs) -> bool:
    """Send a Slack alert (convenience function)"""
    return slack_notifier.send_alert(message, level, **kwargs)


def send_error_alert(error: Exception, context: Optional[str] = None) -> bool:
    """Send an error alert (convenience function)"""
    return slack_notifier.send_error_alert(error, context)


def send_health_alert(service: str, status: str, details: Optional[str] = None) -> bool:
    """Send a health alert (convenience function)"""
    return slack_notifier.send_health_alert(service, status, details)
