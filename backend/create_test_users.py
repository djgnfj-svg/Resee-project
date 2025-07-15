#!/usr/bin/env python
"""
Create test users for Resee platform
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resee.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_test_users():
    """Create test users for development"""
    
    # Create superuser if doesn't exist
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@resee.local',
            password='admin123!',
            first_name='관리자',
            last_name='Resee'
        )
        print("✅ 슈퍼유저 'admin' 생성됨 (비밀번호: admin123!)")
    else:
        print("ℹ️  슈퍼유저 'admin' 이미 존재함")

    # Create test user if doesn't exist
    if not User.objects.filter(username='testuser').exists():
        test_user = User.objects.create_user(
            username='testuser',
            email='test@resee.local',
            password='test123!',
            first_name='테스트',
            last_name='사용자'
        )
        print("✅ 테스트 사용자 'testuser' 생성됨 (비밀번호: test123!)")
    else:
        print("ℹ️  테스트 사용자 'testuser' 이미 존재함")

    # Create demo user if doesn't exist
    if not User.objects.filter(username='demo').exists():
        demo_user = User.objects.create_user(
            username='demo',
            email='demo@resee.local',
            password='demo123!',
            first_name='데모',
            last_name='사용자'
        )
        print("✅ 데모 사용자 'demo' 생성됨 (비밀번호: demo123!)")
    else:
        print("ℹ️  데모 사용자 'demo' 이미 존재함")

    print(f"\n📊 총 사용자 수: {User.objects.count()}")
    
    # Display all test accounts
    print("\n🔑 테스트 계정 목록:")
    print("=" * 50)
    print("1. 관리자 계정:")
    print("   - 사용자명: admin")
    print("   - 비밀번호: admin123!")
    print("   - 이메일: admin@resee.local")
    print("")
    print("2. 테스트 계정:")
    print("   - 사용자명: testuser")
    print("   - 비밀번호: test123!")
    print("   - 이메일: test@resee.local")
    print("")
    print("3. 데모 계정:")
    print("   - 사용자명: demo")
    print("   - 비밀번호: demo123!")
    print("   - 이메일: demo@resee.local")
    print("=" * 50)

if __name__ == '__main__':
    create_test_users()