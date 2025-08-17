"""
Email-related models for tracking and management
"""
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class EmailLog(models.Model):
    """
    Log of all emails sent by the system
    Useful for debugging and audit trails
    """
    
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('sent', '발송완료'),
        ('failed', '발송실패'),
        ('bounced', '반송됨'),
        ('opened', '열람됨'),
    ]
    
    # Email details
    to_email = models.EmailField(db_index=True)
    from_email = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    html_body = models.TextField(blank=True, null=True)
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Related user (if applicable)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_logs'
    )
    
    # Metadata
    sent_at = models.DateTimeField(default=timezone.now, db_index=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    failed_reason = models.TextField(blank=True, null=True)
    
    # Email provider info
    provider = models.CharField(
        max_length=50,
        default='smtp',
        help_text='Email provider used (smtp, ses, sendgrid, etc.)'
    )
    message_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Provider message ID for tracking'
    )
    
    class Meta:
        db_table = 'accounts_email_log'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['-sent_at', 'status']),
            models.Index(fields=['to_email', '-sent_at']),
        ]
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'
    
    def __str__(self):
        return f"{self.subject} to {self.to_email} ({self.status})"
    
    def mark_as_opened(self):
        """Mark email as opened"""
        if not self.opened_at:
            self.opened_at = timezone.now()
            self.status = 'opened'
            self.save(update_fields=['opened_at', 'status'])
    
    def mark_as_failed(self, reason):
        """Mark email as failed with reason"""
        self.status = 'failed'
        self.failed_reason = reason
        self.save(update_fields=['status', 'failed_reason'])


class EmailTemplate(models.Model):
    """
    Reusable email templates
    """
    
    TEMPLATE_TYPES = [
        ('verification', '이메일 인증'),
        ('welcome', '환영 메일'),
        ('password_reset', '비밀번호 재설정'),
        ('review_reminder', '복습 알림'),
        ('subscription', '구독 관련'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    template_type = models.CharField(
        max_length=50,
        choices=TEMPLATE_TYPES,
        db_index=True
    )
    subject = models.CharField(max_length=255)
    body_template = models.TextField(
        help_text='Plain text template. Use {{ variable }} for placeholders'
    )
    html_template = models.TextField(
        blank=True,
        null=True,
        help_text='HTML template. Use {{ variable }} for placeholders'
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts_email_template'
        ordering = ['template_type', 'name']
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
    
    def render(self, context):
        """
        Render template with context variables
        """
        from django.template import Context, Template

        # Render subject
        subject_template = Template(self.subject)
        subject = subject_template.render(Context(context))
        
        # Render body
        body_template = Template(self.body_template)
        body = body_template.render(Context(context))
        
        # Render HTML if available
        html = None
        if self.html_template:
            html_template = Template(self.html_template)
            html = html_template.render(Context(context))
        
        return {
            'subject': subject,
            'body': body,
            'html': html
        }