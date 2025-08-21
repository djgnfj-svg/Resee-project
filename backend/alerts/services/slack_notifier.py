"""
Slack notification service for alert system
"""
import json
import logging
from typing import Dict, Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from django.conf import settings

logger = logging.getLogger(__name__)


class SlackNotifier:
    """
    Slack notification service using webhooks
    """
    
    def __init__(self):
        self.webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', None)
        self.default_channel = getattr(settings, 'SLACK_DEFAULT_CHANNEL', '#alerts')
        self.bot_name = getattr(settings, 'SLACK_BOT_NAME', 'Resee Alert Bot')
    
    def send_alert(self, channel: str, message: str, severity: str, rule_name: str = None) -> Dict[str, Any]:
        """
        Send alert notification to Slack
        
        Args:
            channel: Slack channel to send to (e.g., '#alerts')
            message: Alert message content
            severity: Alert severity level
            rule_name: Name of the alert rule
            
        Returns:
            Dictionary with success status and response info
        """
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return {
                'success': False,
                'error': 'Slack webhook URL not configured',
                'timestamp': self._get_timestamp()
            }
        
        try:
            # Build Slack message payload
            payload = self._build_slack_payload(channel, message, severity, rule_name)
            
            # Send to Slack
            response = self._send_webhook(payload)
            
            return {
                'success': True,
                'response': response,
                'channel': channel,
                'timestamp': self._get_timestamp()
            }
            
        except Exception as e:
            error_msg = f"Failed to send Slack notification: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'timestamp': self._get_timestamp()
            }
    
    def send_test_message(self, channel: str = None) -> Dict[str, Any]:
        """
        Send a test message to verify Slack integration
        
        Args:
            channel: Slack channel to send to
            
        Returns:
            Dictionary with success status and response info
        """
        test_channel = channel or self.default_channel
        test_message = (
            "🧪 **TEST ALERT**\n\n"
            "This is a test message from Resee Alert System.\n"
            "If you see this message, Slack integration is working correctly! ✅"
        )
        
        return self.send_alert(
            channel=test_channel,
            message=test_message,
            severity='low',
            rule_name='Test Rule'
        )
    
    def _build_slack_payload(self, channel: str, message: str, severity: str, rule_name: str = None) -> Dict[str, Any]:
        """
        Build Slack webhook payload
        """
        # Color coding for different severities
        color_map = {
            'low': '#36a64f',      # Green
            'medium': '#ff9500',   # Orange
            'high': '#ff0000',     # Red
            'critical': '#800000'  # Dark red
        }
        
        color = color_map.get(severity, '#808080')  # Default gray
        
        # Convert markdown to Slack format
        slack_message = self._convert_to_slack_format(message)
        
        # Build attachment
        attachment = {
            'color': color,
            'title': f'Alert: {rule_name}' if rule_name else 'System Alert',
            'text': slack_message,
            'footer': 'Resee Alert System',
            'ts': self._get_timestamp(),
            'mrkdwn_in': ['text']
        }
        
        payload = {
            'channel': channel,
            'username': self.bot_name,
            'icon_emoji': ':warning:',
            'attachments': [attachment]
        }
        
        return payload
    
    def _convert_to_slack_format(self, message: str) -> str:
        """
        Convert markdown-style message to Slack format
        """
        # Convert **bold** to *bold*
        slack_message = message.replace('**', '*')
        
        return slack_message
    
    def _send_webhook(self, payload: Dict[str, Any]) -> str:
        """
        Send webhook request to Slack
        """
        data = json.dumps(payload).encode('utf-8')
        
        request = Request(
            self.webhook_url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Resee Alert System'
            }
        )
        
        try:
            with urlopen(request, timeout=10) as response:
                response_data = response.read().decode('utf-8')
                
                if response.status == 200:
                    logger.debug("Slack webhook sent successfully")
                    return response_data
                else:
                    raise HTTPError(
                        response.url, response.status, 
                        f"Slack API returned status {response.status}", 
                        response.headers, None
                    )
                    
        except HTTPError as e:
            logger.error(f"HTTP error sending Slack webhook: {e}")
            raise
        except URLError as e:
            logger.error(f"URL error sending Slack webhook: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending Slack webhook: {e}")
            raise
    
    def _get_timestamp(self) -> int:
        """Get current timestamp"""
        from django.utils import timezone
        return int(timezone.now().timestamp())
    
    @property
    def is_configured(self) -> bool:
        """Check if Slack integration is properly configured"""
        return bool(self.webhook_url)