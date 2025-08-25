"""
Email notification service for alert system
"""
import logging
from typing import Dict, Any, List
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

logger = logging.getLogger(__name__)


class EmailNotifier:
    """
    Email notification service for alerts
    """
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@resee.com')
        self.admin_email = getattr(settings, 'ADMINS', [])
    
    def send_alert(self, recipients: List[str], subject: str, message: str, rule=None) -> Dict[str, Any]:
        """
        Send alert notification via email
        
        Args:
            recipients: List of email addresses
            subject: Email subject
            message: Alert message content
            rule: AlertRule instance (optional)
            
        Returns:
            Dictionary with success status and response info
        """
        if not recipients:
            logger.warning("No email recipients configured")
            return {
                'success': False,
                'error': 'No email recipients configured',
                'timestamp': self._get_timestamp()
            }
        
        try:
            # Build HTML and text versions of the email
            html_content = self._build_html_content(message, rule)
            text_content = self._build_text_content(message)
            
            # Send email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=recipients
            )
            msg.attach_alternative(html_content, "text/html")
            
            sent_count = msg.send()
            
            return {
                'success': sent_count > 0,
                'sent_count': sent_count,
                'recipients': recipients,
                'timestamp': self._get_timestamp()
            }
            
        except Exception as e:
            error_msg = f"Failed to send email notification: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'timestamp': self._get_timestamp()
            }
    
    def send_test_email(self, recipients: List[str] = None) -> Dict[str, Any]:
        """
        Send a test email to verify email integration
        
        Args:
            recipients: List of email addresses (defaults to admin emails)
            
        Returns:
            Dictionary with success status and response info
        """
        test_recipients = recipients or [email for name, email in self.admin_email]
        
        if not test_recipients:
            return {
                'success': False,
                'error': 'No test email recipients configured',
                'timestamp': self._get_timestamp()
            }
        
        test_subject = "[TEST] Resee Alert System - Email Integration Test"
        test_message = (
            "🧪 **TEST ALERT**\n\n"
            "This is a test email from Resee Alert System.\n"
            "If you receive this email, the integration is working correctly! ✅\n\n"
            f"Test sent at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        
        return self.send_alert(
            recipients=test_recipients,
            subject=test_subject,
            message=test_message
        )
    
    def send_daily_summary(self, recipients: List[str], summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send daily alert summary email
        
        Args:
            recipients: List of email addresses
            summary_data: Dictionary with summary statistics
            
        Returns:
            Dictionary with success status and response info
        """
        try:
            # Build summary email content
            subject = f"Daily Alert Summary - {timezone.now().strftime('%Y-%m-%d')}"
            
            # Use template if available, otherwise build simple text
            html_content = self._build_summary_html(summary_data)
            text_content = self._build_summary_text(summary_data)
            
            # Send email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=recipients
            )
            msg.attach_alternative(html_content, "text/html")
            
            sent_count = msg.send()
            
            return {
                'success': sent_count > 0,
                'sent_count': sent_count,
                'recipients': recipients,
                'timestamp': self._get_timestamp()
            }
            
        except Exception as e:
            error_msg = f"Failed to send daily summary email: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'timestamp': self._get_timestamp()
            }
    
    def _build_html_content(self, message: str, rule=None) -> str:
        """
        Build HTML version of alert email
        """
        # Convert markdown-style formatting to HTML
        html_message = message.replace('**', '<strong>').replace('**', '</strong>')
        html_message = html_message.replace('\n', '<br>')
        
        # Build full HTML email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .alert-content {{ background-color: #ffffff; border: 1px solid #dee2e6; padding: 20px; border-radius: 5px; }}
                .severity-critical {{ border-left: 5px solid #dc3545; }}
                .severity-high {{ border-left: 5px solid #fd7e14; }}
                .severity-medium {{ border-left: 5px solid #ffc107; }}
                .severity-low {{ border-left: 5px solid #28a745; }}
                .footer {{ margin-top: 20px; padding: 10px; font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🚨 Resee Alert Notification</h2>
            </div>
            <div class="alert-content {self._get_severity_class(rule)}">
                {html_message}
            </div>
            <div class="footer">
                <p>This alert was generated by Resee Alert System.</p>
                <p>If you believe this is an error, please contact your system administrator.</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _build_text_content(self, message: str) -> str:
        """
        Build plain text version of alert email
        """
        # Remove markdown formatting for plain text
        text_content = message.replace('**', '')
        
        # Add header and footer
        text_content = f"""
🚨 RESEE ALERT NOTIFICATION

{text_content}

---
This alert was generated by Resee Alert System.
If you believe this is an error, please contact your system administrator.
        """.strip()
        
        return text_content
    
    def _build_summary_html(self, summary_data: Dict[str, Any]) -> str:
        """
        Build HTML version of daily summary email
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .summary-section {{ margin: 15px 0; }}
                .stats-table {{ width: 100%; border-collapse: collapse; }}
                .stats-table th, .stats-table td {{ padding: 8px; border: 1px solid #dee2e6; text-align: left; }}
                .stats-table th {{ background-color: #e9ecef; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📊 Daily Alert Summary</h2>
                <p>Date: {timezone.now().strftime('%Y-%m-%d')}</p>
            </div>
            
            <div class="summary-section">
                <h3>Alert Statistics</h3>
                <table class="stats-table">
                    <tr><th>Metric</th><th>Count</th></tr>
                    <tr><td>Total Alerts</td><td>{summary_data.get('total_alerts', 0)}</td></tr>
                    <tr><td>Critical Alerts</td><td>{summary_data.get('critical_alerts', 0)}</td></tr>
                    <tr><td>High Priority Alerts</td><td>{summary_data.get('high_alerts', 0)}</td></tr>
                    <tr><td>Resolved Alerts</td><td>{summary_data.get('resolved_alerts', 0)}</td></tr>
                </table>
            </div>
            
            <div class="summary-section">
                <h3>System Health</h3>
                <p>Average API Response Time: {summary_data.get('avg_response_time', 'N/A')} ms</p>
                <p>Error Rate: {summary_data.get('error_rate', 'N/A')}%</p>
                <p>System Uptime: {summary_data.get('uptime', 'N/A')}</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _build_summary_text(self, summary_data: Dict[str, Any]) -> str:
        """
        Build plain text version of daily summary email
        """
        text_content = f"""
📊 DAILY ALERT SUMMARY

Date: {timezone.now().strftime('%Y-%m-%d')}

Alert Statistics:
- Total Alerts: {summary_data.get('total_alerts', 0)}
- Critical Alerts: {summary_data.get('critical_alerts', 0)}
- High Priority Alerts: {summary_data.get('high_alerts', 0)}
- Resolved Alerts: {summary_data.get('resolved_alerts', 0)}

System Health:
- Average API Response Time: {summary_data.get('avg_response_time', 'N/A')} ms
- Error Rate: {summary_data.get('error_rate', 'N/A')}%
- System Uptime: {summary_data.get('uptime', 'N/A')}

---
Generated by Resee Alert System
        """.strip()
        
        return text_content
    
    def _get_severity_class(self, rule) -> str:
        """Get CSS class for severity level"""
        if not rule:
            return ''
        
        severity_classes = {
            'critical': 'severity-critical',
            'high': 'severity-high',
            'medium': 'severity-medium',
            'low': 'severity-low'
        }
        
        return severity_classes.get(rule.severity, '')
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string"""
        return timezone.now().isoformat()
    
    @property
    def is_configured(self) -> bool:
        """Check if email integration is properly configured"""
        # Check if email backend is configured
        email_backend = getattr(settings, 'EMAIL_BACKEND', None)
        return bool(email_backend and email_backend != 'django.core.mail.backends.dummy.EmailBackend')