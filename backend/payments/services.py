import logging
from decimal import Decimal

import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Payment, PaymentPlan, Subscription, WebhookEvent

User = get_user_model()
logger = logging.getLogger(__name__)

# Stripe 초기화
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Stripe 결제 서비스"""
    
    @staticmethod
    def create_customer(user):
        """Stripe 고객 생성"""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.email.split('@')[0],
                metadata={
                    'user_id': user.id,
                    'environment': settings.ENVIRONMENT
                }
            )
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer for {user.email}: {e}")
            raise
    
    @staticmethod
    def create_payment_intent(user, plan, billing_cycle='monthly'):
        """결제 의도 생성"""
        try:
            # 가격 계산
            amount = plan.monthly_price if billing_cycle == 'monthly' else plan.yearly_price
            
            # 고객 생성 또는 가져오기
            customer = StripeService.get_or_create_customer(user)
            
            # 결제 의도 생성
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # cents 단위
                currency='krw',
                customer=customer.id,
                metadata={
                    'user_id': user.id,
                    'plan_id': plan.id,
                    'billing_cycle': billing_cycle,
                    'environment': settings.ENVIRONMENT
                }
            )
            
            # 결제 기록 생성
            payment = Payment.objects.create(
                user=user,
                plan=plan,
                amount=amount,
                billing_cycle=billing_cycle,
                stripe_payment_intent_id=intent.id,
                status=Payment.Status.PENDING
            )
            
            return intent, payment
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment intent for {user.email}: {e}")
            raise
    
    @staticmethod
    def get_or_create_customer(user):
        """고객 가져오기 또는 생성"""
        # 기존 구독에서 customer_id 확인
        subscription = getattr(user, 'subscription_payment', None)
        if subscription and subscription.stripe_customer_id:
            try:
                customer = stripe.Customer.retrieve(subscription.stripe_customer_id)
                return customer
            except stripe.error.StripeError:
                pass
        
        # 새 고객 생성
        return StripeService.create_customer(user)
    
    @staticmethod
    def create_subscription(user, plan, billing_cycle='monthly'):
        """구독 생성"""
        try:
            customer = StripeService.get_or_create_customer(user)
            
            # 가격 ID 선택
            price_id = (plan.stripe_price_id_monthly 
                       if billing_cycle == 'monthly' 
                       else plan.stripe_price_id_yearly)
            
            if not price_id:
                raise ValueError(f"Price ID not found for plan {plan.name} ({billing_cycle})")
            
            # Stripe 구독 생성
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{'price': price_id}],
                payment_behavior='default_incomplete',
                payment_settings={'save_default_payment_method': 'on_subscription'},
                expand=['latest_invoice.payment_intent'],
                metadata={
                    'user_id': user.id,
                    'plan_id': plan.id,
                    'environment': settings.ENVIRONMENT
                }
            )
            
            # 로컬 구독 기록 생성
            local_subscription, created = Subscription.objects.update_or_create(
                user=user,
                defaults={
                    'plan': plan,
                    'stripe_subscription_id': subscription.id,
                    'stripe_customer_id': customer.id,
                    'billing_cycle': billing_cycle,
                    'current_period_start': timezone.datetime.fromtimestamp(
                        subscription.current_period_start, tz=timezone.utc
                    ),
                    'current_period_end': timezone.datetime.fromtimestamp(
                        subscription.current_period_end, tz=timezone.utc
                    ),
                    'is_active': subscription.status == 'active'
                }
            )
            
            return subscription, local_subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription for {user.email}: {e}")
            raise
    
    @staticmethod
    def cancel_subscription(user, immediately=False):
        """구독 취소"""
        try:
            subscription = getattr(user, 'subscription_payment', None)
            if not subscription or not subscription.stripe_subscription_id:
                raise ValueError("No active subscription found")
            
            if immediately:
                # 즉시 취소
                stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.is_active = False
                subscription.canceled_at = timezone.now()
            else:
                # 기간 종료 시 취소
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                subscription.canceled_at = subscription.current_period_end
            
            subscription.save()
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription for {user.email}: {e}")
            raise
    
    @staticmethod
    def update_subscription_plan(user, new_plan, billing_cycle='monthly'):
        """구독 플랜 변경"""
        try:
            subscription = getattr(user, 'subscription_payment', None)
            if not subscription or not subscription.stripe_subscription_id:
                raise ValueError("No active subscription found")
            
            # 새 가격 ID
            new_price_id = (new_plan.stripe_price_id_monthly 
                           if billing_cycle == 'monthly' 
                           else new_plan.stripe_price_id_yearly)
            
            if not new_price_id:
                raise ValueError(f"Price ID not found for plan {new_plan.name}")
            
            # Stripe 구독 업데이트
            stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{
                    'id': stripe_subscription['items']['data'][0].id,
                    'price': new_price_id,
                }],
                proration_behavior='create_prorations'
            )
            
            # 로컬 구독 업데이트
            subscription.plan = new_plan
            subscription.billing_cycle = billing_cycle
            subscription.save()
            
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update subscription for {user.email}: {e}")
            raise


class WebhookHandler:
    """Stripe 웹훅 처리"""
    
    @staticmethod
    def handle_webhook(payload, sig_header):
        """웹훅 이벤트 처리"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            logger.error("Invalid payload")
            raise
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid signature")
            raise
        
        # 이벤트 중복 처리 방지
        webhook_event, created = WebhookEvent.objects.get_or_create(
            stripe_event_id=event['id'],
            defaults={
                'event_type': event['type'],
                'processed': False
            }
        )
        
        if not created and webhook_event.processed:
            logger.info(f"Event {event['id']} already processed")
            return
        
        try:
            # 이벤트 타입별 처리
            if event['type'] == 'payment_intent.succeeded':
                WebhookHandler._handle_payment_succeeded(event['data']['object'])
            elif event['type'] == 'payment_intent.payment_failed':
                WebhookHandler._handle_payment_failed(event['data']['object'])
            elif event['type'] == 'invoice.payment_succeeded':
                WebhookHandler._handle_invoice_payment_succeeded(event['data']['object'])
            elif event['type'] == 'customer.subscription.updated':
                WebhookHandler._handle_subscription_updated(event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                WebhookHandler._handle_subscription_deleted(event['data']['object'])
            
            webhook_event.processed = True
            webhook_event.save()
            
        except Exception as e:
            logger.error(f"Error processing webhook {event['id']}: {e}")
            webhook_event.error_message = str(e)
            webhook_event.save()
            raise
    
    @staticmethod
    def _handle_payment_succeeded(payment_intent):
        """결제 성공 처리"""
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent['id'])
            payment.status = Payment.Status.SUCCEEDED
            payment.paid_at = timezone.now()
            payment.save()
            
            logger.info(f"Payment succeeded for user {payment.user.email}")
            
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for intent {payment_intent['id']}")
    
    @staticmethod
    def _handle_payment_failed(payment_intent):
        """결제 실패 처리"""
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent['id'])
            payment.status = Payment.Status.FAILED
            payment.failure_reason = payment_intent.get('last_payment_error', {}).get('message', '')
            payment.save()
            
            logger.warning(f"Payment failed for user {payment.user.email}: {payment.failure_reason}")
            
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for intent {payment_intent['id']}")
    
    @staticmethod
    def _handle_invoice_payment_succeeded(invoice):
        """구독 결제 성공 처리"""
        subscription_id = invoice['subscription']
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
            subscription.is_active = True
            subscription.current_period_start = timezone.datetime.fromtimestamp(
                invoice['period_start'], tz=timezone.utc
            )
            subscription.current_period_end = timezone.datetime.fromtimestamp(
                invoice['period_end'], tz=timezone.utc
            )
            subscription.save()
            
            logger.info(f"Subscription renewed for user {subscription.user.email}")
            
        except Subscription.DoesNotExist:
            logger.error(f"Subscription not found for {subscription_id}")
    
    @staticmethod
    def _handle_subscription_updated(subscription_data):
        """구독 업데이트 처리"""
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=subscription_data['id']
            )
            subscription.is_active = subscription_data['status'] == 'active'
            subscription.current_period_start = timezone.datetime.fromtimestamp(
                subscription_data['current_period_start'], tz=timezone.utc
            )
            subscription.current_period_end = timezone.datetime.fromtimestamp(
                subscription_data['current_period_end'], tz=timezone.utc
            )
            subscription.save()
            
            logger.info(f"Subscription updated for user {subscription.user.email}")
            
        except Subscription.DoesNotExist:
            logger.error(f"Subscription not found for {subscription_data['id']}")
    
    @staticmethod
    def _handle_subscription_deleted(subscription_data):
        """구독 삭제 처리"""
        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=subscription_data['id']
            )
            subscription.is_active = False
            subscription.canceled_at = timezone.now()
            subscription.save()
            
            logger.info(f"Subscription canceled for user {subscription.user.email}")
            
        except Subscription.DoesNotExist:
            logger.error(f"Subscription not found for {subscription_data['id']}")