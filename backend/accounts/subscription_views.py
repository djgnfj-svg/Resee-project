"""
Subscription-related views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Subscription, SubscriptionTier
from .serializers import (
    SubscriptionSerializer,
    SubscriptionTierSerializer,
    SubscriptionUpgradeSerializer
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_detail(request):
    """Get current user's subscription details"""
    subscription = get_object_or_404(Subscription, user=request.user)
    serializer = SubscriptionSerializer(subscription)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_tiers(request):
    """Get available subscription tiers"""
    tiers = []
    
    tier_info = {
        SubscriptionTier.FREE: {
            'price': 0,
            'features': [
                '최대 7일까지 복습 지원',
                '기본 학습 기능',
                '무제한 콘텐츠 생성'
            ]
        },
        SubscriptionTier.BASIC: {
            'price': 5000,
            'features': [
                '최대 30일까지 복습 지원',
                '향상된 통계 기능',
                '우선 지원'
            ]
        },
        SubscriptionTier.PREMIUM: {
            'price': 10000,
            'features': [
                '최대 60일까지 복습 지원',
                '고급 분석 기능',
                '전문가 복습 패턴',
                'API 접근'
            ]
        },
        SubscriptionTier.PRO: {
            'price': 20000,
            'features': [
                '최대 90일까지 복습 지원',
                '모든 프리미엄 기능',
                '팀 협업 기능',
                '우선 고객 지원',
                '커스텀 복습 주기'
            ]
        }
    }
    
    tier_max_days = {
        SubscriptionTier.FREE: 7,
        SubscriptionTier.BASIC: 30,
        SubscriptionTier.PREMIUM: 60,
        SubscriptionTier.PRO: 90
    }
    
    for tier_value, tier_label in SubscriptionTier.choices:
        tier_data = {
            'name': tier_value,
            'display_name': tier_label,
            'max_days': tier_max_days[tier_value],
            'price': tier_info[tier_value]['price'],
            'features': tier_info[tier_value]['features']
        }
        tiers.append(tier_data)
    
    serializer = SubscriptionTierSerializer(tiers, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subscription_upgrade(request):
    """Upgrade user's subscription"""
    serializer = SubscriptionUpgradeSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if not request.user.is_email_verified:
        return Response(
            {
                'error': '이메일 인증이 필요합니다.',
                'email_verified': False
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    if serializer.is_valid():
        tier = serializer.validated_data['tier']
        user = request.user
        
        # Get or create subscription
        subscription = getattr(user, 'subscription', None)
        if not subscription:
            from django.utils import timezone
            from datetime import timedelta
            subscription = Subscription.objects.create(
                user=user,
                tier=SubscriptionTier.FREE
            )
        
        # 티어 순서 확인
        tier_hierarchy = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.BASIC: 1,
            SubscriptionTier.PREMIUM: 2,
            SubscriptionTier.PRO: 3,
        }
        
        current_tier_level = tier_hierarchy.get(subscription.tier, 0)
        new_tier_level = tier_hierarchy.get(tier, 0)
        
        # 동일한 티어로의 변경 방지
        if new_tier_level == current_tier_level:
            return Response(
                {'error': f'이미 {subscription.get_tier_display()} 티어입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update subscription
        from django.utils import timezone
        from datetime import timedelta
        
        old_tier = subscription.tier
        subscription.tier = tier
        subscription.is_active = True
        subscription.start_date = timezone.now()
        # 개발용으로 30일 구독 기간 설정
        subscription.end_date = timezone.now() + timedelta(days=30)
        subscription.save()  # save() 메서드에서 max_interval_days가 자동 설정됨
        
        # 로그 기록
        import logging
        logger = logging.getLogger(__name__)
        
        # 업그레이드/다운그레이드 구분
        is_upgrade = new_tier_level > current_tier_level
        action_type = "업그레이드" if is_upgrade else "다운그레이드"
        
        logger.info(f"Subscription {action_type}: {user.email} from {old_tier} to {tier}")
        
        # Return updated subscription with success message
        response_serializer = SubscriptionSerializer(subscription)
        response_data = response_serializer.data
        response_data['message'] = f'구독이 성공적으로 {subscription.get_tier_display()}으로 {action_type}되었습니다!'
        response_data['ai_features'] = user.get_ai_features_list()
        response_data['ai_question_limit'] = user.get_ai_question_limit()
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)