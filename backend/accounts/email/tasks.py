"""
Celery tasks for email operations
"""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_verification_email_async(self, user_id: int):
    """
    비동기 이메일 인증 발송

    Args:
        user_id: 사용자 ID

    Returns:
        bool: 발송 성공 여부
    """
    from .email_service import EmailService

    try:
        email_service = EmailService()
        success = email_service.send_verification_email(user_id)

        if success:
            logger.info(f"Async verification email sent for user_id: {user_id}")
        else:
            logger.warning(f"Failed to send async verification email for user_id: {user_id}")

        return success

    except Exception as exc:
        logger.error(f"Error sending async verification email for user_id {user_id}: {str(exc)}")
        # Retry after 60 seconds
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_password_reset_email_async(self, user_id: int, reset_token: str):
    """
    비동기 비밀번호 재설정 이메일 발송

    Args:
        user_id: 사용자 ID
        reset_token: 재설정 토큰

    Returns:
        bool: 발송 성공 여부
    """
    from .email_service import EmailService

    try:
        email_service = EmailService()
        success = email_service.send_password_reset_email(user_id, reset_token)

        if success:
            logger.info(f"Async password reset email sent for user_id: {user_id}")
        else:
            logger.warning(f"Failed to send async password reset email for user_id: {user_id}")

        return success

    except Exception as exc:
        logger.error(f"Error sending async password reset email for user_id {user_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)
