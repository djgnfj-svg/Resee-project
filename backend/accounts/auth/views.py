import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from resee.throttling import (EmailRateThrottle, LoginRateThrottle,
                              RegistrationRateThrottle)
from resee.error_handlers import APIErrorHandler, StandardAPIResponse
from resee.permissions import EmailVerifiedRequired

from .google_auth import GoogleAuthSerializer
from ..utils.serializers import (EmailTokenObtainPairSerializer,
                                PasswordChangeSerializer,
                                UserRegistrationSerializer, UserSerializer)

User = get_user_model()
logger = logging.getLogger(__name__)


class EmailTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token view that uses email instead of username"""
    serializer_class = EmailTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]

    @swagger_auto_schema(
        operation_summary="로그인 (JWT 토큰 획득)",
        operation_description="""이메일과 비밀번호로 로그인하여 JWT 토큰을 획득합니다.

        **요청 예시:**
        ```json
        {
          "email": "user@example.com",
          "password": "password123"
        }
        ```

        **응답 예시:**
        ```json
        {
          "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
          "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        }
        ```

        받은 `access` 토큰을 다음과 같이 헤더에 포함하여 API 요청을 보내세요:
        `Authorization: Bearer <access_token>`
        """,
        tags=['Authentication'],
        request_body=EmailTokenObtainPairSerializer,
        responses={
            200: openapi.Response(
                description="로그인 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description="액세스 토큰 (60분 유효)"),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description="리프레시 토큰 (7일 유효)"),
                    }
                )
            ),
            400: "잘못된 요청 - 이메일 또는 비밀번호 오류",
            401: "인증 실패 - 이메일 또는 비밀번호가 틀림",
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserViewSet(viewsets.ModelViewSet):
    """User viewset"""
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer

    @swagger_auto_schema(
        method='post',
        operation_summary="회원가입",
        operation_description="""새로운 사용자 계정을 생성합니다.

        **요청 예시:**
        ```json
        {
          "email": "user@example.com",
          "password": "password123",
          "password_confirm": "password123",
          "first_name": "홍",
          "last_name": "길동"
        }
        ```

        개발 환경에서는 이메일 인증이 자동으로 완료되며, 프로덕션 환경에서는 인증 이메일이 발송됩니다.
        """,
        tags=['Authentication'],
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="회원가입 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="성공 메시지"),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT, description="생성된 사용자 정보"),
                        'requires_email_verification': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="이메일 인증 필요 여부"),
                    }
                )
            ),
            400: "잘못된 요청 - 유효성 검사 실패",
            500: "서버 오류",
        }
    )
    @action(detail=False, methods=['post'], permission_classes=[], throttle_classes=[RegistrationRateThrottle])
    def register(self, request):
        """User registration endpoint"""
        logger.info(f"회원가입 요청: {request.data.get('email', 'unknown')}")

        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                logger.info(f"회원가입 성공: {user.email}")

                # 이메일 인증 강제 설정 확인
                enforce_email_verification = getattr(settings, 'ENFORCE_EMAIL_VERIFICATION', False)

                # ENFORCE_EMAIL_VERIFICATION이 False일 때만 자동 인증
                if not enforce_email_verification:
                    user.is_email_verified = True
                    user.save()
                    logger.info(f"개발 환경: {user.email} 자동 이메일 인증 완료")

                    return StandardAPIResponse.created(
                        data={
                            'user': UserSerializer(user).data,
                            'requires_email_verification': False
                        },
                        message='회원가입이 완료되었습니다!'
                    )
                else:
                    # 프로덕션 환경에서는 이메일 인증 필요
                    from ..email.email_service import EmailService
                    email_service = EmailService()
                    email_service.send_verification_email(user.id)

                    return StandardAPIResponse.created(
                        data={
                            'user': UserSerializer(user).data,
                            'requires_email_verification': True
                        },
                        message='회원가입이 완료되었습니다. 이메일을 확인하여 인증을 완료해주세요.'
                    )
            except Exception as e:
                logger.error(f"회원가입 실패: {str(e)}")
                return APIErrorHandler.server_error('회원가입 중 오류가 발생했습니다.')

        # 상세한 에러 정보 로깅
        logger.error(f"회원가입 유효성 검사 실패: {serializer.errors}")

        return APIErrorHandler.validation_error(serializer.errors)


class PasswordChangeView(APIView):
    """Password change view"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="비밀번호 변경",
        operation_description="""현재 로그인된 사용자의 비밀번호를 변경합니다.

        **요청 예시:**
        ```json
        {
          "current_password": "old_password123",
          "new_password": "new_password123",
          "new_password_confirm": "new_password123"
        }
        ```
        """,
        tags=['Authentication'],
        request_body=PasswordChangeSerializer,
        responses={
            200: openapi.Response(
                description="비밀번호 변경 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="성공 메시지"),
                    }
                )
            ),
            400: "잘못된 요청 - 유효성 검사 실패",
            401: "인증 필요",
            500: "서버 오류",
        }
    )
    @transaction.atomic
    def post(self, request):
        """Change user password and invalidate all existing tokens.

        Security: All JWT tokens are blacklisted to prevent unauthorized
        access with old tokens after password change.
        """
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            try:
                # 비밀번호 변경
                serializer.save()

                # 🔒 보안: 모든 기존 JWT 토큰 무효화
                try:
                    from rest_framework_simplejwt.token_blacklist.models import (
                        OutstandingToken,
                        BlacklistedToken
                    )

                    # 사용자의 모든 토큰을 블랙리스트에 추가
                    outstanding_tokens = OutstandingToken.objects.filter(
                        user=request.user
                    )

                    for token in outstanding_tokens:
                        # 이미 블랙리스트에 있지 않은 경우만 추가
                        BlacklistedToken.objects.get_or_create(token=token)

                    logger.info(
                        f"Password changed and {outstanding_tokens.count()} tokens "
                        f"blacklisted for user {request.user.email}"
                    )

                except ImportError:
                    # token_blacklist가 없는 경우 경고만 로깅
                    logger.warning(
                        "token_blacklist not available. "
                        "Old tokens will remain valid until expiration."
                    )

                return Response({
                    'message': 'Password changed successfully. Please login again on all devices.',
                    'action_required': 'relogin'
                }, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(
                    f"Password change failed for user {request.user.email}: {str(e)}",
                    exc_info=True
                )
                return Response(
                    {'error': 'Password change failed'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleOAuthView(APIView):
    """Google OAuth 로그인 뷰"""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Google OAuth 로그인",
        operation_description="""Google OAuth 토큰을 사용하여 로그인하거나 회원가입합니다.

        **요청 예시:**
        ```json
        {
          "token": "google_oauth2_credential_token"
        }
        ```

        **특징:**
        - 기존 계정이 있으면 로그인
        - 없으면 자동으로 계정 생성
        - 이메일 인증이 자동으로 완료됨
        """,
        tags=['Authentication'],
        request_body=GoogleAuthSerializer,
        responses={
            200: openapi.Response(
                description="Google OAuth 로그인 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="성공 메시지"),
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description="액세스 토큰"),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description="리프레시 토큰"),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT, description="사용자 정보"),
                        'is_new_user': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="신규 사용자 여부"),
                        'google_user_info': openapi.Schema(type=openapi.TYPE_OBJECT, description="Google 사용자 정보"),
                    }
                )
            ),
            400: "잘못된 요청 - 유효하지 않은 Google 토큰",
            500: "서버 오류",
        }
    )
    def post(self, request):
        """Google OAuth 토큰으로 로그인"""
        serializer = GoogleAuthSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.get_user()
            is_new_user = serializer.is_new_user()
            google_user_info = serializer.get_google_user_info()

            # JWT 토큰 생성
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            logger.info(f"Google OAuth 로그인 성공: {user.email} ({'신규' if is_new_user else '기존'} 사용자)")

            response_data = {
                'message': f"Google 로그인 {'및 회원가입이' if is_new_user else ''}이 완료되었습니다.",
                'access': str(access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
                'is_new_user': is_new_user,
                'google_user_info': {
                    'name': google_user_info.get('name', ''),
                    'picture': google_user_info.get('picture', ''),
                    'locale': google_user_info.get('locale', ''),
                }
            }

            return Response(response_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)