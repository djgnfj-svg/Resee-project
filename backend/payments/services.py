import logging
import time
from decimal import Decimal
from typing import Optional, Tuple

import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.core.cache import cache
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Payment, PaymentPlan, Subscription, WebhookEvent

User = get_user_model()
logger = logging.getLogger(__name__)

# Stripe 초기화
stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentError(Exception):
    """결제 관련 커스텀 예외"""
    pass

class PaymentValidationError(PaymentError):
    """결제 검증 실패"""
    pass

class PaymentProcessingError(PaymentError):
    """결제 처리 실패"""
    pass

class DuplicatePaymentError(PaymentError):
    """중복 결제 시도"""
    pass

class InsufficientPermissionError(PaymentError):
    """권한 부족"""
    pass


class StripeService:
    """Stripe 결제 서비스 - 강화된 예외처리"""
    
    # 재시도 설정
    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 1  # seconds
    
    # 캐시 설정
    CUSTOMER_CACHE_TTL = 3600  # 1 hour
    PAYMENT_LOCK_TTL = 300  # 5 minutes
    
    @staticmethod
    def _retry_stripe_call(func, *args, **kwargs):
        """Stripe API 호출 재시도 로직"""
        last_error = None
        
        for attempt in range(StripeService.RETRY_ATTEMPTS):
            try:
                return func(*args, **kwargs)
                
            except stripe.error.RateLimitError as e:
                last_error = e
                wait_time = StripeService.RETRY_DELAY * (2 ** attempt)  # 지수 백오프
                logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1})")
                time.sleep(wait_time)
                
            except stripe.error.APIConnectionError as e:
                last_error = e
                wait_time = StripeService.RETRY_DELAY * (2 ** attempt)
                logger.warning(f"Connection error, retrying in {wait_time}s (attempt {attempt + 1})")
                time.sleep(wait_time)
                
            except (stripe.error.APIError, stripe.error.ServiceUnavailableError) as e:
                last_error = e
                if attempt < StripeService.RETRY_ATTEMPTS - 1:
                    wait_time = StripeService.RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"API error, retrying in {wait_time}s (attempt {attempt + 1})")
                    time.sleep(wait_time)
                else:
                    break
                    
            except stripe.error.StripeError as e:
                # 재시도하면 안 되는 에러들
                raise PaymentProcessingError(f"Stripe error: {str(e)}") from e
        
        # 모든 재시도 실패
        raise PaymentProcessingError(f"Max retries exceeded: {str(last_error)}") from last_error

    @staticmethod
    def _validate_user_can_pay(user) -> None:
        """사용자가 결제할 수 있는지 검증"""
        if not user.is_active:
            raise InsufficientPermissionError("비활성화된 사용자는 결제할 수 없습니다.")
            
        if not user.is_email_verified:
            raise PaymentValidationError("이메일 인증이 필요합니다.")
            
        # 최근 결제 실패가 많은 사용자 차단
        recent_failures = Payment.objects.filter(
            user=user,
            status=Payment.Status.FAILED,
            created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count()
        
        if recent_failures >= 5:
            raise PaymentValidationError("24시간 내 결제 실패가 너무 많습니다. 고객센터에 문의하세요.")

    @staticmethod
    def _acquire_payment_lock(user_id: int) -> bool:
        """사용자별 결제 잠금 획득"""
        lock_key = f"payment_lock_{user_id}"
        return cache.add(lock_key, "locked", timeout=StripeService.PAYMENT_LOCK_TTL)
    
    @staticmethod
    def _release_payment_lock(user_id: int) -> None:
        """사용자별 결제 잠금 해제"""
        lock_key = f"payment_lock_{user_id}"
        cache.delete(lock_key)

    @staticmethod
    @transaction.atomic
    def create_customer(user) -> stripe.Customer:
        """Stripe 고객 생성 - 강화된 예외처리"""
        StripeService._validate_user_can_pay(user)
        
        cache_key = f"stripe_customer_{user.id}"
        cached_customer = cache.get(cache_key)
        if cached_customer:
            return cached_customer
        
        try:
            def _create():
                return stripe.Customer.create(
                    email=user.email,
                    name=user.email.split('@')[0],
                    metadata={
                        'user_id': str(user.id),
                        'environment': getattr(settings, 'ENVIRONMENT', 'development'),
                        'created_at': timezone.now().isoformat()
                    }
                )
            
            customer = StripeService._retry_stripe_call(_create)
            
            # 성공적으로 생성된 고객 정보 캐싱
            cache.set(cache_key, customer, timeout=StripeService.CUSTOMER_CACHE_TTL)
            
            logger.info(f"Successfully created Stripe customer {customer.id} for user {user.email}")
            return customer
            
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid request creating customer for {user.email}: {e}")
            raise PaymentValidationError(f"고객 정보가 유효하지 않습니다: {str(e)}") from e
            
        except stripe.error.AuthenticationError as e:
            logger.critical(f"Authentication error creating customer: {e}")
            raise PaymentProcessingError("결제 시스템 인증 오류입니다. 관리자에게 문의하세요.") from e
            
        except Exception as e:
            logger.error(f"Unexpected error creating customer for {user.email}: {e}")
            raise PaymentProcessingError("고객 생성 중 예상치 못한 오류가 발생했습니다.") from e
    
    @staticmethod
    def create_payment_intent(user, plan, billing_cycle='monthly') -> Tuple[stripe.PaymentIntent, Payment]:
        """결제 의도 생성 - 트랜잭션 보장 및 동시성 제어"""
        # 동시 결제 방지를 위한 락 획득
        if not StripeService._acquire_payment_lock(user.id):
            raise DuplicatePaymentError("이미 진행 중인 결제가 있습니다. 잠시 후 다시 시도해주세요.")
        
        try:
            with transaction.atomic():
                # 사용자 검증
                StripeService._validate_user_can_pay(user)
                
                # 플랜 검증
                if not plan.is_active:
                    raise PaymentValidationError("비활성화된 플랜입니다.")
                
                # 가격 검증
                amount = plan.monthly_price if billing_cycle == 'monthly' else plan.yearly_price
                if amount <= 0:
                    raise PaymentValidationError("결제 금액이 유효하지 않습니다.")
                
                # 최대 결제 금액 제한 (보안)
                max_amount = Decimal('1000000')  # 100만원
                if amount > max_amount:
                    raise PaymentValidationError("결제 금액이 허용 한도를 초과했습니다.")
                
                # 기존 대기 중인 결제 확인
                existing_pending = Payment.objects.filter(
                    user=user,
                    status=Payment.Status.PENDING,
                    created_at__gte=timezone.now() - timezone.timedelta(minutes=30)
                ).exists()
                
                if existing_pending:
                    raise DuplicatePaymentError("대기 중인 결제가 있습니다.")
                
                # 고객 생성/조회 (캐시 활용)
                customer = StripeService.get_or_create_customer(user)
                
                # DB에 결제 기록 먼저 생성 (Stripe 실패 시 롤백을 위해)
                payment = Payment.objects.create(
                    user=user,
                    plan=plan,
                    amount=amount,
                    billing_cycle=billing_cycle,
                    stripe_payment_intent_id='',  # 임시값
                    status=Payment.Status.PENDING
                )
                
                try:
                    # Stripe 결제 의도 생성
                    def _create_intent():
                        return stripe.PaymentIntent.create(
                            amount=int(amount * 100),  # cents 단위로 변환
                            currency='krw',
                            customer=customer.id,
                            payment_method_types=['card'],
                            confirmation_method='manual',
                            confirm=False,  # 자동 확인 방지
                            metadata={
                                'user_id': str(user.id),
                                'user_email': user.email,
                                'plan_id': str(plan.id),
                                'plan_name': plan.name,
                                'billing_cycle': billing_cycle,
                                'environment': getattr(settings, 'ENVIRONMENT', 'development'),
                                'created_at': timezone.now().isoformat(),
                                'payment_db_id': str(payment.id)
                            }
                        )
                    
                    intent = StripeService._retry_stripe_call(_create_intent)
                    
                    # DB 업데이트
                    payment.stripe_payment_intent_id = intent.id
                    payment.save(update_fields=['stripe_payment_intent_id'])
                    
                    logger.info(
                        f"Payment intent created successfully: "
                        f"user={user.email}, plan={plan.name}, "
                        f"amount={amount}, intent_id={intent.id}"
                    )
                    
                    return intent, payment
                    
                except Exception as stripe_error:
                    # Stripe 실패 시 DB 결제 기록 삭제
                    payment.delete()
                    raise stripe_error
                    
        except stripe.error.CardError as e:
            logger.warning(f"Card error for user {user.email}: {e}")
            raise PaymentValidationError(f"카드 오류: {e.user_message or '카드를 확인해주세요.'}") from e
            
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid request for user {user.email}: {e}")
            raise PaymentValidationError(f"요청이 유효하지 않습니다: {str(e)}") from e
            
        except stripe.error.AuthenticationError as e:
            logger.critical(f"Authentication error: {e}")
            raise PaymentProcessingError("결제 시스템 인증 오류입니다.") from e
            
        except (DuplicatePaymentError, PaymentValidationError, InsufficientPermissionError):
            # 이미 적절한 메시지가 있는 예외들은 그대로 재발생
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error creating payment intent: {e}")
            raise PaymentProcessingError("결제 처리 중 예상치 못한 오류가 발생했습니다.") from e
            
        finally:
            # 항상 락 해제
            StripeService._release_payment_lock(user.id)
    
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
    def create_subscription(user, plan, billing_cycle='monthly') -> Tuple[stripe.Subscription, Subscription]:
        """구독 생성 - 트랜잭션 보장 및 데이터 일관성"""
        # 동시 구독 생성 방지
        if not StripeService._acquire_payment_lock(user.id):
            raise DuplicatePaymentError("이미 진행 중인 구독 생성 작업이 있습니다.")
        
        try:
            with transaction.atomic():
                # 사용자 검증
                StripeService._validate_user_can_pay(user)
                
                # 기존 활성 구독 확인 (DB 락으로 동시성 제어)
                existing_subscription = Subscription.objects.select_for_update().filter(
                    user=user, 
                    is_active=True
                ).first()
                
                if existing_subscription:
                    raise DuplicatePaymentError("이미 활성 구독이 있습니다.")
                
                # 플랜 검증
                if not plan.is_active:
                    raise PaymentValidationError("비활성화된 플랜입니다.")
                
                # 가격 ID 검증
                price_id = (plan.stripe_price_id_monthly 
                           if billing_cycle == 'monthly' 
                           else plan.stripe_price_id_yearly)
                
                if not price_id:
                    raise PaymentValidationError(f"{plan.name} 플랜의 {billing_cycle} 가격 정보가 없습니다.")
                
                # 고객 생성/조회
                customer = StripeService.get_or_create_customer(user)
                
                # 로컬 구독 기록 먼저 생성 (Stripe 실패 시 롤백)
                local_subscription = Subscription.objects.create(
                    user=user,
                    plan=plan,
                    stripe_subscription_id='',  # 임시값
                    stripe_customer_id=customer.id,
                    billing_cycle=billing_cycle,
                    current_period_start=timezone.now(),
                    current_period_end=timezone.now() + timezone.timedelta(days=30),  # 임시값
                    is_active=False  # Stripe 성공 후 활성화
                )
                
                try:
                    # Stripe 구독 생성
                    def _create_subscription():
                        return stripe.Subscription.create(
                            customer=customer.id,
                            items=[{'price': price_id}],
                            payment_behavior='default_incomplete',
                            payment_settings={
                                'save_default_payment_method': 'on_subscription',
                                'payment_method_types': ['card']
                            },
                            expand=['latest_invoice.payment_intent'],
                            trial_period_days=0,  # 무료 평가판 없음
                            metadata={
                                'user_id': str(user.id),
                                'user_email': user.email,
                                'plan_id': str(plan.id),
                                'plan_name': plan.name,
                                'billing_cycle': billing_cycle,
                                'environment': getattr(settings, 'ENVIRONMENT', 'development'),
                                'local_subscription_id': str(local_subscription.id)
                            }
                        )
                    
                    stripe_subscription = StripeService._retry_stripe_call(_create_subscription)
                    
                    # 로컬 구독 정보 업데이트
                    local_subscription.stripe_subscription_id = stripe_subscription.id
                    local_subscription.current_period_start = timezone.datetime.fromtimestamp(
                        stripe_subscription.current_period_start, tz=timezone.utc
                    )
                    local_subscription.current_period_end = timezone.datetime.fromtimestamp(
                        stripe_subscription.current_period_end, tz=timezone.utc
                    )
                    local_subscription.is_active = stripe_subscription.status in ['active', 'trialing']
                    
                    # 평가판 기간이 있다면
                    if stripe_subscription.trial_end:
                        local_subscription.trial_end = timezone.datetime.fromtimestamp(
                            stripe_subscription.trial_end, tz=timezone.utc
                        )
                    
                    local_subscription.save()
                    
                    logger.info(
                        f"Subscription created successfully: "
                        f"user={user.email}, plan={plan.name}, "
                        f"stripe_id={stripe_subscription.id}, status={stripe_subscription.status}"
                    )
                    
                    return stripe_subscription, local_subscription
                    
                except Exception as stripe_error:
                    # Stripe 실패 시 로컬 구독 삭제
                    local_subscription.delete()
                    raise stripe_error
                    
        except stripe.error.CardError as e:
            logger.warning(f"Card error creating subscription for {user.email}: {e}")
            raise PaymentValidationError(f"카드 오류: {e.user_message or '결제 정보를 확인해주세요.'}") from e
            
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid request creating subscription for {user.email}: {e}")
            raise PaymentValidationError(f"구독 요청이 유효하지 않습니다: {str(e)}") from e
            
        except (DuplicatePaymentError, PaymentValidationError, InsufficientPermissionError):
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error creating subscription for {user.email}: {e}")
            raise PaymentProcessingError("구독 생성 중 예상치 못한 오류가 발생했습니다.") from e
            
        finally:
            StripeService._release_payment_lock(user.id)
    
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


class CompensationHandler:
    """보상 트랜잭션 처리 - 실패한 작업 복구"""
    
    @staticmethod
    def cleanup_failed_payment(payment_id: int) -> None:
        """실패한 결제 정리"""
        try:
            with transaction.atomic():
                payment = Payment.objects.select_for_update().get(id=payment_id)
                
                if payment.stripe_payment_intent_id:
                    try:
                        # Stripe에서 결제 의도 취소
                        stripe.PaymentIntent.cancel(payment.stripe_payment_intent_id)
                        logger.info(f"Cancelled Stripe payment intent {payment.stripe_payment_intent_id}")
                    except stripe.error.StripeError as e:
                        logger.warning(f"Could not cancel Stripe payment intent: {e}")
                
                # 결제 상태 업데이트
                payment.status = Payment.Status.CANCELED
                payment.save()
                
                logger.info(f"Cleaned up failed payment {payment_id}")
                
        except Payment.DoesNotExist:
            logger.warning(f"Payment {payment_id} not found for cleanup")
        except Exception as e:
            logger.error(f"Error cleaning up payment {payment_id}: {e}")
    
    @staticmethod
    def cleanup_failed_subscription(subscription_id: int) -> None:
        """실패한 구독 정리"""
        try:
            with transaction.atomic():
                subscription = Subscription.objects.select_for_update().get(id=subscription_id)
                
                if subscription.stripe_subscription_id:
                    try:
                        # Stripe에서 구독 취소
                        stripe.Subscription.delete(subscription.stripe_subscription_id)
                        logger.info(f"Cancelled Stripe subscription {subscription.stripe_subscription_id}")
                    except stripe.error.StripeError as e:
                        logger.warning(f"Could not cancel Stripe subscription: {e}")
                
                # 구독 비활성화
                subscription.is_active = False
                subscription.canceled_at = timezone.now()
                subscription.save()
                
                logger.info(f"Cleaned up failed subscription {subscription_id}")
                
        except Subscription.DoesNotExist:
            logger.warning(f"Subscription {subscription_id} not found for cleanup")
        except Exception as e:
            logger.error(f"Error cleaning up subscription {subscription_id}: {e}")
    
    @staticmethod
    def sync_payment_status(payment_intent_id: str) -> None:
        """Stripe와 로컬 결제 상태 동기화"""
        try:
            with transaction.atomic():
                # Stripe에서 최신 상태 조회
                intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                
                # 로컬 결제 기록 조회
                payment = Payment.objects.select_for_update().get(
                    stripe_payment_intent_id=payment_intent_id
                )
                
                # 상태 매핑
                status_mapping = {
                    'succeeded': Payment.Status.SUCCEEDED,
                    'processing': Payment.Status.PENDING,
                    'requires_payment_method': Payment.Status.FAILED,
                    'requires_confirmation': Payment.Status.PENDING,
                    'requires_action': Payment.Status.PENDING,
                    'canceled': Payment.Status.CANCELED,
                    'requires_capture': Payment.Status.PENDING,
                }
                
                new_status = status_mapping.get(intent.status, Payment.Status.PENDING)
                
                if payment.status != new_status:
                    payment.status = new_status
                    if new_status == Payment.Status.SUCCEEDED:
                        payment.paid_at = timezone.now()
                    payment.save()
                    
                    logger.info(f"Synchronized payment {payment.id} status to {new_status}")
                
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for intent {payment_intent_id}")
        except Exception as e:
            logger.error(f"Error syncing payment status for {payment_intent_id}: {e}")


class WebhookHandler:
    """Stripe 웹훅 처리 - 강화된 오류 처리 및 재시도 로직"""
    
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    
    @staticmethod
    def handle_webhook(payload, sig_header) -> None:
        """웹훅 이벤트 처리 - 멱등성 보장"""
        # 웹훅 서명 검증
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            raise ValueError("Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise stripe.error.SignatureVerificationError("Invalid signature")
        
        # 이벤트 ID 검증
        if not event.get('id'):
            raise ValueError("Event ID missing")
        
        # 이벤트 중복 처리 방지 (트랜잭션으로 안전하게)
        try:
            with transaction.atomic():
                webhook_event, created = WebhookEvent.objects.get_or_create(
                    stripe_event_id=event['id'],
                    defaults={
                        'event_type': event['type'],
                        'processed': False
                    }
                )
                
                if not created:
                    if webhook_event.processed:
                        logger.info(f"Webhook event {event['id']} already processed successfully")
                        return
                    else:
                        # 이전 처리가 실패했다면 재시도
                        logger.info(f"Retrying failed webhook event {event['id']}")
        
        except IntegrityError:
            # 동시성 문제로 이미 생성된 경우
            logger.info(f"Webhook event {event['id']} already being processed")
            return
        
        # 이벤트 처리 (재시도 로직 포함)
        success = False
        last_error = None
        
        for attempt in range(WebhookHandler.MAX_RETRIES):
            try:
                with transaction.atomic():
                    WebhookHandler._process_event(event)
                    
                    # 성공 시 마킹
                    webhook_event.processed = True
                    webhook_event.error_message = ''
                    webhook_event.save()
                    
                    success = True
                    logger.info(f"Successfully processed webhook event {event['id']} on attempt {attempt + 1}")
                    break
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed for webhook {event['id']}: {e}")
                
                if attempt < WebhookHandler.MAX_RETRIES - 1:
                    time.sleep(WebhookHandler.RETRY_DELAY)
        
        if not success:
            # 모든 재시도 실패
            webhook_event.error_message = str(last_error)
            webhook_event.save()
            
            logger.error(f"Failed to process webhook {event['id']} after {WebhookHandler.MAX_RETRIES} attempts: {last_error}")
            
            # 중요한 이벤트는 알림 발송
            if event['type'] in ['payment_intent.succeeded', 'payment_intent.payment_failed']:
                WebhookHandler._send_failure_alert(event, last_error)
            
            raise Exception(f"Webhook processing failed: {last_error}")
    
    @staticmethod
    def _process_event(event) -> None:
        """이벤트 타입별 처리"""
        event_type = event['type']
        event_data = event['data']['object']
        
        # 지원하는 이벤트 타입 확인
        handlers = {
            'payment_intent.succeeded': WebhookHandler._handle_payment_succeeded,
            'payment_intent.payment_failed': WebhookHandler._handle_payment_failed,
            'payment_intent.canceled': WebhookHandler._handle_payment_canceled,
            'invoice.payment_succeeded': WebhookHandler._handle_invoice_payment_succeeded,
            'invoice.payment_failed': WebhookHandler._handle_invoice_payment_failed,
            'customer.subscription.created': WebhookHandler._handle_subscription_created,
            'customer.subscription.updated': WebhookHandler._handle_subscription_updated,
            'customer.subscription.deleted': WebhookHandler._handle_subscription_deleted,
            'customer.subscription.trial_will_end': WebhookHandler._handle_trial_will_end,
        }
        
        handler = handlers.get(event_type)
        if handler:
            handler(event_data)
            logger.info(f"Processed {event_type} event")
        else:
            logger.info(f"Unhandled event type: {event_type}")
    
    @staticmethod
    def _send_failure_alert(event, error) -> None:
        """웹훅 처리 실패 시 알림"""
        # 실제로는 Slack, 이메일 등으로 알림 발송
        logger.critical(
            f"URGENT: Webhook processing failed for critical event {event['id']} "
            f"({event['type']}): {error}"
        )
    
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