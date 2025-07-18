#!/usr/bin/env python
"""
Django script to create test review data for the Resee application.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone
import random

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resee.settings')
django.setup()

from django.contrib.auth import get_user_model
from content.models import Content
from review.models import ReviewSchedule, ReviewHistory

User = get_user_model()

def create_test_reviews():
    """Create test review data"""
    
    print("🚀 테스트 복습 데이터 생성을 시작합니다...")
    
    # Get test users
    test_users = User.objects.filter(username__in=['testuser', 'demo'])
    
    if not test_users.exists():
        print("⚠️  테스트 사용자가 없습니다.")
        return
    
    for user in test_users:
        print(f"\n👤 사용자 '{user.username}'의 복습 데이터 생성 중...")
        
        # Get user's content
        user_contents = Content.objects.filter(author=user)
        
        if not user_contents.exists():
            print(f"⚠️  사용자 '{user.username}'의 콘텐츠가 없습니다.")
            continue
        
        # Create review schedules for each content
        for content in user_contents:
            # Check if schedule already exists
            schedule, created = ReviewSchedule.objects.get_or_create(
                user=user,
                content=content,
                defaults={
                    'next_review_date': timezone.now().date(),
                    'interval_index': 0,
                    'is_active': True,
                    'initial_review_completed': False
                }
            )
            
            if created:
                print(f"✅ 리뷰 스케줄 생성: {content.title}")
        
        # Create review history data for the last 30 days
        today = timezone.now().date()
        
        for days_back in range(30):
            review_date = today - timedelta(days=days_back)
            
            # Skip some days to create realistic streak patterns
            if random.random() < 0.3:  # 30% chance to skip a day
                continue
            
            # Create 1-5 reviews per day
            num_reviews = random.randint(1, min(5, user_contents.count()))
            selected_contents = random.sample(list(user_contents), num_reviews)
            
            for content in selected_contents:
                # Skip if review already exists for this date
                if ReviewHistory.objects.filter(
                    user=user,
                    content=content,
                    review_date__date=review_date
                ).exists():
                    continue
                
                # Create review with weighted results (more "remembered" for realistic success rate)
                result_weights = [
                    ('remembered', 0.6),  # 60% success rate
                    ('partial', 0.25),    # 25% partial
                    ('forgot', 0.15)      # 15% forgot
                ]
                
                result = random.choices(
                    [r[0] for r in result_weights],
                    weights=[r[1] for r in result_weights]
                )[0]
                
                review_history = ReviewHistory.objects.create(
                    user=user,
                    content=content,
                    review_date=timezone.datetime.combine(
                        review_date, 
                        timezone.datetime.min.time()
                    ).replace(tzinfo=timezone.get_current_timezone()),
                    result=result,
                    time_spent=random.randint(30, 300),  # 30 seconds to 5 minutes
                    notes=f"테스트 복습 - {result}"
                )
                
                print(f"✅ 복습 히스토리 생성: {content.title} - {result} ({review_date})")

def main():
    """Main function to create test review data"""
    
    print("="*60)
    print("🧪 RESEE 복습 데이터 생성")
    print("="*60)
    
    try:
        create_test_reviews()
        
        print("\n" + "="*60)
        print("✅ 복습 데이터 생성 완료!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 복습 데이터 생성 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()