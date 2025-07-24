"""
실무용 이메일 유틸리티
"""
import logging
from typing import Optional, Dict, Any
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from celery import shared_task

logger = logging.getLogger(__name__)


class EmailService:
    """실무용 이메일 서비스 클래스"""
    
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


# 실무에서는 더 구체적인 에러 처리
@shared_task(bind=True, max_retries=3)
def send_verification_email_task(self, user_id: int):
    """
    실무용 이메일 인증 태스크 (재시도 로직 포함)
    """
    try:
        from .models import User
        
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
            # 관리자용 슬랙/이메일 알림은 실무 환경에서 설정 필요
            raise




# 실무용 이메일 템플릿 관리
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