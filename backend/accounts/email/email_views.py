"""
Email-related views: verification, resend, and subscription.
"""
import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from resee.throttling import EmailRateThrottle

User = get_user_model()
logger = logging.getLogger(__name__)


class EmailVerificationView(APIView):
    """Email verification view"""
    permission_classes = [AllowAny]
    throttle_classes = [EmailRateThrottle]

    @swagger_auto_schema(
        operation_summary="이메일 인증",
        operation_description="""이메일 인증 토큰으로 사용자 이메일을 인증합니다.

        **요청 예시:**
        ```json
        {
          "email": "user@example.com",
          "token": "verification_token_here"
        }
        ```

        토큰은 24시간 동안 유효합니다.
        """,
        tags=['Email Verification'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description="사용자 이메일"),
                'token': openapi.Schema(type=openapi.TYPE_STRING, description="인증 토큰"),
            },
            required=['email', 'token']
        ),
        responses={
            200: openapi.Response(
                description="이메일 인증 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="성공 메시지"),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT, description="사용자 정보"),
                    }
                )
            ),
            400: "잘못된 요청 - 토큰 만료 또는 유효하지 않음",
            500: "서버 오류",
        }
    )
    def post(self, request):
        """Verify email with token.

        Security: Uses hashed token verification with constant-time comparison.
        The token is sent in plaintext by the user, but compared against the
        SHA-256 hash stored in the database.
        """
        from ..utils.serializers import UserSerializer

        token = request.data.get('token')
        email = request.data.get('email')

        if not token or not email:
            return Response(
                {'error': '토큰과 이메일을 제공해주세요.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get user by email only
            user = User.objects.get(email=email)

            # 🔒 보안: Use secure hashed token verification method
            # This method:
            # 1. Hashes the provided token with SHA-256
            # 2. Uses constant-time comparison to prevent timing attacks
            # 3. Checks token expiration
            if user.verify_email(token):
                logger.info(f"Email verification successful for user {user.email}")

                # Send welcome email
                from .email_service import EmailService
                email_service = EmailService()
                email_service.send_welcome_email(user.id)

                return Response(
                    {
                        'message': '이메일 인증이 완료되었습니다!',
                        'user': UserSerializer(user).data
                    },
                    status=status.HTTP_200_OK
                )
            else:
                logger.warning(f"Invalid email verification attempt: {email}")
                return Response(
                    {'error': '유효하지 않은 인증 정보입니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except User.DoesNotExist:
            logger.warning(f"Invalid email verification attempt: {email}")
            return Response(
                {'error': '유효하지 않은 인증 정보입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Email verification failed: {str(e)}")
            return Response(
                {'error': '이메일 인증 중 오류가 발생했습니다.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResendVerificationView(APIView):
    """Resend email verification"""
    permission_classes = [AllowAny]
    throttle_classes = [EmailRateThrottle]

    @swagger_auto_schema(
        operation_summary="인증 이메일 재발송",
        operation_description="""이메일 인증을 위한 인증 이메일을 재발송합니다.

        **요청 예시:**
        ```json
        {
          "email": "user@example.com"
        }
        ```

        **제한사항:**
        - 5분 간격으로만 재발송 가능
        - 이미 인증된 계정은 재발송 불가
        """,
        tags=['Email Verification'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description="사용자 이메일"),
            },
            required=['email']
        ),
        responses={
            200: openapi.Response(
                description="인증 이메일 재발송 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="성공 메시지"),
                    }
                )
            ),
            400: "잘못된 요청 - 이미 인증된 계정 또는 존재하지 않는 이메일",
            429: "너무 많은 요청 - 5분 후 재시도",
            500: "서버 오류",
        }
    )
    def post(self, request):
        """Resend verification email"""
        email = request.data.get('email')

        if not email:
            return Response(
                {'error': '이메일을 제공해주세요.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)

            if user.is_email_verified:
                return Response(
                    {'error': '이미 인증된 계정입니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check for rate limiting (prevent spam)
            if user.email_verification_sent_at:
                time_since_last = timezone.now() - user.email_verification_sent_at
                if time_since_last < timedelta(minutes=5):
                    remaining_minutes = 5 - int(time_since_last.total_seconds() / 60)
                    return Response(
                        {'error': f'인증 이메일은 {remaining_minutes}분 후에 다시 요청할 수 있습니다.'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS
                    )

            # Send verification email
            from .email_service import EmailService
            email_service = EmailService()
            email_service.send_verification_email(user.id)

            logger.info(f"Verification email resent to {user.email}")

            return Response(
                {'message': '인증 이메일이 재발송되었습니다. 이메일을 확인해주세요.'},
                status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            logger.warning(f"Resend verification attempt for non-existent email: {email}")
            return Response(
                {'error': '등록되지 않은 이메일입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Resend verification failed: {str(e)}")
            return Response(
                {'error': '인증 이메일 재발송 중 오류가 발생했습니다.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
