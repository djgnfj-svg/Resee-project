from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer, ProfileSerializer, UserRegistrationSerializer, 
    PasswordChangeSerializer, AccountDeleteSerializer, EmailTokenObtainPairSerializer
)
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
                return Response(
                    {
                        'message': '회원가입이 완료되었습니다.',
                        'user': UserSerializer(user).data
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