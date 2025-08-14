"""
Rate limit 상태 확인 및 관리 명령어
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Rate limit 상태 확인 및 관리'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['status', 'clear', 'user_status', 'top_users'],
            default='status',
            help='실행할 액션 선택'
        )
        
        parser.add_argument(
            '--user-id',
            type=int,
            help='특정 사용자 ID (user_status 액션용)'
        )
        
        parser.add_argument(
            '--ip',
            type=str,
            help='특정 IP 주소 (clear 액션용)'
        )
        
        parser.add_argument(
            '--scope',
            type=str,
            help='Rate limit 범위 (clear 액션용)'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'status':
            self._show_general_status()
        elif action == 'clear':
            self._clear_rate_limits(options)
        elif action == 'user_status':
            self._show_user_status(options['user_id'])
        elif action == 'top_users':
            self._show_top_users()

    def _show_general_status(self):
        """전체 Rate limit 상태 표시"""
        self.stdout.write(self.style.SUCCESS('=== Rate Limit 전체 상태 ===\n'))
        
        # Rate limit 미들웨어 활성화 상태
        from django.conf import settings
        rate_limit_enabled = getattr(settings, 'RATE_LIMIT_ENABLE', False)
        status = "활성화" if rate_limit_enabled else "비활성화"
        color = self.style.SUCCESS if rate_limit_enabled else self.style.WARNING
        self.stdout.write(f"Rate Limiting 상태: {color(status)}")
        
        # 화이트리스트 IP 확인
        whitelist = getattr(settings, 'ADMIN_IP_WHITELIST', [])
        if whitelist:
            self.stdout.write(f"화이트리스트 IP: {', '.join(whitelist)}")
        else:
            self.stdout.write("화이트리스트 IP: 없음")
        
        self.stdout.write("")
        
        # 현재 활성 Rate limit 확인
        self._show_active_rate_limits()

    def _show_active_rate_limits(self):
        """현재 활성화된 Rate limit 표시"""
        self.stdout.write("=== 현재 활성 Rate Limits ===")
        
        try:
            # Redis에서 rate_limit 관련 키 가져오기
            redis_client = cache._cache.get_client()
            keys = redis_client.keys("rate_limit:*")
            
            if not keys:
                self.stdout.write("활성 Rate limit 없음")
                return
            
            # 키별로 분류
            rate_limits = {
                'ip': [],
                'user': [],
                'endpoint': [],
                'ai': []
            }
            
            for key in keys:
                key_str = key.decode('utf-8')
                parts = key_str.split(':')
                
                if len(parts) >= 3:
                    limit_type = parts[1]
                    if limit_type in rate_limits:
                        value = redis_client.get(key)
                        ttl = redis_client.ttl(key)
                        
                        rate_limits[limit_type].append({
                            'key': key_str,
                            'value': int(value) if value else 0,
                            'ttl': ttl
                        })
            
            # 결과 출력
            for limit_type, limits in rate_limits.items():
                if limits:
                    self.stdout.write(f"\n{limit_type.upper()} Rate Limits:")
                    for limit in sorted(limits, key=lambda x: x['value'], reverse=True)[:10]:
                        ttl_str = f"{limit['ttl']}초" if limit['ttl'] > 0 else "만료됨"
                        self.stdout.write(f"  {limit['key']}: {limit['value']} ({ttl_str})")
                        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Rate limit 상태 확인 실패: {e}")
            )

    def _show_user_status(self, user_id):
        """특정 사용자의 Rate limit 상태 표시"""
        if not user_id:
            self.stdout.write(
                self.style.ERROR("--user-id 옵션이 필요합니다")
            )
            return
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"사용자 ID {user_id}를 찾을 수 없습니다")
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'=== 사용자 {user.email} (ID: {user_id}) Rate Limit 상태 ===\n')
        )
        
        # 구독 정보
        if hasattr(user, 'subscription'):
            tier = user.subscription.tier
            self.stdout.write(f"구독 티어: {tier}")
        else:
            self.stdout.write("구독 정보: 없음")
        
        # 사용자별 Rate limit 확인
        try:
            redis_client = cache._cache.get_client()
            user_keys = redis_client.keys(f"rate_limit:user:{user_id}:*")
            ai_keys = redis_client.keys(f"rate_limit:user_ai:{user_id}:*")
            upload_keys = redis_client.keys(f"rate_limit:user_upload:{user_id}:*")
            
            all_keys = user_keys + ai_keys + upload_keys
            
            if not all_keys:
                self.stdout.write("현재 Rate limit 없음")
                return
            
            self.stdout.write("\n현재 Rate Limits:")
            for key in all_keys:
                key_str = key.decode('utf-8')
                value = redis_client.get(key)
                ttl = redis_client.ttl(key)
                
                limit_type = key_str.split(':')[1:3]
                limit_name = ':'.join(limit_type)
                ttl_str = f"{ttl}초" if ttl > 0 else "만료됨"
                
                self.stdout.write(f"  {limit_name}: {value} ({ttl_str})")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"사용자 Rate limit 확인 실패: {e}")
            )

    def _show_top_users(self):
        """가장 많은 요청을 보낸 사용자들 표시"""
        self.stdout.write(self.style.SUCCESS('=== 최고 요청량 사용자들 ===\n'))
        
        try:
            redis_client = cache._cache.get_client()
            user_keys = redis_client.keys("rate_limit:user:*:hour")
            
            if not user_keys:
                self.stdout.write("시간당 Rate limit 데이터 없음")
                return
            
            user_requests = []
            
            for key in user_keys:
                key_str = key.decode('utf-8')
                parts = key_str.split(':')
                
                if len(parts) >= 3:
                    user_id = int(parts[2])
                    value = int(redis_client.get(key) or 0)
                    
                    try:
                        user = User.objects.get(id=user_id)
                        tier = user.subscription.tier if hasattr(user, 'subscription') else 'FREE'
                        
                        user_requests.append({
                            'user_id': user_id,
                            'email': user.email,
                            'tier': tier,
                            'requests': value
                        })
                    except User.DoesNotExist:
                        continue
            
            # 요청 수로 정렬
            user_requests.sort(key=lambda x: x['requests'], reverse=True)
            
            self.stdout.write("사용자별 시간당 요청 수:")
            for i, user_data in enumerate(user_requests[:20], 1):
                self.stdout.write(
                    f"{i:2}. {user_data['email']} ({user_data['tier']}): "
                    f"{user_data['requests']} requests"
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"최고 사용자 확인 실패: {e}")
            )

    def _clear_rate_limits(self, options):
        """Rate limit 초기화"""
        user_id = options.get('user_id')
        ip = options.get('ip')
        scope = options.get('scope')
        
        try:
            redis_client = cache._cache.get_client()
            
            if user_id:
                # 특정 사용자의 Rate limit 초기화
                keys = redis_client.keys(f"rate_limit:*:{user_id}:*")
                if keys:
                    redis_client.delete(*keys)
                    self.stdout.write(
                        self.style.SUCCESS(f"사용자 {user_id}의 Rate limit 초기화 완료")
                    )
                else:
                    self.stdout.write("해당 사용자의 Rate limit 데이터 없음")
            
            elif ip:
                # 특정 IP의 Rate limit 초기화
                keys = redis_client.keys(f"rate_limit:*:{ip}:*")
                if keys:
                    redis_client.delete(*keys)
                    self.stdout.write(
                        self.style.SUCCESS(f"IP {ip}의 Rate limit 초기화 완료")
                    )
                else:
                    self.stdout.write("해당 IP의 Rate limit 데이터 없음")
            
            elif scope:
                # 특정 스코프의 Rate limit 초기화
                keys = redis_client.keys(f"rate_limit:{scope}:*")
                if keys:
                    redis_client.delete(*keys)
                    self.stdout.write(
                        self.style.SUCCESS(f"스코프 '{scope}'의 Rate limit 초기화 완료")
                    )
                else:
                    self.stdout.write(f"스코프 '{scope}'의 Rate limit 데이터 없음")
            
            else:
                # 모든 Rate limit 초기화 (주의!)
                self.stdout.write(
                    self.style.WARNING("모든 Rate limit을 초기화하시겠습니까? [y/N]: "),
                    ending=""
                )
                
                confirm = input()
                if confirm.lower() == 'y':
                    keys = redis_client.keys("rate_limit:*")
                    if keys:
                        redis_client.delete(*keys)
                        self.stdout.write(
                            self.style.SUCCESS(f"모든 Rate limit 초기화 완료 ({len(keys)}개)")
                        )
                    else:
                        self.stdout.write("Rate limit 데이터 없음")
                else:
                    self.stdout.write("취소됨")
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Rate limit 초기화 실패: {e}")
            )