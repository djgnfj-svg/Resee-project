"""
Custom email backends for development and testing
"""
import logging

from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.console import \
    EmailBackend as ConsoleEmailBackend

logger = logging.getLogger(__name__)


class DevelopmentEmailBackend(ConsoleEmailBackend):
    """
    Development email backend that prints to console and logs
    Useful for local development without actual email sending
    """
    
    def send_messages(self, email_messages):
        """Send email messages with enhanced logging"""
        if not email_messages:
            return 0
            
        num_sent = 0
        for message in email_messages:
            # Log email details
            logger.info("=" * 60)
            logger.info("📧 EMAIL NOTIFICATION")
            logger.info("=" * 60)
            logger.info(f"To: {', '.join(message.to)}")
            logger.info(f"From: {message.from_email}")
            logger.info(f"Subject: {message.subject}")
            logger.info("-" * 60)
            
            # Extract verification link if present
            if "verify-email" in message.body:
                import re
                link_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                links = re.findall(link_pattern, message.body)
                if links:
                    logger.info("🔗 VERIFICATION LINK:")
                    for link in links:
                        if "verify-email" in link:
                            logger.info(f"   {link}")
                            logger.info("")
                            logger.info("💡 TIP: Copy this link to browser to verify email")
            
            logger.info("-" * 60)
            logger.info("Message Body (first 500 chars):")
            logger.info(message.body[:500])
            logger.info("=" * 60)
            
            num_sent += 1
            
        # Also print to console for visibility
        super().send_messages(email_messages)
        
        return num_sent


class DatabaseEmailBackend(BaseEmailBackend):
    """
    Database email backend that stores emails in database
    Useful for testing and reviewing sent emails
    """
    
    def send_messages(self, email_messages):
        """Store email messages in database"""
        if not email_messages:
            return 0
            
        from django.utils import timezone

        from accounts.models import \
            EmailLog  # You'll need to create this model
        
        num_sent = 0
        for message in email_messages:
            try:
                EmailLog.objects.create(
                    to_email=', '.join(message.to),
                    from_email=message.from_email,
                    subject=message.subject,
                    body=message.body,
                    html_body=message.alternatives[0][0] if message.alternatives else '',
                    sent_at=timezone.now(),
                    status='sent'
                )
                num_sent += 1
                
                logger.info(f"Email stored in database: {message.subject} to {message.to}")
                
            except Exception as e:
                logger.error(f"Failed to store email in database: {e}")
                
        return num_sent


class MockSMTPBackend(BaseEmailBackend):
    """
    Mock SMTP backend that simulates email sending
    Returns success without actually sending emails
    """
    
    def send_messages(self, email_messages):
        """Simulate sending emails"""
        if not email_messages:
            return 0
            
        import random
        import time
        
        num_sent = 0
        for message in email_messages:
            # Simulate network delay
            time.sleep(random.uniform(0.1, 0.3))
            
            logger.info(f"[MOCK] Email sent: {message.subject} to {', '.join(message.to)}")
            
            # Simulate occasional failures for testing
            if random.random() > 0.95:  # 5% failure rate
                logger.warning(f"[MOCK] Simulated failure for email to {message.to}")
                continue
                
            num_sent += 1
            
        return num_sent