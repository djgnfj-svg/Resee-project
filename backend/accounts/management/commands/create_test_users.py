"""
Create test users for development/testing
"""
import uuid

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import SubscriptionTier

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test users for development/testing'

    def handle(self, *args, **options):
        test_users = [
            {
                'email': 'admin@resee.com',
                'password': 'admin123!',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
                'is_email_verified': True,
            },
            {
                'email': 'test@resee.com',
                'password': 'test123!',
                'first_name': 'Test',
                'last_name': 'User',
                'is_staff': False,
                'is_superuser': False,
                'is_email_verified': True,
            },
            {
                'email': 'demo@resee.com',
                'password': 'demo123!',
                'first_name': 'Demo',
                'last_name': 'User',
                'is_staff': False,
                'is_superuser': False,
                'is_email_verified': True,
            },
            {
                'email': 'unverified@resee.com',
                'password': 'test123!',
                'first_name': 'Unverified',
                'last_name': 'User',
                'is_staff': False,
                'is_superuser': False,
                'is_email_verified': False,
            },
        ]

        for user_data in test_users:
            email = user_data['email']
            try:
                user = User.objects.get(email=email)
                self.stdout.write(f'사용자 {email} 이미 존재 - 업데이트 중')
                
                # 기존 사용자 업데이트
                for key, value in user_data.items():
                    if key != 'password':
                        setattr(user, key, value)
                
                user.set_password(user_data['password'])
                user.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ 사용자 {email} 업데이트 완료')
                )
                
            except User.DoesNotExist:
                # 새 사용자 생성
                user_data_copy = user_data.copy()
                password = user_data_copy.pop('password')
                
                # is_ 필드들은 create_user가 아닌 별도로 설정
                is_staff = user_data_copy.pop('is_staff', False)
                is_superuser = user_data_copy.pop('is_superuser', False)
                is_email_verified = user_data_copy.pop('is_email_verified', False)
                
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=user_data_copy.get('first_name', ''),
                    last_name=user_data_copy.get('last_name', '')
                )
                
                # 추가 필드 설정
                user.is_staff = is_staff
                user.is_superuser = is_superuser
                user.is_email_verified = is_email_verified
                user.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ 사용자 {email} 생성 완료')
                )
            
            # 인증 토큰이 필요한 경우 생성
            if not user.is_email_verified and not user.email_verification_token:
                user.email_verification_token = str(uuid.uuid4())
                user.save()
                self.stdout.write(f'  - 인증 토큰 생성됨')

        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 테스트 사용자 생성/업데이트 완료!')
        )
        self.stdout.write('로그인 정보:')
        for user_data in test_users:
            self.stdout.write(f'  - {user_data["email"]} / {user_data.get("password", "test123!")}')