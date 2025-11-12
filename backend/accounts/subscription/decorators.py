"""
Decorators for subscription-related operations.
"""
import functools
import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def require_admin_password(view_func):
    """
    Decorator to require admin password verification for subscription changes.

    Usage:
        @require_admin_password
        def my_view(request):
            # Admin password already verified
            pass

    Request data must contain 'password' field.
    The password is verified against SUBSCRIPTION_ADMIN_PASSWORD setting.

    Returns:
        - 400 if password field is missing
        - 403 if password is incorrect
        - 503 if SUBSCRIPTION_ADMIN_PASSWORD is not configured
        - Calls view_func if password is correct
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Get password from request data
        password = request.data.get('password')

        if not password:
            return Response(
                {'error': '비밀번호를 입력해주세요.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get admin password from settings
        admin_password = getattr(settings, 'SUBSCRIPTION_ADMIN_PASSWORD', None)

        if not admin_password:
            logger.error("SUBSCRIPTION_ADMIN_PASSWORD not configured")
            return Response(
                {'error': '구독 변경이 일시적으로 비활성화되었습니다.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Verify password
        if password != admin_password:
            logger.warning(
                f"Failed admin password verification attempt for user {request.user.email}"
            )
            return Response(
                {'error': '비밀번호가 올바르지 않습니다.'},
                status=status.HTTP_403_FORBIDDEN
            )

        logger.info(f"Admin password verified for user {request.user.email}")

        # Password verified, call the original view
        return view_func(request, *args, **kwargs)

    return wrapper


def require_user_password(view_func):
    """
    Decorator to require user's own password verification.

    Usage:
        @require_user_password
        def my_view(request):
            # User password already verified
            pass

    Request data must contain 'password' field.
    The password is verified against the logged-in user's password.

    Returns:
        - 400 if password field is missing
        - 403 if password is incorrect
        - Calls view_func if password is correct
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Get password from request data
        password = request.data.get('password')

        if not password:
            return Response(
                {'error': '비밀번호를 입력해주세요.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify user password
        if not request.user.check_password(password):
            logger.warning(
                f"Failed password verification attempt for user {request.user.email}"
            )
            return Response(
                {'error': '비밀번호가 올바르지 않습니다.'},
                status=status.HTTP_403_FORBIDDEN
            )

        logger.info(f"Password verified for user {request.user.email}")

        # Password verified, call the original view
        return view_func(request, *args, **kwargs)

    return wrapper
