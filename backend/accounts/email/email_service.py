"""
통합 이메일 서비스 - 모델, 유틸리티, 백엔드 기능 통합
"""
import logging
from typing import Any, Dict, Optional

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


    def send_verification_email(self, user_id: int):
        """
        이메일 인증 전송 (동기 방식)
        """
        try:
            user = User.objects.get(id=user_id)
            
            # 이미 인증된 사용자는 스킵
            if user.is_email_verified:
                logger.info(f"User {user.email} already verified, skipping")
                return True
                
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
            
            success = self.send_template_email(
                template_name='email_verification',
                context=context,
                subject=f"[{context['company_name']}] 이메일 인증을 완료해주세요",
                recipient_email=user.email
            )
            
            if success:
                logger.info(f"Verification email sent to {user.email}")
            else:
                logger.error(f"Failed to send verification email to {user.email}")
                
            return success
            
        except User.DoesNotExist:
            logger.error(f"User with id {user_id} does not exist")
            return False
            
        except Exception as exc:
            logger.error(f"Failed to send verification email: {str(exc)}")
            return False

    def send_welcome_email(self, user_id: int):
        """
        웰컴 이메일 전송 (동기 방식)
        """
        try:
            user = User.objects.get(id=user_id)
            
            context = {
                'user': user,
                'company_name': getattr(settings, 'COMPANY_NAME', 'Your Company'),
                'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@yourcompany.com'),
            }
            
            success = self.send_template_email(
                template_name='welcome_email',
                context=context,
                subject=f"[{context['company_name']}] 환영합니다!",
                recipient_email=user.email
            )
            
            if success:
                logger.info(f"Welcome email sent to {user.email}")
            else:
                logger.error(f"Failed to send welcome email to {user.email}")
                
            return success
            
        except User.DoesNotExist:
            logger.error(f"User with id {user_id} does not exist")
            return False
            
        except Exception as exc:
            logger.error(f"Failed to send welcome email: {str(exc)}")
            return False