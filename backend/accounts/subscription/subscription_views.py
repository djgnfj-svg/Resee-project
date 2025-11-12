"""
Subscription-related views
"""
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Subscription, SubscriptionTier, PaymentHistory, BillingSchedule
from ..utils.serializers import (SubscriptionSerializer, SubscriptionTierSerializer,
                                SubscriptionUpgradeSerializer, PaymentHistorySerializer)
from .decorators import require_admin_password, require_user_password


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
@require_admin_password
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
            billing_cycle = request.data.get('billing_cycle', 'monthly')
            user = request.user
            logger.info(f"Step 1: Got tier={tier}, billing_cycle={billing_cycle}, user={user.email}")
            
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
            
            subscription.billing_cycle = billing_cycle
            logger.info(f"Step 5e: Set billing_cycle to {billing_cycle}")
            
            # Set subscription period based on billing cycle
            if billing_cycle == 'yearly':
                subscription.end_date = timezone.now() + timedelta(days=365)
            else:
                subscription.end_date = timezone.now() + timedelta(days=30)
            
            # Set next billing date for auto-renewal
            if subscription.auto_renewal:
                subscription.next_billing_date = subscription.end_date
                
            logger.info("Step 5e: Set end_date and next_billing_date")
            
            logger.info("Step 5f: About to call subscription.save()...")
            subscription.save()  # save() 메서드에서 max_interval_days가 자동 설정됨
            logger.info("Step 5f: subscription.save() completed")
            
            # Set payment amount based on tier and billing cycle
            if tier == SubscriptionTier.BASIC:
                monthly_price = 10000.0
                if billing_cycle == 'yearly':
                    subscription.amount_paid = monthly_price * 12 * 0.8  # 20% discount for yearly
                else:
                    subscription.amount_paid = monthly_price
            elif tier == SubscriptionTier.PRO:
                monthly_price = 25000.0
                if billing_cycle == 'yearly':
                    subscription.amount_paid = monthly_price * 12 * 0.8  # 20% discount for yearly
                else:
                    subscription.amount_paid = monthly_price
            else:
                subscription.amount_paid = 0
                
            # Set next billing amount for auto-renewal
            subscription.next_billing_amount = subscription.amount_paid
            subscription.save()
            
            # 업그레이드/다운그레이드 구분
            logger.info("Step 6: Determining upgrade/downgrade...")
            is_upgrade = new_tier_level > current_tier_level
            action_type = "업그레이드" if is_upgrade else "다운그레이드"
            logger.info(f"Step 6: is_upgrade={is_upgrade}, action_type={action_type}")
            
            # Create payment history record
            payment_type = PaymentHistory.PaymentType.UPGRADE if is_upgrade else PaymentHistory.PaymentType.DOWNGRADE
            if old_tier == SubscriptionTier.FREE and tier != SubscriptionTier.FREE:
                payment_type = PaymentHistory.PaymentType.INITIAL
                
            PaymentHistory.objects.create(
                user=user,
                payment_type=payment_type,
                from_tier=old_tier if old_tier != tier else None,
                to_tier=tier,
                amount=subscription.amount_paid,
                billing_cycle=billing_cycle,
                payment_method_used=subscription.payment_method,
                description=f"{action_type} 완료: {old_tier} → {tier}",
                notes=f"결제 주기: {billing_cycle}, 금액: {subscription.amount_paid}원"
            )
            
            # Billing schedule creation removed (payment system not active)
            logger.info("Step 7: Skipped billing schedule (FREE tier only)")
            
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
@require_admin_password
def subscription_downgrade(request):
    """Downgrade user's subscription with refund calculation"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Starting subscription downgrade for user: {request.user.email}")

        user = request.user
        subscription = getattr(user, 'subscription', None)

        if not subscription:
            logger.error(f"User {user.email} has no subscription")
            return Response({'error': '구독 정보를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # Get target tier and billing cycle from request
        target_tier = request.data.get('tier')
        billing_cycle = request.data.get('billing_cycle', 'monthly')
        
        if not target_tier:
            return Response({'error': '다운그레이드할 티어를 지정해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate tier hierarchy for downgrade
        tier_hierarchy = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.BASIC: 1,
            SubscriptionTier.PRO: 2,
        }
        
        current_tier_level = tier_hierarchy.get(subscription.tier, 0)
        target_tier_level = tier_hierarchy.get(target_tier, 0)
        
        if target_tier_level >= current_tier_level:
            return Response(
                {'error': '더 낮은 티어로만 다운그레이드할 수 있습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate refund amount (simple pro-rata calculation)
        refund_amount = 0
        if subscription.end_date and subscription.amount_paid:
            remaining_days = subscription.days_remaining() or 0
            total_days = 30  # Assuming monthly billing
            if remaining_days > 0:
                refund_amount = float(subscription.amount_paid) * (remaining_days / total_days)
        
        # Get new pricing
        tier_pricing = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.BASIC: 10000.0,
            SubscriptionTier.PRO: 25000.0,
        }
        
        new_amount = tier_pricing.get(target_tier, 0)
        
        # Update subscription
        from datetime import timedelta
        from django.utils import timezone
        
        old_tier = subscription.tier
        subscription.tier = target_tier
        subscription.is_active = True
        subscription.start_date = timezone.now()
        
        if target_tier == SubscriptionTier.FREE:
            subscription.end_date = None
            subscription.amount_paid = 0
            subscription.auto_renewal = False
            subscription.next_billing_date = None
        else:
            # Keep existing end date for paid downgrades
            subscription.amount_paid = new_amount
            if subscription.auto_renewal and subscription.end_date:
                subscription.next_billing_date = subscription.end_date
        
        subscription.save()
        
        # Create payment history record
        PaymentHistory.objects.create(
            user=user,
            payment_type=PaymentHistory.PaymentType.DOWNGRADE,
            from_tier=old_tier,
            to_tier=target_tier,
            amount=new_amount,
            refund_amount=refund_amount,
            billing_cycle=subscription.billing_cycle,
            payment_method_used=subscription.payment_method,
            description=f"다운그레이드: {old_tier} → {target_tier}",
            notes=f"환불금액: {refund_amount}원" if refund_amount > 0 else ""
        )
        
        # Update billing schedule for downgrade
        # Billing schedule update removed (payment system not active)
        logger.info("Skipped billing schedule update (FREE tier only)")
        
        logger.info(f"Subscription downgraded: {user.email} from {old_tier} to {target_tier}, refund: {refund_amount}")
        
        # Return updated subscription
        from ..utils.serializers import SubscriptionSerializer
        response_serializer = SubscriptionSerializer(subscription)
        response_data = response_serializer.data
        response_data['message'] = f'구독이 성공적으로 {subscription.get_tier_display()}으로 다운그레이드되었습니다!'
        
        if refund_amount > 0:
            response_data['refund_amount'] = refund_amount
            response_data['message'] += f' {refund_amount:.0f}원이 환불됩니다.'
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in subscription downgrade: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return Response(
            {'error': f'다운그레이드 중 오류가 발생했습니다: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_user_password
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
        
        # Create payment history record for cancellation
        PaymentHistory.objects.create(
            user=user,
            payment_type=PaymentHistory.PaymentType.CANCELLATION,
            from_tier=old_tier,
            to_tier=SubscriptionTier.FREE,
            amount=0,
            description=f"구독 취소: {old_tier} → FREE"
        )
        
        # Cancel all pending billing schedules
        # Billing schedule cancellation removed (payment system not active)
        logger.info("Skipped billing schedule cancellation (FREE tier only)")
        
        logger.info(f"Subscription cancelled: {user.email} from {old_tier} to FREE")
        
        # Return updated subscription
        from ..utils.serializers import SubscriptionSerializer
        response_serializer = SubscriptionSerializer(subscription)
        response_data = response_serializer.data
        response_data['message'] = '구독이 성공적으로 취소되었습니다. 무료 플랜으로 변경되었습니다.'
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in subscription cancel: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({'error': f'구독 취소 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_auto_renewal(request):
    """Toggle auto-renewal setting for user's subscription"""
    try:
        user = request.user
        subscription = getattr(user, 'subscription', None)
        
        if not subscription:
            return Response({'error': '구독 정보를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        if subscription.tier == SubscriptionTier.FREE:
            return Response({'error': '무료 플랜은 자동갱신 설정이 필요하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Toggle auto-renewal
        subscription.auto_renewal = not subscription.auto_renewal
        
        # Update next_billing_date based on auto_renewal status
        if subscription.auto_renewal and subscription.end_date:
            subscription.next_billing_date = subscription.end_date
        else:
            subscription.next_billing_date = None
            
        subscription.save()
        
        # Log the change
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Auto-renewal {'enabled' if subscription.auto_renewal else 'disabled'} for {user.email}")
        
        # Return updated subscription
        from ..utils.serializers import SubscriptionSerializer
        serializer = SubscriptionSerializer(subscription)
        response_data = serializer.data
        response_data['message'] = f"자동갱신이 {'활성화' if subscription.auto_renewal else '비활성화'}되었습니다."
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in toggle auto renewal: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({'error': '자동갱신 설정 변경 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== RESTful ViewSet ====================

class SubscriptionViewSet(viewsets.GenericViewSet):
    """
    RESTful Subscription ViewSet

    Endpoints:
    - PATCH /subscriptions/me - Update subscription (upgrade/downgrade/toggle auto-renewal)
    - DELETE /subscriptions/me - Cancel subscription (downgrade to FREE)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionSerializer

    @action(detail=False, methods=['patch', 'delete'], url_path='me')
    def me(self, request):
        """
        PATCH /subscriptions/me - Update subscription
        DELETE /subscriptions/me - Cancel subscription

        PATCH Handles:
        - Upgrade: {"tier": "BASIC"} or {"tier": "PRO"}
        - Downgrade: {"tier": "FREE"} or {"tier": "BASIC"}
        - Toggle auto-renewal: {"auto_renewal": true/false}

        Request body:
            - tier (optional): Target subscription tier
            - auto_renewal (optional): Auto-renewal status
            - password (required): Admin password or user password
            - billing_cycle (optional): MONTHLY or YEARLY
        """
        import logging
        logger = logging.getLogger(__name__)

        user = request.user
        subscription = getattr(user, 'subscription', None)

        if not subscription:
            return Response(
                {'error': '구독 정보를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Handle DELETE request (subscription cancellation)
        if request.method == 'DELETE':
            if subscription.tier == SubscriptionTier.FREE:
                return Response(
                    {'error': '이미 무료 플랜을 사용중입니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify password
            password = request.data.get('password')
            if not password:
                return Response(
                    {'error': '비밀번호를 입력해주세요.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not user.check_password(password):
                return Response(
                    {'error': '비밀번호가 올바르지 않습니다.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Cancel subscription by downgrading to FREE
            from datetime import timedelta
            from django.utils import timezone

            old_tier = subscription.tier
            subscription.tier = SubscriptionTier.FREE
            subscription.is_active = True  # FREE tier is always active
            subscription.start_date = timezone.now()
            subscription.end_date = None  # FREE tier has no end date
            subscription.amount_paid = 0.0
            subscription.save()

            # Create payment history record
            PaymentHistory.objects.create(
                user=user,
                transaction_type='cancellation',
                amount=-subscription.amount_paid if hasattr(subscription, 'amount_paid') else 0,
                tier=SubscriptionTier.FREE,
                description=f'구독 취소: {old_tier} → free'
            )

            logger.info(f"Subscription cancelled for {user.email}: {old_tier} → FREE")

            # Return updated subscription
            serializer = SubscriptionSerializer(subscription)
            response_data = serializer.data
            response_data['message'] = '구독이 취소되었습니다. 무료 플랜으로 변경되었습니다.'

            return Response(response_data, status=status.HTTP_200_OK)

        # Handle PATCH request (subscription update)
        # Get request data
        target_tier = request.data.get('tier')
        auto_renewal = request.data.get('auto_renewal')
        password = request.data.get('password')
        billing_cycle = request.data.get('billing_cycle', 'monthly')

        # At least one field must be provided
        if target_tier is None and auto_renewal is None:
            return Response(
                {'error': 'tier 또는 auto_renewal 중 하나는 필수입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Password verification
        if not password:
            return Response(
                {'error': '비밀번호를 입력해주세요.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Handle tier change (upgrade/downgrade)
        if target_tier is not None:
            # Verify admin password for tier changes
            admin_password = getattr(settings, 'SUBSCRIPTION_ADMIN_PASSWORD', None)
            if not admin_password:
                return Response(
                    {'error': '구독 변경이 일시적으로 비활성화되었습니다.'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            if password != admin_password:
                return Response(
                    {'error': '비밀번호가 올바르지 않습니다.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Delegate to upgrade/downgrade logic
            tier_hierarchy = {
                SubscriptionTier.FREE: 0,
                SubscriptionTier.BASIC: 1,
                SubscriptionTier.PRO: 2,
            }

            current_level = tier_hierarchy.get(subscription.tier, 0)
            target_level = tier_hierarchy.get(target_tier, 0)

            if target_level == current_level:
                return Response(
                    {'error': f'이미 {subscription.get_tier_display()} 티어입니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create request data for existing views
            data = {'tier': target_tier, 'password': password, 'billing_cycle': billing_cycle}
            request._full_data = data

            if target_level > current_level:
                # Upgrade
                return subscription_upgrade(request)
            else:
                # Downgrade
                return subscription_downgrade(request)

        # Handle auto-renewal toggle only
        if auto_renewal is not None:
            # Verify user password for auto-renewal changes
            if not user.check_password(password):
                return Response(
                    {'error': '비밀번호가 올바르지 않습니다.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            if subscription.tier == SubscriptionTier.FREE:
                return Response(
                    {'error': '무료 플랜은 자동갱신 설정이 필요하지 않습니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update auto-renewal
            subscription.auto_renewal = auto_renewal

            # Update next_billing_date
            if subscription.auto_renewal and subscription.end_date:
                subscription.next_billing_date = subscription.end_date
            else:
                subscription.next_billing_date = None

            subscription.save()

            logger.info(f"Auto-renewal {'enabled' if auto_renewal else 'disabled'} for {user.email}")

            # Return updated subscription
            serializer = SubscriptionSerializer(subscription)
            response_data = serializer.data
            response_data['message'] = f"자동갱신이 {'활성화' if auto_renewal else '비활성화'}되었습니다."

            return Response(response_data, status=status.HTTP_200_OK)