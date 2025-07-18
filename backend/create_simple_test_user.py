#!/usr/bin/env python
import os
import sys
import django

# Django 환경 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resee.settings')
sys.path.append('/app')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# test/test 계정 생성
try:
    user = User.objects.create_user(
        username='test',
        password='test',
        email='test@example.com'
    )
    print("✅ 사용자 'test' 생성 완료")
    print("   사용자명: test")
    print("   비밀번호: test")
    print("   이메일: test@example.com")
except Exception as e:
    print(f"⚠️ 사용자 'test' 생성 실패 또는 이미 존재: {e}")

# 계정 확인
users = User.objects.all()
print(f"\n📋 전체 사용자 수: {users.count()}")
for user in users:
    print(f"   - {user.username} ({user.email})")

print("\n🌐 로그인 페이지: http://localhost:3000/login")
print("🔑 test / test 로 로그인하세요!")