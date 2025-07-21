#!/usr/bin/env python
"""
AWS SES 이메일 발송 테스트 스크립트
"""

import os
import sys
import django
from django.conf import settings

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resee.settings')
django.setup()

from django.core.mail import send_mail
from accounts.tasks import send_verification_email
from accounts.models import User

def test_basic_email():
    """기본 이메일 발송 테스트"""
    print("🧪 기본 이메일 발송 테스트...")
    
    try:
        result = send_mail(
            subject='[Resee] AWS SES 연동 테스트',
            message='AWS SES가 성공적으로 연동되었습니다!\n\n이 이메일은 테스트용입니다.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['your-test-email@gmail.com'],  # 본인 이메일로 변경하세요
            html_message="""
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #4F46E5;">🎉 AWS SES 연동 성공!</h2>
                <p>AWS SES가 성공적으로 연동되었습니다.</p>
                <p>이제 실제 이메일을 발송할 수 있습니다.</p>
                <hr>
                <small style="color: #666;">이 이메일은 테스트용입니다.</small>
            </div>
            """,
            fail_silently=False,
        )
        
        if result:
            print("✅ 기본 이메일 발송 성공!")
            return True
        else:
            print("❌ 기본 이메일 발송 실패")
            return False
            
    except Exception as e:
        print(f"❌ 기본 이메일 발송 오류: {str(e)}")
        return False

def test_verification_email():
    """인증 이메일 발송 테스트"""
    print("\n🧪 인증 이메일 발송 테스트...")
    
    try:
        # 테스트 사용자 생성
        test_email = "test-ses@example.com"  # 본인 이메일로 변경하세요
        
        # 기존 사용자 삭제 (있다면)
        User.objects.filter(email=test_email).delete()
        
        # 새 사용자 생성
        user = User.objects.create_user(
            email=test_email,
            password='test123!',
            first_name='SES',
            last_name='Test',
            is_email_verified=False
        )
        
        print(f"테스트 사용자 생성: {user.email}")
        
        # 인증 이메일 발송
        from accounts.tasks import send_verification_email
        result = send_verification_email(user.id)
        
        if result:
            print("✅ 인증 이메일 발송 성공!")
            print(f"📧 {user.email}로 인증 이메일이 발송되었습니다.")
            return True
        else:
            print("❌ 인증 이메일 발송 실패")
            return False
            
    except Exception as e:
        print(f"❌ 인증 이메일 발송 오류: {str(e)}")
        return False

def check_aws_settings():
    """AWS 설정 확인"""
    print("\n🔍 AWS SES 설정 확인...")
    
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"AWS_SES_REGION_NAME: {getattr(settings, 'AWS_SES_REGION_NAME', 'Not set')}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    # AWS 자격증명 확인 (실제 값은 표시하지 않음)
    aws_access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', '')
    aws_secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', '')
    
    if aws_access_key:
        print(f"AWS_ACCESS_KEY_ID: ✅ 설정됨 (AKI...{aws_access_key[-4:]})")
    else:
        print("AWS_ACCESS_KEY_ID: ❌ 설정되지 않음")
        
    if aws_secret_key:
        print(f"AWS_SECRET_ACCESS_KEY: ✅ 설정됨")
    else:
        print("AWS_SECRET_ACCESS_KEY: ❌ 설정되지 않음")

def main():
    """메인 테스트 함수"""
    print("=" * 50)
    print("🚀 AWS SES 연동 테스트 시작")
    print("=" * 50)
    
    # 설정 확인
    check_aws_settings()
    
    # 이메일 백엔드가 SES인지 확인
    if settings.EMAIL_BACKEND != 'django_ses.SESBackend':
        print(f"\n⚠️  현재 EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        print("AWS SES를 사용하려면 EMAIL_BACKEND=django_ses.SESBackend로 설정하세요.")
        return
    
    # 기본 이메일 테스트
    basic_success = test_basic_email()
    
    # 인증 이메일 테스트
    verification_success = test_verification_email()
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)
    print(f"기본 이메일 발송: {'✅ 성공' if basic_success else '❌ 실패'}")
    print(f"인증 이메일 발송: {'✅ 성공' if verification_success else '❌ 실패'}")
    
    if basic_success and verification_success:
        print("\n🎉 AWS SES 연동이 성공적으로 완료되었습니다!")
        print("이제 실제 회원가입 이메일 인증이 작동합니다.")
    else:
        print("\n❌ AWS SES 연동에 문제가 있습니다.")
        print("AWS_SES_SETUP_GUIDE.md 파일을 참조하여 설정을 확인하세요.")

if __name__ == "__main__":
    main()