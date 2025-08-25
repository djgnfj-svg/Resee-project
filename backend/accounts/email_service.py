"""
통합 이메일 서비스 - 모델, 유틸리티, 백엔드 기능 통합
"""
import logging
from typing import Any, Dict, Optional

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import models
from django.template import Context, Template
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

User = get_user_model()
logger = logging.getLogger(__name__)


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


class EmailService:
    """통합 이메일 서비스 클래스"""
    
    @staticmethod
    def send_template_email(
        template_name: str,
        context: Dict[str, Any],
        subject: str,
        recipient_email: str,
        from_email: Optional[str] = None
    ) -> bool:
        """
        템플릿 기반 이메일 발송
        
        Args:
            template_name: 템플릿 파일명 (확장자 제외)
            context: 템플릿 컨텍스트
            subject: 이메일 제목
            recipient_email: 수신자 이메일
            from_email: 발신자 이메일 (기본값: DEFAULT_FROM_EMAIL)
            
        Returns:
            bool: 발송 성공 여부
        """
        try:
            # HTML 템플릿 렌더링
            html_message = render_to_string(f'emails/{template_name}.html', context)
            plain_message = strip_tags(html_message)
            
            # 발신자 이메일 설정
            if not from_email:
                from_email = settings.DEFAULT_FROM_EMAIL
                
            # 이메일 발송
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=from_email,
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            return False


@shared_task(bind=True, max_retries=3)
def send_verification_email_task(self, user_id: int):
    """
    이메일 인증 태스크 (재시도 로직 포함)
    """
    try:
        user = User.objects.get(id=user_id)
        
        # 이미 인증된 사용자는 스킵
        if user.is_email_verified:
            logger.info(f"User {user.email} already verified, skipping")
            return
            
        # 토큰 생성
        token = user.generate_email_verification_token()
        
        # 이메일 발송
        context = {
            'user': user,
            'verification_url': f"{settings.FRONTEND_URL}/verify-email?token={token}&email={user.email}",
            'company_name': getattr(settings, 'COMPANY_NAME', 'Your Company'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@yourcompany.com'),
            'expiry_hours': settings.EMAIL_VERIFICATION_TIMEOUT_DAYS * 24,
        }
        
        success = EmailService.send_template_email(
            template_name='email_verification',
            context=context,
            subject=f"[{context['company_name']}] 이메일 인증을 완료해주세요",
            recipient_email=user.email
        )
        
        if not success:
            raise Exception("Failed to send email")
            
        logger.info(f"Verification email sent to {user.email}")
        return True
        
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
        raise
        
    except Exception as exc:
        logger.error(f"Failed to send verification email (attempt {self.request.retries + 1}): {str(exc)}")
        
        # 재시도 로직
        if self.request.retries < self.max_retries:
            # 지수 백오프: 2^retry_count * 60초
            countdown = (2 ** self.request.retries) * 60
            logger.info(f"Retrying in {countdown} seconds...")
            raise self.retry(exc=exc, countdown=countdown)
        else:
            # 최대 재시도 횟수 초과시 알림 발송
            logger.critical(
                f"Max retries exceeded for user {user_id} email verification. "
                f"Manual intervention required. User email: {user.email}"
            )
            raise


# 이메일 템플릿 상수
EMAIL_TEMPLATES = {
    'verification': {
        'subject': '[{company}] 이메일 인증을 완료해주세요',
        'template': 'email_verification'
    },
    'welcome': {
        'subject': '[{company}] 환영합니다!',
        'template': 'welcome_email'
    },
    'password_reset': {
        'subject': '[{company}] 비밀번호 재설정',
        'template': 'password_reset'
    }
}