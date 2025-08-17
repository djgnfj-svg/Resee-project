"""
결제 플랜 생성 관리 명령어
"""
from django.core.management.base import BaseCommand

from accounts.models import SubscriptionTier
from payments.models import PaymentPlan


class Command(BaseCommand):
    help = '기본 결제 플랜 생성'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='기존 플랜이 있어도 새로 생성'
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # 기존 플랜 확인
        if PaymentPlan.objects.exists() and not force:
            self.stdout.write(
                self.style.WARNING('결제 플랜이 이미 존재합니다. --force 옵션으로 재생성할 수 있습니다.')
            )
            return

        if force:
            PaymentPlan.objects.all().delete()
            self.stdout.write('기존 결제 플랜을 삭제했습니다.')

        # 결제 플랜 데이터
        plans = [
            {
                'name': 'Free',
                'tier': SubscriptionTier.FREE,
                'monthly_price': 0,
                'yearly_price': 0,
                'description': '기본 무료 플랜',
                'features': [
                    '최대 3일 복습 간격',
                    '기본 복습 기능',
                    '월 5회 AI 질문 생성',
                    '기본 학습 통계'
                ]
            },
            {
                'name': 'Basic',
                'tier': SubscriptionTier.BASIC,
                'monthly_price': 9900,
                'yearly_price': 99000,  # 17% 할인
                'description': '개인 학습자를 위한 기본 플랜',
                'features': [
                    '최대 90일 복습 간격',
                    '모든 복습 기능',
                    '월 50회 AI 질문 생성',
                    '상세 학습 통계',
                    '카테고리별 성과 분석',
                    '우선 고객지원'
                ],
                'stripe_price_id_monthly': 'price_basic_monthly_kr',
                'stripe_price_id_yearly': 'price_basic_yearly_kr'
            },
            {
                'name': 'Pro',
                'tier': SubscriptionTier.PRO,
                'monthly_price': 19900,
                'yearly_price': 199000,  # 17% 할인
                'description': '전문가와 교육기관을 위한 최고급 플랜',
                'features': [
                    '최대 180일 복습 간격',
                    '모든 Basic 기능',
                    '무제한 AI 질문 생성',
                    '전문가급 학습 분석',
                    '학습 패턴 AI 분석',
                    '개인화된 복습 추천',
                    'API 접근 권한',
                    '1:1 전담 지원',
                    '맞춤형 기능 개발'
                ],
                'stripe_price_id_monthly': 'price_pro_monthly_kr',
                'stripe_price_id_yearly': 'price_pro_yearly_kr'
            }
        ]

        # 플랜 생성
        created_count = 0
        for plan_data in plans:
            plan, created = PaymentPlan.objects.get_or_create(
                tier=plan_data['tier'],
                defaults=plan_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {plan.name} 플랜 생성 완료')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  {plan.name} 플랜 이미 존재')
                )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(f'🎉 총 {created_count}개의 결제 플랜이 생성되었습니다!')
        )
        
        # 생성된 플랜 요약 출력
        self.stdout.write('')
        self.stdout.write('📋 생성된 결제 플랜:')
        for plan in PaymentPlan.objects.order_by('tier'):
            monthly = f"{plan.monthly_price:,}원" if plan.monthly_price > 0 else "무료"
            yearly = f"{plan.yearly_price:,}원" if plan.yearly_price > 0 else "무료"
            discount = plan.yearly_discount_percentage
            
            self.stdout.write(f"  • {plan.name} ({plan.get_tier_display()})")
            self.stdout.write(f"    - 월간: {monthly}")
            if discount > 0:
                self.stdout.write(f"    - 연간: {yearly} ({discount}% 할인)")
            else:
                self.stdout.write(f"    - 연간: {yearly}")