"""
Subscription-related views (simplified version)

Note: Payment system (upgrade/downgrade/cancel) not implemented yet.
Only tier information and current subscription details are provided.
"""
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Subscription
from ..utils.serializers import SubscriptionSerializer
from . import tier_utils


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_detail(request):
    """Get current user's subscription details."""
    subscription = get_object_or_404(Subscription, user=request.user)
    serializer = SubscriptionSerializer(subscription)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_tiers(request):
    """
    Get available subscription tiers with pricing information.

    Query parameters:
    - billing_cycle: 'monthly' or 'yearly' (default: 'monthly')
    """
    billing_cycle = request.query_params.get('billing_cycle', 'monthly')
    tiers_info = tier_utils.get_all_tiers_info(billing_cycle=billing_cycle)

    return Response({
        'tiers': tiers_info,
        'billing_cycle': billing_cycle
    })
