import logging

import stripe
from django.conf import settings
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment, PaymentPlan, Subscription
from .serializers import (CreatePaymentIntentSerializer,
                          CreateSubscriptionSerializer, PaymentPlanSerializer,
                          PaymentSerializer, SubscriptionSerializer,
                          UpdateSubscriptionSerializer)
from .services import (
    StripeService, WebhookHandler, CompensationHandler,
    PaymentError, PaymentValidationError, PaymentProcessingError,
    DuplicatePaymentError, InsufficientPermissionError
)

logger = logging.getLogger(__name__)


class PaymentPlanListView(generics.ListAPIView):
    """결제 플랜 목록 조회"""
    serializer_class = PaymentPlanSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return PaymentPlan.objects.filter(is_active=True).order_by('tier')


class CreatePaymentIntentView(APIView):
    """결제 의도 생성 API - 강화된 예외처리"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # 입력 데이터 검증
        serializer = CreatePaymentIntentSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Invalid payment intent request from {request.user.email}: {serializer.errors}")
            return Response({
                'error': '입력 데이터가 유효하지 않습니다.',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 플랜 조회 (존재하지 않으면 404 에러)
            try:
                plan = PaymentPlan.objects.get(id=serializer.validated_data['plan_id'])
            except PaymentPlan.DoesNotExist:
                return Response({
                    'error': '존재하지 않는 결제 플랜입니다.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            billing_cycle = serializer.validated_data['billing_cycle']
            
            # 결제 의도 생성
            intent, payment = StripeService.create_payment_intent(
                user=request.user,
                plan=plan,
                billing_cycle=billing_cycle
            )
            
            # 성공 응답
            response_data = {
                'client_secret': intent.client_secret,
                'payment_id': payment.id,
                'amount': str(payment.amount),
                'currency': payment.currency,
                'plan_name': plan.name,
                'billing_cycle': billing_cycle
            }
            
            logger.info(f"Payment intent created: user={request.user.email}, plan={plan.name}, amount={payment.amount}")
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except DuplicatePaymentError as e:
            logger.warning(f"Duplicate payment attempt: {request.user.email}")
            return Response({
                'error': str(e),
                'error_code': 'DUPLICATE_PAYMENT'
            }, status=status.HTTP_409_CONFLICT)
            
        except PaymentValidationError as e:
            logger.warning(f"Payment validation error: {request.user.email} - {e}")
            return Response({
                'error': str(e),
                'error_code': 'VALIDATION_ERROR'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except InsufficientPermissionError as e:
            logger.warning(f"Insufficient permission: {request.user.email} - {e}")
            return Response({
                'error': str(e),
                'error_code': 'PERMISSION_DENIED'
            }, status=status.HTTP_403_FORBIDDEN)
            
        except PaymentProcessingError as e:
            logger.error(f"Payment processing error: {request.user.email} - {e}")
            return Response({
                'error': str(e),
                'error_code': 'PROCESSING_ERROR'
            }, status=status.HTTP_502_BAD_GATEWAY)
            
        except Exception as e:
            # 예상치 못한 오류 - 로그와 함께 일반적인 메시지 반환
            logger.error(f"Unexpected error in CreatePaymentIntentView: {request.user.email} - {e}", exc_info=True)
            return Response({
                'error': '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateSubscriptionView(APIView):
    """구독 생성 API"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CreateSubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                plan = PaymentPlan.objects.get(id=serializer.validated_data['plan_id'])
                billing_cycle = serializer.validated_data['billing_cycle']
                
                # 기존 구독 확인
                existing_subscription = getattr(request.user, 'subscription_payment', None)
                if existing_subscription and existing_subscription.is_active:
                    return Response(
                        {'error': '이미 활성 구독이 있습니다.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                stripe_subscription, local_subscription = StripeService.create_subscription(
                    user=request.user,
                    plan=plan,
                    billing_cycle=billing_cycle
                )
                
                return Response({
                    'subscription_id': local_subscription.id,
                    'client_secret': stripe_subscription.latest_invoice.payment_intent.client_secret,
                    'status': stripe_subscription.status
                })
                
            except Exception as e:
                logger.error(f"Subscription creation failed: {e}")
                return Response(
                    {'error': '구독 생성 중 오류가 발생했습니다.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionDetailView(generics.RetrieveAPIView):
    """사용자 구독 정보 조회"""
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        try:
            return self.request.user.subscription_payment
        except Subscription.DoesNotExist:
            return None
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response({'message': '구독 정보가 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class UpdateSubscriptionView(APIView):
    """구독 플랜 변경 API"""
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        serializer = UpdateSubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                new_plan = PaymentPlan.objects.get(id=serializer.validated_data['plan_id'])
                billing_cycle = serializer.validated_data['billing_cycle']
                
                subscription = StripeService.update_subscription_plan(
                    user=request.user,
                    new_plan=new_plan,
                    billing_cycle=billing_cycle
                )
                
                serializer = SubscriptionSerializer(subscription)
                return Response(serializer.data)
                
            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                logger.error(f"Subscription update failed: {e}")
                return Response(
                    {'error': '구독 변경 중 오류가 발생했습니다.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CancelSubscriptionView(APIView):
    """구독 취소 API"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        immediately = request.data.get('immediately', False)
        
        try:
            subscription = StripeService.cancel_subscription(
                user=request.user,
                immediately=immediately
            )
            
            serializer = SubscriptionSerializer(subscription)
            return Response(serializer.data)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Subscription cancellation failed: {e}")
            return Response(
                {'error': '구독 취소 중 오류가 발생했습니다.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentHistoryView(generics.ListAPIView):
    """사용자 결제 기록 조회"""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).order_by('-created_at')


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Stripe 웹훅 엔드포인트"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        WebhookHandler.handle_webhook(payload, sig_header)
        return HttpResponse(status=200)
    except Exception as e:
        logger.error(f"Webhook handling failed: {e}")
        return HttpResponse(status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_status(request):
    """구독 상태 확인 API"""
    try:
        subscription = request.user.subscription_payment
        return Response({
            'has_subscription': True,
            'is_active': subscription.is_active,
            'plan_tier': subscription.plan.tier,
            'billing_cycle': subscription.billing_cycle,
            'current_period_end': subscription.current_period_end,
            'is_expired': subscription.is_expired(),
            'days_until_renewal': subscription.days_until_renewal()
        })
    except Subscription.DoesNotExist:
        return Response({
            'has_subscription': False,
            'is_active': False,
            'plan_tier': 'free'
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def preview_subscription_change(request):
    """구독 변경 미리보기 API"""
    serializer = UpdateSubscriptionSerializer(data=request.data)
    if serializer.is_valid():
        try:
            new_plan = PaymentPlan.objects.get(id=serializer.validated_data['plan_id'])
            billing_cycle = serializer.validated_data['billing_cycle']
            
            # 현재 구독 정보
            current_subscription = request.user.subscription_payment
            current_amount = (current_subscription.plan.monthly_price 
                            if current_subscription.billing_cycle == 'monthly' 
                            else current_subscription.plan.yearly_price)
            
            # 새 플랜 정보
            new_amount = (new_plan.monthly_price 
                         if billing_cycle == 'monthly' 
                         else new_plan.yearly_price)
            
            # 비용 차이 계산
            price_difference = new_amount - current_amount
            
            return Response({
                'current_plan': current_subscription.plan.name,
                'new_plan': new_plan.name,
                'current_amount': current_amount,
                'new_amount': new_amount,
                'price_difference': price_difference,
                'is_upgrade': price_difference > 0,
                'effective_date': current_subscription.current_period_end if price_difference > 0 else 'immediately'
            })
            
        except PaymentPlan.DoesNotExist:
            return Response(
                {'error': '유효하지 않은 플랜입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Subscription.DoesNotExist:
            return Response(
                {'error': '구독 정보가 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)