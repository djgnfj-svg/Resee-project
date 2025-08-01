from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from .serializers import (
    UserSerializer, ProfileSerializer, UserRegistrationSerializer, 
    PasswordChangeSerializer, AccountDeleteSerializer, EmailTokenObtainPairSerializer
)
from .google_auth import GoogleAuthSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class EmailTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token view that uses email instead of username"""
    serializer_class = EmailTokenObtainPairSerializer
    
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
    @action(detail=False, methods=['post'], permission_classes=[])
    def register(self, request):
        """User registration endpoint"""
        logger.info(f"회원가입 요청: {request.data.get('email', 'unknown')}")
        
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                logger.info(f"회원가입 성공: {user.email}")
                
                # 개발 환경에서는 자동으로 이메일 인증 완료 처리
                if settings.DEBUG:
                    user.is_email_verified = True
                    user.save()
                    logger.info(f"개발 환경: {user.email} 자동 이메일 인증 완료")
                    
                    return Response(
                        {
                            'message': '회원가입이 완료되었습니다!',
                            'user': UserSerializer(user).data,
                            'requires_email_verification': False
                        },
                        status=status.HTTP_201_CREATED
                    )
                else:
                    # 프로덕션 환경에서는 이메일 인증 필요
                    from .tasks import send_verification_email
                    send_verification_email.delay(user.id)
                    
                    return Response(
                        {
                            'message': '회원가입이 완료되었습니다. 이메일을 확인하여 인증을 완료해주세요.',
                            'user': UserSerializer(user).data,
                            'requires_email_verification': True
                        },
                        status=status.HTTP_201_CREATED
                    )
            except Exception as e:
                logger.error(f"회원가입 실패: {str(e)}")
                return Response(
                    {
                        'error': '회원가입 중 오류가 발생했습니다.',
                        'details': str(e)
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # 상세한 에러 정보 로깅
        logger.error(f"회원가입 유효성 검사 실패: {serializer.errors}")
        
        # 에러 메시지를 한국어로 변환
        error_messages = {}
        for field, errors in serializer.errors.items():
            if isinstance(errors, list):
                error_messages[field] = errors
            else:
                error_messages[field] = [str(errors)]
        
        return Response(
            {
                'error': '입력 정보를 확인해주세요.',
                'field_errors': error_messages
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class ProfileView(APIView):
    """User profile view"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="프로필 조회",
        operation_description="현재 로그인된 사용자의 프로필 정보를 조회합니다.",
        tags=['User Profile'],
        responses={
            200: ProfileSerializer,
            401: "인증 필요",
        }
    )
    def get(self, request):
        """Get user profile"""
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="프로필 수정",
        operation_description="""현재 로그인된 사용자의 프로필 정보를 수정합니다.
        
        **요청 예시:**
        ```json
        {
          "first_name": "홍",
          "last_name": "길동",
          "timezone": "Asia/Seoul",
          "notification_enabled": true
        }
        ```
        """,
        tags=['User Profile'],
        request_body=ProfileSerializer,
        responses={
            200: ProfileSerializer,
            400: "잘못된 요청 - 유효성 검사 실패",
            401: "인증 필요",
        }
    )
    def put(self, request):
        """Update user profile"""
        serializer = ProfileSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        tags=['User Profile'],
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
    def post(self, request):
        """Change user password"""
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                serializer.save()
                logger.info(f"Password changed for user {request.user.email}")
                return Response(
                    {'message': 'Password changed successfully'},
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                logger.error(f"Password change failed for user {request.user.email}: {str(e)}")
                return Response(
                    {'error': 'Password change failed'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountDeleteView(APIView):
    """Account deletion view"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="계정 삭제",
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
        tags=['User Profile'],
        request_body=AccountDeleteSerializer,
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
    def post(self, request):
        """Delete user account"""
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


class EmailVerificationView(APIView):
    """Email verification view"""
    permission_classes = [AllowAny]
    
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
        """Verify email with token"""
        token = request.data.get('token')
        email = request.data.get('email')
        
        if not token or not email:
            return Response(
                {'error': '토큰과 이메일을 제공해주세요.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email, email_verification_token=token)
            
            # Check if token has expired (default 24 hours)
            expiry_time = user.email_verification_sent_at + timedelta(days=1)
            if timezone.now() > expiry_time:
                logger.warning(f"Email verification token expired for user {user.email}")
                return Response(
                    {'error': '인증 토큰이 만료되었습니다. 새로운 인증 이메일을 요청해주세요.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mark email as verified
            user.is_email_verified = True
            user.email_verification_token = None
            user.email_verification_sent_at = None
            user.save()
            
            logger.info(f"Email verification successful for user {user.email}")
            
            # Send welcome email
            from .tasks import send_welcome_email
            send_welcome_email.delay(user.id)
            
            return Response(
                {
                    'message': '이메일 인증이 완료되었습니다!',
                    'user': UserSerializer(user).data
                },
                status=status.HTTP_200_OK
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
            from .tasks import send_verification_email
            send_verification_email.delay(user.id)
            
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


class GoogleOAuthView(APIView):
    """Google OAuth 로그인 뷰"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Google OAuth 로그인",
        operation_description="""Google OAuth 토큰을 사용하여 로그인하거나 회원가입합니다.
        
        **요청 예시:**
        ```json
        {
          "credential": "google_oauth2_credential_token"
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


class WeeklyGoalUpdateView(APIView):
    """주간 목표 설정 API"""
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        """주간 목표 업데이트"""
        user = request.user
        weekly_goal = request.data.get('weekly_goal')
        
        if weekly_goal is None:
            return Response(
                {'error': '주간 목표를 입력해주세요.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            weekly_goal = int(weekly_goal)
            if weekly_goal < 1 or weekly_goal > 1000:
                return Response(
                    {'error': '주간 목표는 1회 이상 1000회 이하로 설정해주세요.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {'error': '올바른 숫자를 입력해주세요.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.weekly_goal = weekly_goal
        user.save()
        
        return Response({
            'message': '주간 목표가 성공적으로 업데이트되었습니다.',
            'weekly_goal': weekly_goal
        }, status=status.HTTP_200_OK)