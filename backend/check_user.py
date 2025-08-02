#!/usr/bin/env python
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resee.settings')
sys.path.append('/app')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print('=== 사용자 계정 확인 ===')
users = User.objects.all()ㄷ=enum

for user in users:
    print(f'이메일: {user.email}, 사용자명: {user.username}, 활성화: {user.is_active}')

print('\n=== test@resee.com 사용자 상세 ===')
try:
    test_user = User.objects.get(email='test@resee.com')
    print(f'ID: {test_user.id}')
    print(f'이메일: {test_user.email}')
    print(f'사용자명: {test_user.username}')
    print(f'활성화: {test_user.is_active}')
    print(f'이메일 인증: {getattr(test_user, "email_verified", "필드 없음")}')
    print(f'비밀번호 설정됨: {test_user.has_usable_password()}')
except User.DoesNotExist:
    print('test@resee.com 사용자를 찾을 수 없습니다.')