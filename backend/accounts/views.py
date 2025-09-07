import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
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
from .serializers import (AccountDeleteSerializer,
                          EmailTokenObtainPairSerializer,
                          PasswordChangeSerializer, ProfileSerializer,
                          SubscriptionUpgradeSerializer,
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
                
                # 개발 환경에서는 자동으로 이메일 인증 완료 처리
                if settings.DEBUG:
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
                    from .email_service import EmailService
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
        serializer = UserSerializer(request.user)
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
    
    def get(self, request):
        """주간 목표 조회"""
        user = request.user
        return Response({
            'weekly_goal': user.weekly_goal
        }, status=status.HTTP_200_OK)
    
    def put(self, request):
        """주간 목표 업데이트 (PUT method)"""
        return self._update_weekly_goal(request)
    
    def patch(self, request):
        """주간 목표 업데이트 (PATCH method)"""
        return self._update_weekly_goal(request)
    
    def _update_weekly_goal(self, request):
        """주간 목표 업데이트 공통 로직"""
        user = request.user
        weekly_goal = request.data.get('weekly_goal')
        
        if weekly_goal is None:
            return Response(
                {'error': '주간 목표를 입력해주세요.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            weekly_goal = int(weekly_goal)
            if weekly_goal < 1 or weekly_goal > 100:
                return Response(
                    {'error': '주간 목표는 1회 이상 100회 이하로 설정해주세요.'}, 
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


class AIUsageView(APIView):
    """AI 사용량 조회 API"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="AI 사용량 조회",
        operation_description="""
        현재 사용자의 AI 기능 사용량을 조회합니다.
        
        **응답 데이터:**
        - 오늘의 사용량 (생성한 질문 수, 평가 횟수)
        - 일일 한도 및 남은 횟수
        - 구독 티어별 제한 정보
        - 주간 사용량 통계
        
        **구독 티어별 한도:**
        - Free: 10개/일
        - Premium: 50개/일
        - Pro: 200개/일
        """,
        tags=['AI Usage'],
        responses={
            200: openapi.Response(
                description="AI 사용량 정보",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'today': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                                'questions_generated': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'evaluations_performed': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'daily_limit': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'remaining': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'usage_percentage': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'tier': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        'weekly': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'total_questions': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'total_evaluations': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'average_daily_questions': openapi.Schema(type=openapi.TYPE_NUMBER),
                            }
                        ),
                        'subscription_info': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'tier': openapi.Schema(type=openapi.TYPE_STRING),
                                'features': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                                'can_use_ai': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            }
                        )
                    }
                )
            ),
            401: "인증 필요",
        }
    )
    def get(self, request):
        """AI 사용량 정보 조회"""
        user = request.user
        
        # 오늘의 사용량
        usage_today = AIUsageTracking.get_or_create_for_today(user)
        today_summary = usage_today.get_usage_summary()
        
        # 주간 사용량
        weekly_summary = AIUsageTracking.get_user_weekly_usage(user, weeks=1)
        
        # 구독 정보
        subscription_info = {
            'tier': user.subscription.tier,
            'features': user.get_ai_features_list(),
            'can_use_ai': user.can_use_ai_features(),
            'question_limit': user.get_ai_question_limit(),
        }
        
        response_data = {
            'today': today_summary,
            'weekly': {
                'total_questions': weekly_summary['total_questions'],
                'total_evaluations': weekly_summary['total_evaluations'],
                'average_daily_questions': weekly_summary['average_daily_questions'],
            },
            'subscription_info': subscription_info
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class SubscriptionUpgradeView(APIView):
    """구독 업그레이드 API"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="구독 플랜 업그레이드",
        operation_description="""
        사용자의 구독 플랜을 업그레이드합니다. (결제 시스템 없이 즉시 적용)
        
        **요청 예시:**
        ```json
        {
          "tier": "premium"
        }
        ```
        
        **지원하는 티어:**
        - free: 무료 (기본)
        - basic: 베이직 (14일 간격)
        - premium: 프리미엄 (30일 간격)
        - pro: 프로 (90일 간격)
        
        **업그레이드 조건:**
        - 이메일 인증이 완료된 사용자만 가능
        - 현재 티어보다 높은 티어로만 업그레이드 가능
        - 다운그레이드는 지원하지 않음
        """,
        tags=['Subscription'],
        request_body=SubscriptionUpgradeSerializer,
        responses={
            200: openapi.Response(
                description="구독 업그레이드 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="성공 메시지"),
                        'subscription': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'tier': openapi.Schema(type=openapi.TYPE_STRING),
                                'tier_display': openapi.Schema(type=openapi.TYPE_STRING),
                                'max_interval_days': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'start_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                'end_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                            }
                        ),
                        'ai_features': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'ai_question_limit': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            ),
            400: "잘못된 요청 - 유효하지 않은 티어 또는 업그레이드 불가",
            401: "인증 필요",
            403: "권한 없음 - 이메일 인증 필요",
            500: "서버 오류",
        }
    )
    def post(self, request):
        """구독 플랜 업그레이드"""
        serializer = SubscriptionUpgradeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        new_tier = serializer.validated_data['tier']
        
        # 이메일 인증 확인
        if not user.is_email_verified:
            logger.warning(f"Subscription upgrade attempt without email verification: {user.email}")
            return Response(
                {'error': '구독을 업그레이드하려면 먼저 이메일 인증을 완료해주세요.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # 현재 구독 가져오기
            from .models import Subscription, SubscriptionTier
            subscription = getattr(user, 'subscription', None)
            
            if not subscription:
                # 구독이 없으면 새로 생성 (기본적으로 FREE로 생성되어야 함)
                subscription = Subscription.objects.create(
                    user=user,
                    tier=SubscriptionTier.FREE
                )
            
            # 티어 순서 확인 (다운그레이드 방지)
            tier_hierarchy = {
                SubscriptionTier.FREE: 0,
                SubscriptionTier.BASIC: 1,
                SubscriptionTier.PREMIUM: 2,
                SubscriptionTier.PRO: 3,
            }
            
            current_tier_level = tier_hierarchy.get(subscription.tier, 0)
            new_tier_level = tier_hierarchy.get(new_tier, 0)
            
            if new_tier_level <= current_tier_level:
                return Response(
                    {'error': f'현재 티어({subscription.get_tier_display()})보다 높은 티어로만 업그레이드할 수 있습니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 구독 업그레이드 수행
            old_tier = subscription.tier
            subscription.tier = new_tier
            subscription.is_active = True
            subscription.start_date = timezone.now()
            
            # 구독 기간 설정 (개발용으로 30일로 설정)
            subscription.end_date = timezone.now() + timedelta(days=30)
            
            subscription.save()  # save() 메서드에서 max_interval_days가 자동 설정됨
            
            logger.info(f"Subscription upgraded: {user.email} from {old_tier} to {new_tier}")
            
            # 응답 데이터 구성
            response_data = {
                'message': f'구독이 성공적으로 {subscription.get_tier_display()}으로 업그레이드되었습니다!',
                'subscription': {
                    'tier': subscription.tier,
                    'tier_display': subscription.get_tier_display(),
                    'max_interval_days': subscription.max_interval_days,
                    'is_active': subscription.is_active,
                    'start_date': subscription.start_date.isoformat(),
                    'end_date': subscription.end_date.isoformat() if subscription.end_date else None,
                },
                'ai_features': user.get_ai_features_list(),
                'ai_question_limit': user.get_ai_question_limit(),
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Subscription upgrade failed for {user.email}: {str(e)}")
            return Response(
                {'error': '구독 업그레이드 중 오류가 발생했습니다.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )