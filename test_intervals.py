#!/usr/bin/env python3
"""
에빙하우스 간격 테스트 스크립트
"""
import os
import sys
import django

# Django 설정
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resee.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from content.models import Content
from review.models import ReviewSchedule, ReviewHistory
from review.utils import get_review_intervals

User = get_user_model()

def main():
    # PRO 계정 가져오기
    user = User.objects.get(email='longterm_pro@resee.com')
    print(f"사용자: {user.email}, 구독: {user.subscription.tier}")
    
    # 기존 테스트 콘텐츠 삭제
    existing = Content.objects.filter(author=user, title__contains='간격 테스트').delete()
    print(f"기존 테스트 콘텐츠 삭제: {existing}")
    
    # 새 콘텐츠 생성
    content = Content.objects.create(
        title='간격 테스트 콘텐츠',
        content='''에빙하우스 망각곡선 간격 테스트를 위한 콘텐츠입니다.

이 콘텐츠는 다음과 같은 간격으로 복습되어야 합니다:
- 첫 복습: 1일 후  
- 두번째 복습: 3일 후
- 세번째 복습: 7일 후
- 네번째 복습: 14일 후

연속된 날에는 나타나면 안 됩니다!''',
        author=user,
        priority='high'
    )
    
    print(f"\n=== 새 콘텐츠 생성 ===")
    print(f"ID: {content.id}")
    print(f"제목: {content.title}")
    print(f"생성일: {content.created_at}")
    
    # 복습 스케줄 확인
    schedule = ReviewSchedule.objects.filter(content=content, user=user).first()
    if schedule:
        print(f"\n=== 초기 복습 스케줄 ===")
        print(f"다음 복습일: {schedule.next_review_date}")
        print(f"간격 인덱스: {schedule.interval_index}")
        print(f"초기 복습 완료: {schedule.initial_review_completed}")
        
        # 오늘부터 여러 날 확인
        print(f"\n=== 연속 날짜별 복습 확인 ===")
        for i in range(8):  # 8일간 확인
            check_date = timezone.now().date() + timedelta(days=i)
            
            reviews_that_day = ReviewSchedule.objects.filter(
                user=user,
                is_active=True,
                next_review_date__date=check_date
            ).count()
            
            our_content_review = ReviewSchedule.objects.filter(
                content=content,
                user=user,
                is_active=True,
                next_review_date__date=check_date
            ).exists()
            
            status = "📋 우리 콘텐츠 있음" if our_content_review else "⭕ 없음"
            print(f"Day {i:2d} ({check_date}): 전체 {reviews_that_day}개, {status}")
    else:
        print("복습 스케줄이 생성되지 않았습니다!")
    
    return content, schedule

if __name__ == "__main__":
    content, schedule = main()