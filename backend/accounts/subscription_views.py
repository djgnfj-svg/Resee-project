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
        subscription = request.user.subscription
        
        # Check if already at PRO tier
        if subscription.tier == SubscriptionTier.PRO and tier == SubscriptionTier.PRO:
            return Response(
                {'error': 'Already at highest subscription tier.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update subscription
        subscription.tier = tier
        subscription.save()
        
        # Return updated subscription
        response_serializer = SubscriptionSerializer(subscription)
        return Response(response_serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)