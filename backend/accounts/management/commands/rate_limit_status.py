"""
Rate limit 상태 확인 명령어 (단순화됨)
Redis 제거로 인해 DRF throttling 사용
"""
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Rate limit 설정 상태 확인 (DRF throttling 기반)'

    def handle(self, *args, **options):
        self.stdout.write("=== Rate Limiting 상태 ===")

        # DRF throttling 설정 표시
        throttle_rates = getattr(settings, 'REST_FRAMEWORK', {}).get('DEFAULT_THROTTLE_RATES', {})

        self.stdout.write("\n📊 DRF Throttling 설정:")
        for key, rate in throttle_rates.items():
            self.stdout.write(f"  • {key}: {rate}")

        self.stdout.write(f"\n✅ Redis 제거완료 - DRF throttling으로 전환됨")
        self.stdout.write("   더 이상 Redis 기반 rate limiting이 사용되지 않습니다.")