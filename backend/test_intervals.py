from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from content.models import Content
from review.models import ReviewSchedule, ReviewHistory
from review.utils import get_review_intervals

User = get_user_model()

# PRO 계정 가져오기
user = User.objects.get(email='longterm_pro@resee.com')
print(f'사용자: {user.email}, 구독: {user.subscription.tier}')

# 기존 테스트 콘텐츠 삭제
existing = Content.objects.filter(author=user, title__contains='간격 테스트').delete()
print(f'기존 테스트 콘텐츠 삭제: {existing}')

# 새 콘텐츠 생성
content = Content.objects.create(
    title='간격 테스트 콘텐츠',
    content='에빙하우스 망각곡선 간격 테스트',
    author=user,
    priority='high'
)

print(f'콘텐츠 ID: {content.id}, 생성일: {content.created_at}')

# 복습 스케줄 확인
schedule = ReviewSchedule.objects.filter(content=content, user=user).first()
if schedule:
    print(f'다음 복습일: {schedule.next_review_date}')
    print(f'간격 인덱스: {schedule.interval_index}')
    
    # 연속 날짜별 확인
    print('\n=== 연속 날짜별 복습 확인 ===')
    for i in range(8):
        check_date = timezone.now().date() + timedelta(days=i)
        our_content_review = ReviewSchedule.objects.filter(
            content=content,
            user=user,
            is_active=True,
            next_review_date__date=check_date
        ).exists()
        status = '📋 복습 있음' if our_content_review else '⭕ 없음'
        print(f'Day {i:2d} ({check_date}): {status}')
else:
    print('복습 스케줄이 생성되지 않았습니다\!')
