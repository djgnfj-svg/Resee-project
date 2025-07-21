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
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class EmailTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token view that uses email instead of username"""
    serializer_class = EmailTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    """User viewset"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer
    
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
    
    def get(self, request):
        """Get user profile"""
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)
    
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