"""
결제 시스템 모니터링 관리 명령어
결제 시스템의 건강 상태를 확인하고 문제점을 탐지합니다.
"""

import logging
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q

from payments.models import Payment, Subscription, WebhookEvent
from accounts.models import User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '결제 시스템 상태를 모니터링하고 이상 징후를 탐지합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='몇 시간 동안의 데이터를 확인할지 (기본값: 24)'
        )
        parser.add_argument(
            '--alert-threshold',
            type=float,
            default=10.0,
            help='실패율 임계값 % (기본값: 10.0)'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        alert_threshold = options['alert_threshold']

        self.stdout.write(f"결제 시스템 모니터링 시작 (최근 {hours}시간)")
        self.stdout.write(f"실패율 알림 임계값: {alert_threshold}%\n")

        cutoff_time = timezone.now() - timedelta(hours=hours)

        # 결제 통계
        self.check_payment_health(cutoff_time, alert_threshold)
        
        # 구독 통계
        self.check_subscription_health(cutoff_time)
        
        # 웹훅 상태
        self.check_webhook_health(cutoff_time)
        
        # 사용자 이상 행동 탐지
        self.detect_suspicious_activities(cutoff_time)

        self.stdout.write(self.style.SUCCESS('\n모니터링 완료!'))

    def check_payment_health(self, cutoff_time, alert_threshold):
        """결제 시스템 건강 상태 확인"""
        self.stdout.write("=== 결제 통계 ===")

        payments = Payment.objects.filter(created_at__gte=cutoff_time)
        total_payments = payments.count()

        if total_payments == 0:
            self.stdout.write("결제 기록 없음")
            return

        # 상태별 통계
        status_stats = payments.values('status').annotate(count=Count('id')).order_by('-count')
        
        succeeded_count = payments.filter(status=Payment.Status.SUCCEEDED).count()
        failed_count = payments.filter(status=Payment.Status.FAILED).count()
        pending_count = payments.filter(status=Payment.Status.PENDING).count()

        # 성공률 및 실패율 계산
        if total_payments > 0:
            success_rate = (succeeded_count / total_payments) * 100
            failure_rate = (failed_count / total_payments) * 100
        else:
            success_rate = failure_rate = 0

        self.stdout.write(f"총 결제 시도: {total_payments}")
        self.stdout.write(f"성공: {succeeded_count} ({success_rate:.1f}%)")
        self.stdout.write(f"실패: {failed_count} ({failure_rate:.1f}%)")
        self.stdout.write(f"대기: {pending_count}")

        # 실패율 알림
        if failure_rate > alert_threshold:
            self.stdout.write(
                self.style.ERROR(
                    f"🚨 높은 실패율 감지! {failure_rate:.1f}% (임계값: {alert_threshold}%)"
                )
            )

        # 금액 통계
        total_amount = payments.filter(status=Payment.Status.SUCCEEDED).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        avg_amount = payments.filter(status=Payment.Status.SUCCEEDED).aggregate(
            avg=Avg('amount')
        )['avg'] or Decimal('0')

        self.stdout.write(f"총 결제 금액: ₩{total_amount:,}")
        self.stdout.write(f"평균 결제 금액: ₩{avg_amount:,.0f}")

        # 실패 사유 분석
        failure_reasons = payments.filter(
            status=Payment.Status.FAILED,
            failure_reason__isnull=False
        ).exclude(failure_reason='').values('failure_reason').annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        if failure_reasons:
            self.stdout.write("\n주요 실패 사유:")
            for reason in failure_reasons:
                self.stdout.write(f"  • {reason['failure_reason']}: {reason['count']}회")

    def check_subscription_health(self, cutoff_time):
        """구독 시스템 건강 상태 확인"""
        self.stdout.write("\n=== 구독 통계 ===")

        # 전체 구독 통계
        total_subscriptions = Subscription.objects.count()
        active_subscriptions = Subscription.objects.filter(is_active=True).count()
        
        # 최근 생성된 구독
        recent_subscriptions = Subscription.objects.filter(created_at__gte=cutoff_time).count()
        
        # 최근 취소된 구독
        recent_cancellations = Subscription.objects.filter(
            canceled_at__gte=cutoff_time,
            canceled_at__isnull=False
        ).count()

        self.stdout.write(f"전체 구독: {total_subscriptions}")
        self.stdout.write(f"활성 구독: {active_subscriptions}")
        self.stdout.write(f"최근 신규 구독: {recent_subscriptions}")
        self.stdout.write(f"최근 취소: {recent_cancellations}")

        # 구독 플랜별 통계
        plan_stats = Subscription.objects.filter(is_active=True).values(
            'plan__name'
        ).annotate(count=Count('id')).order_by('-count')

        if plan_stats:
            self.stdout.write("\n플랜별 활성 구독:")
            for stat in plan_stats:
                self.stdout.write(f"  • {stat['plan__name']}: {stat['count']}개")

        # 만료 임박 구독
        expiring_soon = Subscription.objects.filter(
            is_active=True,
            current_period_end__lte=timezone.now() + timedelta(days=3)
        ).count()

        if expiring_soon > 0:
            self.stdout.write(f"\n⚠️  3일 내 만료 예정: {expiring_soon}개")

    def check_webhook_health(self, cutoff_time):
        """웹훅 처리 상태 확인"""
        self.stdout.write("\n=== 웹훅 상태 ===")

        webhooks = WebhookEvent.objects.filter(created_at__gte=cutoff_time)
        total_webhooks = webhooks.count()

        if total_webhooks == 0:
            self.stdout.write("웹훅 이벤트 없음")
            return

        processed_webhooks = webhooks.filter(processed=True).count()
        failed_webhooks = webhooks.filter(processed=False).count()

        success_rate = (processed_webhooks / total_webhooks) * 100 if total_webhooks > 0 else 0

        self.stdout.write(f"총 웹훅 이벤트: {total_webhooks}")
        self.stdout.write(f"처리 성공: {processed_webhooks} ({success_rate:.1f}%)")
        self.stdout.write(f"처리 실패: {failed_webhooks}")

        if failed_webhooks > 0:
            self.stdout.write(
                self.style.WARNING(f"⚠️  처리 실패한 웹훅: {failed_webhooks}개")
            )

        # 이벤트 타입별 통계
        event_types = webhooks.values('event_type').annotate(
            total=Count('id'),
            failed=Count('id', filter=Q(processed=False))
        ).order_by('-total')[:5]

        if event_types:
            self.stdout.write("\n주요 웹훅 이벤트:")
            for event in event_types:
                self.stdout.write(
                    f"  • {event['event_type']}: "
                    f"{event['total']}개 (실패: {event['failed']}개)"
                )

    def detect_suspicious_activities(self, cutoff_time):
        """의심스러운 활동 탐지"""
        self.stdout.write("\n=== 이상 징후 탐지 ===")

        suspicious_count = 0

        # 1. 짧은 시간에 여러 결제 시도
        frequent_attempts = Payment.objects.filter(
            created_at__gte=cutoff_time
        ).values('user').annotate(
            attempt_count=Count('id')
        ).filter(attempt_count__gte=5)

        if frequent_attempts:
            self.stdout.write(f"🔍 빈번한 결제 시도 사용자: {frequent_attempts.count()}명")
            suspicious_count += frequent_attempts.count()

        # 2. 높은 실패율 사용자
        high_failure_users = Payment.objects.filter(
            created_at__gte=cutoff_time
        ).values('user').annotate(
            total_attempts=Count('id'),
            failed_attempts=Count('id', filter=Q(status=Payment.Status.FAILED))
        ).filter(
            total_attempts__gte=3,
            failed_attempts__gte=2
        )

        high_failure_count = 0
        for user_stat in high_failure_users:
            failure_rate = (user_stat['failed_attempts'] / user_stat['total_attempts']) * 100
            if failure_rate >= 50:  # 50% 이상 실패율
                high_failure_count += 1

        if high_failure_count > 0:
            self.stdout.write(f"🔍 높은 실패율 사용자: {high_failure_count}명")
            suspicious_count += high_failure_count

        # 3. 구독 후 즉시 취소
        quick_cancellations = Subscription.objects.filter(
            created_at__gte=cutoff_time,
            canceled_at__isnull=False,
            canceled_at__lt=timezone.now() - timedelta(hours=1)
        ).count()

        if quick_cancellations > 0:
            self.stdout.write(f"🔍 즉시 취소 구독: {quick_cancellations}개")
            suspicious_count += quick_cancellations

        if suspicious_count == 0:
            self.stdout.write("✅ 의심스러운 활동 없음")