import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


@shared_task
def send_verification_email(user_id):
    """Send email verification to user"""
    try:
        from .models import User
        user = User.objects.get(id=user_id)
        
        if user.is_email_verified:
            logger.info(f"User {user.email} is already verified")
            return
        
        # Generate verification token
        token = user.generate_email_verification_token()
        
        # Create verification URL
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}&email={user.email}"
        
        # Render email template
        context = {
            'user': user,
            'verification_url': verification_url,
            'expiry_hours': settings.EMAIL_VERIFICATION_TIMEOUT_DAYS * 24,
        }
        
        html_message = render_to_string('accounts/email_verification.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject='[Resee] 이메일 인증을 완료해주세요',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Verification email sent to {user.email}")
        return True
        
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
        return False
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        return False


@shared_task
def send_welcome_email(user_id):
    """Send welcome email after successful verification"""
    try:
        from .models import User
        user = User.objects.get(id=user_id)
        
        context = {
            'user': user,
            'login_url': f"{settings.FRONTEND_URL}/login",
        }
        
        html_message = render_to_string('accounts/welcome_email.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='[Resee] 환영합니다!',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent to {user.email}")
        return True
        
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
        return False
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        return False