"""
결제 상태 동기화 관리 명령어
Stripe와 로컬 DB의 결제/구독 상태를 동기화합니다.
"""

import logging
from datetime import timedelta

import stripe
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from payments.models import Payment, Subscription
from payments.services import CompensationHandler

logger = logging.getLogger(__name__)

# Stripe 초기화
stripe.api_key = settings.STRIPE_SECRET_KEY


class Command(BaseCommand):
    help = '결제 및 구독 상태를 Stripe와 동기화합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='몇 일 전까지의 데이터를 확인할지 (기본값: 7)'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='불일치 발견 시 자동으로 수정 (기본값: 확인만)'
        )
        parser.add_argument(
            '--payment-only',
            action='store_true',
            help='결제만 확인 (구독 제외)'
        )
        parser.add_argument(
            '--subscription-only',
            action='store_true',
            help='구독만 확인 (결제 제외)'
        )

    def handle(self, *args, **options):
        days = options['days']
        should_fix = options['fix']
        payment_only = options['payment_only']
        subscription_only = options['subscription_only']

        self.stdout.write(f"결제/구독 상태 동기화 시작 (최근 {days}일)")
        self.stdout.write(f"자동 수정: {'ON' if should_fix else 'OFF'}")

        cutoff_date = timezone.now() - timedelta(days=days)

        # 결제 상태 확인
        if not subscription_only:
            self.sync_payments(cutoff_date, should_fix)

        # 구독 상태 확인
        if not payment_only:
            self.sync_subscriptions(cutoff_date, should_fix)

        self.stdout.write(self.style.SUCCESS('동기화 완료!'))

    def sync_payments(self, cutoff_date, should_fix):
        """결제 상태 동기화"""
        self.stdout.write("\n=== 결제 상태 확인 ===")

        # 대기 중이거나 실패 상태인 결제 확인
        payments = Payment.objects.filter(
            created_at__gte=cutoff_date,
            status__in=[Payment.Status.PENDING, Payment.Status.FAILED]
        ).exclude(stripe_payment_intent_id='')

        total_payments = payments.count()
        self.stdout.write(f"확인할 결제: {total_payments}개")

        fixed_count = 0
        error_count = 0

        for payment in payments:
            try:
                # Stripe에서 최신 상태 조회
                intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
                
                # 상태 매핑
                stripe_status_mapping = {
                    'succeeded': Payment.Status.SUCCEEDED,
                    'processing': Payment.Status.PENDING,
                    'requires_payment_method': Payment.Status.FAILED,
                    'requires_confirmation': Payment.Status.PENDING,
                    'requires_action': Payment.Status.PENDING,
                    'canceled': Payment.Status.CANCELED,
                    'requires_capture': Payment.Status.PENDING,
                }

                expected_status = stripe_status_mapping.get(intent.status, Payment.Status.PENDING)

                if payment.status != expected_status:
                    self.stdout.write(
                        self.style.WARNING(
                            f"불일치 발견 - Payment ID: {payment.id}, "
                            f"로컬: {payment.status}, Stripe: {intent.status} -> {expected_status}"
                        )
                    )

                    if should_fix:
                        payment.status = expected_status
                        if expected_status == Payment.Status.SUCCEEDED:
                            payment.paid_at = timezone.now()
                        payment.save()
                        
                        self.stdout.write(f"  ✓ 수정됨: {expected_status}")
                        fixed_count += 1

            except stripe.error.StripeError as e:
                self.stdout.write(
                    self.style.ERROR(f"Stripe 오류 - Payment ID: {payment.id}: {e}")
                )
                error_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"예상치 못한 오류 - Payment ID: {payment.id}: {e}")
                )
                error_count += 1

        self.stdout.write(f"결제 동기화 결과: 수정 {fixed_count}개, 오류 {error_count}개")

    def sync_subscriptions(self, cutoff_date, should_fix):
        """구독 상태 동기화"""
        self.stdout.write("\n=== 구독 상태 확인 ===")

        # 활성 구독 확인
        subscriptions = Subscription.objects.filter(
            created_at__gte=cutoff_date,
            is_active=True
        ).exclude(stripe_subscription_id='')

        total_subscriptions = subscriptions.count()
        self.stdout.write(f"확인할 구독: {total_subscriptions}개")

        fixed_count = 0
        error_count = 0

        for subscription in subscriptions:
            try:
                # Stripe에서 최신 상태 조회
                stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
                
                stripe_is_active = stripe_sub.status in ['active', 'trialing']
                
                # 상태 불일치 확인
                if subscription.is_active != stripe_is_active:
                    self.stdout.write(
                        self.style.WARNING(
                            f"불일치 발견 - Subscription ID: {subscription.id}, "
                            f"로컬: {subscription.is_active}, Stripe: {stripe_sub.status} -> {stripe_is_active}"
                        )
                    )

                    if should_fix:
                        subscription.is_active = stripe_is_active
                        subscription.current_period_start = timezone.datetime.fromtimestamp(
                            stripe_sub.current_period_start, tz=timezone.utc
                        )
                        subscription.current_period_end = timezone.datetime.fromtimestamp(
                            stripe_sub.current_period_end, tz=timezone.utc
                        )
                        
                        if not stripe_is_active:
                            subscription.canceled_at = timezone.now()
                        
                        subscription.save()
                        
                        self.stdout.write(f"  ✓ 수정됨: {stripe_is_active}")
                        fixed_count += 1

                # 기간 정보 동기화
                stripe_period_start = timezone.datetime.fromtimestamp(
                    stripe_sub.current_period_start, tz=timezone.utc
                )
                stripe_period_end = timezone.datetime.fromtimestamp(
                    stripe_sub.current_period_end, tz=timezone.utc
                )

                if (subscription.current_period_start != stripe_period_start or 
                    subscription.current_period_end != stripe_period_end):
                    
                    if should_fix:
                        subscription.current_period_start = stripe_period_start
                        subscription.current_period_end = stripe_period_end
                        subscription.save()

            except stripe.error.StripeError as e:
                self.stdout.write(
                    self.style.ERROR(f"Stripe 오류 - Subscription ID: {subscription.id}: {e}")
                )
                error_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"예상치 못한 오류 - Subscription ID: {subscription.id}: {e}")
                )
                error_count += 1

        self.stdout.write(f"구독 동기화 결과: 수정 {fixed_count}개, 오류 {error_count}개")

    def cleanup_orphaned_payments(self, cutoff_date, should_fix):
        """고아 결제 기록 정리"""
        self.stdout.write("\n=== 고아 결제 기록 정리 ===")

        # Stripe ID가 없는 오래된 대기 중 결제
        orphaned_payments = Payment.objects.filter(
            created_at__lt=cutoff_date,
            status=Payment.Status.PENDING,
            stripe_payment_intent_id__in=['', None]
        )

        count = orphaned_payments.count()
        self.stdout.write(f"정리할 고아 결제: {count}개")

        if should_fix and count > 0:
            orphaned_payments.update(
                status=Payment.Status.CANCELED,
                failure_reason="System cleanup - orphaned payment"
            )
            self.stdout.write(f"✓ {count}개의 고아 결제를 정리했습니다.")