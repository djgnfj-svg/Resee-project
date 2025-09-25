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
                                SubscriptionUpgradeSerializer, UserSerializer)

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


# Views are imported directly in urls.py to avoid circular imports