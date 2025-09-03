"""
Subscription-related views
"""
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Subscription, SubscriptionTier
from .serializers import (SubscriptionSerializer, SubscriptionTierSerializer,
                          SubscriptionUpgradeSerializer)


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
                '최대 90일까지 복습 지원',
                '향상된 통계 기능',
                '우선 지원',
                'AI 기능 사용 가능'
            ]
        },
        SubscriptionTier.PRO: {
            'price': 20000,
            'features': [
                '최대 180일까지 복습 지원',
                '모든 고급 기능',
                '팀 협업 기능',
                '우선 고객 지원',
                '커스텀 복습 주기'
            ]
        }
    }
    
    # Ebbinghaus-optimized maximum intervals
    tier_max_days = {
        SubscriptionTier.FREE: 3,
        SubscriptionTier.BASIC: 90,
        SubscriptionTier.PRO: 180
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
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting subscription upgrade for user: {request.user.email}")
        
        # Check user and subscription first
        user = request.user
        logger.info(f"User: {user}, has subscription: {hasattr(user, 'subscription')}")
        
        if not hasattr(user, 'subscription'):
            logger.error(f"User {user.email} has no subscription attribute")
            return Response({'error': 'User subscription not found'}, status=status.HTTP_400_BAD_REQUEST)
            
        subscription = user.subscription
        logger.info(f"Current subscription: {subscription}, tier: {subscription.tier}")
        
        serializer = SubscriptionUpgradeSerializer(
            data=request.data,
            context={'request': request}
        )
        
        # 환경변수로 이메일 인증 강제 여부 제어
        if getattr(settings, 'ENFORCE_EMAIL_VERIFICATION', True) and not request.user.is_email_verified:
            return Response(
                {
                    'error': '이메일 인증이 필요합니다.',
                    'email_verified': False
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        logger.info("Email verification passed")
        
        if serializer.is_valid():
            logger.info(f"Serializer is valid, validated data: {serializer.validated_data}")
        else:
            logger.error(f"Serializer validation failed: {serializer.errors}")
            
    except Exception as e:
        logger.error(f"Error in subscription upgrade view: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({'error': f'Internal error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    if serializer.is_valid():
        logger.info("=== Starting subscription upgrade process ===")
        
        try:
            tier = serializer.validated_data['tier']
            user = request.user
            logger.info(f"Step 1: Got tier={tier}, user={user.email}")
            
            # Get or create subscription
            logger.info("Step 2: Getting subscription...")
            subscription = getattr(user, 'subscription', None)
            logger.info(f"Step 2: subscription={subscription}")
            
            if not subscription:
                logger.info("Step 2b: Creating new subscription...")
                from datetime import timedelta

                from django.utils import timezone
                subscription = Subscription.objects.create(
                    user=user,
                    tier=SubscriptionTier.FREE
                )
                logger.info(f"Step 2b: Created subscription={subscription}")
            
            # 티어 순서 확인
            logger.info("Step 3: Checking tier hierarchy...")
            tier_hierarchy = {
                SubscriptionTier.FREE: 0,
                SubscriptionTier.BASIC: 1,
                SubscriptionTier.PRO: 2,
            }
            
            current_tier_level = tier_hierarchy.get(subscription.tier, 0)
            new_tier_level = tier_hierarchy.get(tier, 0)
            logger.info(f"Step 3: current_tier_level={current_tier_level}, new_tier_level={new_tier_level}")
            
            # 동일한 티어로의 변경 방지
            if new_tier_level == current_tier_level:
                logger.info("Step 4: Same tier, returning error")
                return Response(
                    {'error': f'이미 {subscription.get_tier_display()} 티어입니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update subscription
            logger.info("Step 5: Updating subscription...")
            from datetime import timedelta

            from django.utils import timezone
            
            old_tier = subscription.tier
            logger.info(f"Step 5a: old_tier={old_tier}")
            
            subscription.tier = tier
            logger.info(f"Step 5b: Set tier to {tier}")
            
            subscription.is_active = True
            logger.info("Step 5c: Set is_active=True")
            
            subscription.start_date = timezone.now()
            logger.info("Step 5d: Set start_date")
            
            # 개발용으로 30일 구독 기간 설정
            subscription.end_date = timezone.now() + timedelta(days=30)
            logger.info("Step 5e: Set end_date")
            
            logger.info("Step 5f: About to call subscription.save()...")
            subscription.save()  # save() 메서드에서 max_interval_days가 자동 설정됨
            logger.info("Step 5f: subscription.save() completed")
            
            # 업그레이드/다운그레이드 구분
            logger.info("Step 6: Determining upgrade/downgrade...")
            is_upgrade = new_tier_level > current_tier_level
            action_type = "업그레이드" if is_upgrade else "다운그레이드"
            logger.info(f"Step 6: is_upgrade={is_upgrade}, action_type={action_type}")
            
            logger.info(f"Subscription {action_type}: {user.email} from {old_tier} to {tier}")
            
        except Exception as e:
            logger.error(f"Error in subscription upgrade main process: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return Response({'error': f'Subscription update failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Return updated subscription with success message
        try:
            response_serializer = SubscriptionSerializer(subscription)
            response_data = response_serializer.data
            response_data['message'] = f'구독이 성공적으로 {subscription.get_tier_display()}으로 {action_type}되었습니다!'
            
            # Add AI features and limits safely
            try:
                response_data['ai_features'] = user.get_ai_features_list()
                response_data['ai_question_limit'] = user.get_ai_question_limit()
            except AttributeError as e:
                logger.error(f"AttributeError getting AI info: {e}")
                response_data['ai_features'] = []
                response_data['ai_question_limit'] = 0
                
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Unexpected error in subscription upgrade response: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Fallback response
            return Response({
                'message': '구독이 성공적으로 업데이트되었습니다.',
                'tier': tier,
                'ai_features': [],
                'ai_question_limit': 0
            }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subscription_cancel(request):
    """Cancel user's subscription (downgrade to FREE)"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        user = request.user
        logger.info(f"Starting subscription cancellation for user: {user.email}")
        
        # Get user's subscription
        subscription = getattr(user, 'subscription', None)
        if not subscription:
            logger.error(f"User {user.email} has no subscription")
            return Response({'error': '구독 정보를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if already FREE tier
        if subscription.tier == SubscriptionTier.FREE:
            logger.info(f"User {user.email} is already on FREE tier")
            return Response({'error': '이미 무료 플랜을 사용중입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Cancel subscription by downgrading to FREE
        from datetime import timedelta
        from django.utils import timezone
        
        old_tier = subscription.tier
        subscription.tier = SubscriptionTier.FREE
        subscription.is_active = True  # FREE tier is always active
        subscription.start_date = timezone.now()
        subscription.end_date = None  # FREE tier has no end date
        
        # Clear payment amount for free tier
        subscription.amount_paid = 0.0
        subscription.save()
        
        logger.info(f"Subscription cancelled: {user.email} from {old_tier} to FREE")
        
        # Return updated subscription
        from .serializers import SubscriptionSerializer
        response_serializer = SubscriptionSerializer(subscription)
        response_data = response_serializer.data
        response_data['message'] = '구독이 성공적으로 취소되었습니다. 무료 플랜으로 변경되었습니다.'
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in subscription cancel: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({'error': f'구독 취소 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)