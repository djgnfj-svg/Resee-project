import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from resee.error_handlers import APIErrorHandler, StandardAPIResponse
from resee.throttling import LoginRateThrottle, RegistrationRateThrottle

from ..utils.serializers import (
    EmailTokenObtainPairSerializer, PasswordChangeSerializer,
    UserRegistrationSerializer, UserSerializer,
)
from .google_auth import GoogleAuthSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


def set_refresh_token_cookie(response, refresh_token):
    """Set refresh token as HttpOnly cookie"""
    # Determine if we're in production (HTTPS) or development (HTTP)
    is_production = not settings.DEBUG

    response.set_cookie(
        key='refresh_token',
        value=str(refresh_token),
        max_age=60 * 60 * 24 * 7,  # 7 days
        httponly=True,
        secure=is_production,  # HTTPS only in production
        samesite='Lax',  # CSRF protection
        path='/',
    )
    return response


def delete_refresh_token_cookie(response):
    """Delete refresh token cookie"""
    response.delete_cookie(
        key='refresh_token',
        path='/',
        samesite='Lax',
    )
    return response


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
          "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        }
        ```

        **보안:**
        - Access token: 응답 본문에 포함 (메모리에 저장)
        - Refresh token: HttpOnly Cookie로 설정 (XSS 공격 방지)

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
                    }
                )
            ),
            400: "잘못된 요청 - 이메일 또는 비밀번호 오류",
            401: "인증 실패 - 이메일 또는 비밀번호가 틀림",
        }
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        # Set refresh token as HttpOnly cookie
        if response.status_code == 200 and 'refresh' in response.data:
            refresh_token = response.data.pop('refresh')
            set_refresh_token_cookie(response, refresh_token)

        return response


class UserViewSet(viewsets.ModelViewSet):
    """User viewset"""
    queryset = User.objects.select_related('subscription').all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """Override permissions based on action"""
        if self.action in ['create', 'register']:
            return []
        elif self.action in ['me', 'update_password', 'destroy']:
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_throttle_classes(self):
        """Override throttle classes based on action"""
        if self.action in ['create', 'register']:
            return [RegistrationRateThrottle]
        return super().get_throttle_classes()

    def get_serializer_class(self):
        if self.action in ['create', 'register']:
            return UserRegistrationSerializer
        elif self.action == 'update_password':
            return PasswordChangeSerializer
        return UserSerializer

    @swagger_auto_schema(
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
    def create(self, request):
        """RESTful user registration (POST /users/)"""
        return self._register_user(request)

    @action(detail=False, methods=['post'])
    def register(self, request):
        """Legacy registration endpoint (POST /users/register/) - 하위 호환성"""
        return self._register_user(request)

    def _register_user(self, request):
        """Common registration logic"""
        logger.info(f"User registration request: {request.data.get('email', 'unknown')}")

        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                logger.info(f"User registration successful: {user.email}")

                # 이메일 인증 강제 설정 확인
                enforce_email_verification = getattr(settings, 'ENFORCE_EMAIL_VERIFICATION', False)

                # ENFORCE_EMAIL_VERIFICATION이 False일 때만 자동 인증
                if not enforce_email_verification:
                    user.is_email_verified = True
                    user.save()
                    logger.info(f"Development environment: Email auto-verified for {user.email}")

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
                logger.error(f"User registration failed: {str(e)}")
                return APIErrorHandler.server_error('An error occurred during registration.')

        # Log detailed error information
        logger.error(f"User registration validation failed: {serializer.errors}")

        return APIErrorHandler.validation_error(serializer.errors)

    @swagger_auto_schema(
        method='get',
        operation_summary="현재 사용자 정보 조회",
        operation_description="현재 로그인된 사용자의 상세 정보를 조회합니다.",
        tags=['Authentication'],
        responses={
            200: UserSerializer,
            401: "인증 필요",
        }
    )
    @swagger_auto_schema(
        method='delete',
        operation_summary="계정 삭제 (RESTful)",
        operation_description="""현재 로그인된 사용자의 계정을 완전히 삭제합니다.

        **주의:** 이 작업은 되돌릴 수 없으며, 모든 사용자 데이터가 영구적으로 삭제됩니다.

        **요청 예시:**
        ```json
        {
          "password": "current_password123",
          "confirmation": "DELETE"
        }
        ```
        """,
        tags=['Authentication'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'password': openapi.Schema(type=openapi.TYPE_STRING, description="현재 비밀번호"),
                'confirmation': openapi.Schema(type=openapi.TYPE_STRING, description="'DELETE' 문자열"),
            },
            required=['password', 'confirmation']
        ),
        responses={
            200: openapi.Response(
                description="계정 삭제 성공",
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
    @action(detail=False, methods=['get', 'delete'], url_path='me')
    def me(self, request):
        """Get or delete current user (GET/DELETE /users/me/)"""
        if request.method == 'GET':
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        elif request.method == 'DELETE':
            from ..utils.serializers import AccountDeleteSerializer
            serializer = AccountDeleteSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                try:
                    user = request.user
                    email = user.email

                    # Log the deletion before deleting
                    logger.warning(f"Account deletion initiated for user {email}")

                    # Delete the account
                    serializer.save()

                    logger.warning(f"Account deleted for user {email}")

                    return Response(
                        {'message': 'Account deleted successfully'},
                        status=status.HTTP_200_OK
                    )
                except Exception as e:
                    logger.error(f"Account deletion failed for user {request.user.email}: {str(e)}")
                    return Response(
                        {'error': 'Account deletion failed'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        method='put',
        operation_summary="비밀번호 변경 (RESTful)",
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
                        'action_required': openapi.Schema(type=openapi.TYPE_STRING, description="필요한 조치"),
                    }
                )
            ),
            400: "잘못된 요청 - 유효성 검사 실패",
            401: "인증 필요",
            500: "서버 오류",
        }
    )
    @action(detail=False, methods=['put'], url_path='me/password')
    @transaction.atomic
    def update_password(self, request):
        """Change user password (PUT /users/me/password/)"""
        from .services import AuthService

        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            current_password = serializer.validated_data['current_password']
            new_password = serializer.validated_data['new_password']

            # Use AuthService for password change
            auth_service = AuthService(request.user)
            success, error_message = auth_service.change_password(
                current_password=current_password,
                new_password=new_password
            )

            if success:
                return Response({
                    'message': 'Password changed successfully. Please login again on all devices.',
                    'action_required': 'relogin'
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': error_message or 'Password change failed'},
                    status=status.HTTP_400_BAD_REQUEST
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

        **보안:**
        - Access token: 응답 본문에 포함 (메모리에 저장)
        - Refresh token: HttpOnly Cookie로 설정 (XSS 공격 방지)
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

            logger.info(f"Google OAuth login successful: {user.email} ({'new' if is_new_user else 'existing'} user)")

            response_data = {
                'message': f"Google login {'and registration' if is_new_user else ''} completed successfully.",
                'access': str(access_token),
                'user': UserSerializer(user).data,
                'is_new_user': is_new_user,
                'google_user_info': {
                    'name': google_user_info.get('name', ''),
                    'picture': google_user_info.get('picture', ''),
                    'locale': google_user_info.get('locale', ''),
                }
            }

            response = Response(response_data, status=status.HTTP_200_OK)

            # Set refresh token as HttpOnly cookie
            set_refresh_token_cookie(response, refresh)

            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CookieTokenRefreshView(TokenRefreshView):
    """Custom token refresh view that reads refresh token from HttpOnly cookie"""

    @swagger_auto_schema(
        operation_summary="JWT 토큰 갱신 (Cookie 기반)",
        operation_description="""HttpOnly Cookie에 저장된 refresh token을 사용하여 새 access token을 발급합니다.

        **보안:**
        - Refresh token은 HttpOnly Cookie에서 자동으로 읽어옵니다
        - 새로운 refresh token도 HttpOnly Cookie로 설정됩니다 (rotation)
        - Access token만 응답 본문에 포함됩니다

        **응답 예시:**
        ```json
        {
          "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        }
        ```
        """,
        tags=['Authentication'],
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, properties={}),
        responses={
            200: openapi.Response(
                description="토큰 갱신 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description="새 액세스 토큰 (60분 유효)"),
                    }
                )
            ),
            401: "인증 실패 - refresh token이 없거나 유효하지 않음",
        }
    )
    def post(self, request, *args, **kwargs):
        # Read refresh token from cookie
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response(
                {'detail': 'Refresh token not found in cookies'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Add refresh token to request data
        request.data['refresh'] = refresh_token

        try:
            response = super().post(request, *args, **kwargs)

            # Set new refresh token as HttpOnly cookie (rotation)
            if response.status_code == 200 and 'refresh' in response.data:
                new_refresh_token = response.data.pop('refresh')
                set_refresh_token_cookie(response, new_refresh_token)

            return response
        except (InvalidToken, TokenError) as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(APIView):
    """Logout view that clears the refresh token cookie"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="로그아웃",
        operation_description="""로그아웃하고 refresh token cookie를 삭제합니다.

        **기능:**
        - Refresh token을 blacklist에 추가 (재사용 방지)
        - HttpOnly Cookie 삭제

        **헤더 요구사항:**
        - Authorization: Bearer <access_token>
        """,
        tags=['Authentication'],
        responses={
            200: openapi.Response(
                description="로그아웃 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="성공 메시지"),
                    }
                )
            ),
            401: "인증 필요",
        }
    )
    def post(self, request):
        try:
            # Get refresh token from cookie
            refresh_token = request.COOKIES.get('refresh_token')

            if refresh_token:
                # Blacklist the refresh token
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.info(f"User {request.user.email} logged out successfully")

            response = Response(
                {'message': 'Logged out successfully'},
                status=status.HTTP_200_OK
            )

            # Delete the refresh token cookie
            delete_refresh_token_cookie(response)

            return response
        except Exception as e:
            logger.error(f"Logout failed for user {request.user.email}: {str(e)}")
            # Still delete the cookie even if blacklisting fails
            response = Response(
                {'message': 'Logged out successfully'},
                status=status.HTTP_200_OK
            )
            delete_refresh_token_cookie(response)
            return response
