import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from resee.error_handlers import APIErrorHandler, StandardAPIResponse

from .utils.serializers import (AccountDeleteSerializer, ProfileSerializer,
                                SubscriptionUpgradeSerializer, UserSerializer, NotificationPreferenceSerializer)

User = get_user_model()
logger = logging.getLogger(__name__)


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


class NotificationPreferenceView(APIView):
    """Notification preference management view"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="알림 설정 조회",
        operation_description="현재 로그인된 사용자의 알림 설정을 조회합니다.",
        tags=['Notification'],
        responses={
            200: NotificationPreferenceSerializer,
            401: "인증 필요",
        }
    )
    def get(self, request):
        """Get user notification preferences"""
        try:
            # Get or create notification preference for user
            from .models import NotificationPreference
            preference, created = NotificationPreference.objects.get_or_create(
                user=request.user
            )

            serializer = NotificationPreferenceSerializer(preference)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Failed to get notification preferences for {request.user.email}: {str(e)}")
            return Response(
                {'error': '알림 설정을 가져오는데 실패했습니다.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="알림 설정 수정",
        operation_description="""현재 로그인된 사용자의 알림 설정을 수정합니다.

        **요청 예시:**
        ```json
        {
          "email_notifications_enabled": true,
          "daily_reminder_enabled": true,
          "daily_reminder_time": "09:00",
          "evening_reminder_enabled": false,
          "evening_reminder_time": "20:00",
          "weekly_summary_enabled": true,
          "weekly_summary_day": 1,
          "weekly_summary_time": "09:00"
        }
        ```
        """,
        tags=['Notification'],
        request_body=NotificationPreferenceSerializer,
        responses={
            200: NotificationPreferenceSerializer,
            400: "잘못된 요청 - 유효성 검사 실패",
            401: "인증 필요",
        }
    )
    def put(self, request):
        """Update user notification preferences"""
        try:
            from .models import NotificationPreference

            # Get or create notification preference for user
            preference, created = NotificationPreference.objects.get_or_create(
                user=request.user
            )

            serializer = NotificationPreferenceSerializer(preference, data=request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Notification preferences updated for user {request.user.email}")
                return Response(serializer.data)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Failed to update notification preferences for {request.user.email}: {str(e)}")
            return Response(
                {'error': '알림 설정 저장에 실패했습니다.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Views are imported directly in urls.py to avoid circular imports