"""
복습 시스템 유틸리티 함수
"""

from datetime import timedelta

from django.utils import timezone

from accounts.subscription.services import SubscriptionService


def get_review_intervals(user=None):
    """에빙하우스 망각곡선을 사용한 사용자 구독 티어 기반 복습 간격 반환

    Hermann Ebbinghaus의 최적 간격 반복 연구를 기반으로:
    - 1일: 초기 강화
    - 3일: 단기 공고화
    - 7일: 작업 기억에서 장기 기억으로 전환
    - 14일: 장기 기억 강화
    - 30일: 월간 강화
    - 60일: 격월 공고화
    - 120일: 분기별 복습 (4개월)
    - 180일: 반기별 복습 (6개월)

    Args:
        user: 사용자 인스턴스 (선택). 제공되지 않으면 기본 간격 반환.

    Returns:
        list: 구독 티어 기반 복습 간격 (일 단위)
    """
    # 구독 티어에 따라 간격 반환
    from accounts.models import SubscriptionTier

    # 각 티어별 에빙하우스 최적화 간격
    tier_intervals = {
        SubscriptionTier.FREE: [1, 3],  # 기본 간격 반복 (최대 3일)
        SubscriptionTier.BASIC: [
            1,
            3,
            7,
            14,
            30,
            60,
            90,
        ],  # 중기 기억 (최대 90일)
        SubscriptionTier.PRO: [
            1,
            3,
            7,
            14,
            30,
            60,
            120,
            180,
        ],  # 완전한 장기 보존 (최대 180일)
    }

    # 사용자가 없으면 무료 티어 간격으로 기본 설정
    if not user:
        return tier_intervals[SubscriptionTier.FREE]

    # 사용자가 활성 구독을 가지고 있는지 확인
    if not hasattr(user, "subscription"):
        return tier_intervals[SubscriptionTier.FREE]

    subscription = user.subscription

    # 구독이 활성화되어 있고 만료되지 않았는지 확인
    if not subscription.is_active or subscription.is_expired():
        return tier_intervals[SubscriptionTier.FREE]

    # 사용자 티어의 간격 반환
    return tier_intervals.get(subscription.tier, tier_intervals[SubscriptionTier.FREE])


def calculate_next_review_date(user, interval_index, result="remembered"):
    """
    에빙하우스 망각곡선 간격을 사용하여 다음 복습 날짜를 계산합니다

    Args:
        user: 사용자 인스턴스
        interval_index: 현재 간격 인덱스
        result: 복습 결과 ('remembered' 또는 'forgotten')

    Returns:
        tuple: (다음_복습_날짜, 새_간격_인덱스)
    """
    intervals = get_review_intervals(user)

    if result == "forgotten":
        # 실패 시 첫 번째 간격으로 리셋
        new_interval_index = 0
    else:
        # 성공 시 다음 간격으로 진행
        new_interval_index = min(interval_index + 1, len(intervals) - 1)

    # 간격을 일 단위로 가져오기
    interval_days = intervals[new_interval_index]
    next_review_date = timezone.now() + timedelta(days=interval_days)

    return next_review_date, new_interval_index


def calculate_success_rate(user, category=None, days=30):
    """
    지정된 기간 내 사용자의 성공률을 계산합니다

    Args:
        user: 사용자 인스턴스
        category: 카테고리 인스턴스 (선택)
        days: 조회할 일수 (기본: 30)

    Returns:
        tuple: (성공률, 총_복습_수, 상세정보)
    """
    from .models import ReviewHistory

    start_date = timezone.now().date() - timedelta(days=days)

    # 기본 쿼리셋
    reviews = ReviewHistory.objects.filter(user=user, review_date__date__gte=start_date)

    # 카테고리가 제공되면 필터링
    if category:
        reviews = reviews.filter(content__category=category)

    total_reviews = reviews.count()
    successful_reviews = reviews.filter(result="remembered").count()

    success_rate = (
        (successful_reviews / total_reviews * 100) if total_reviews > 0 else 0
    )

    # 결과별 분류가 포함된 상세 딕셔너리 생성
    details = {}
    for result_choice, _ in ReviewHistory.RESULT_CHOICES:
        count = reviews.filter(result=result_choice).count()
        details[result_choice] = count

    return round(success_rate, 1), total_reviews, details


def get_today_reviews_count(user, category=None):
    """
    사용자의 오늘 복습 수를 반환합니다

    대시보드와 복습 페이지 간 일관성을 보장하기 위해
    TodayReviewView에서 사용하는 로직과 일치해야 합니다.

    Args:
        user: 사용자 인스턴스
        category: 카테고리 인스턴스 (선택)

    Returns:
        int: 오늘 해야 할 복습 수 (아직 완료되지 않은 초기 복습 포함)
    """
    from datetime import timedelta

    from django.db.models import Q

    from .models import ReviewSchedule

    today = timezone.now().date()

    # 사용자의 구독 티어를 가져오고 연체 제한 결정 (TodayReviewView와 동일)
    max_overdue_days = SubscriptionService(user).get_max_review_interval()
    if not max_overdue_days:
        max_overdue_days = 7  # FREE 티어 기본값

    # 구독을 기반으로 연체 복습 마감일 계산
    cutoff_date = timezone.now() - timedelta(days=max_overdue_days)

    schedules = ReviewSchedule.objects.filter(user=user, is_active=True).filter(
        # TodayReviewView와 동일 로직: 오늘/연체 또는 초기 복습 미완료
        Q(next_review_date__date__lte=today, next_review_date__gte=cutoff_date)
        | Q(initial_review_completed=False)
    )

    if category:
        schedules = schedules.filter(content__category=category)

    return schedules.count()


def get_pending_reviews_count(user, category=None):
    """
    사용자의 대기 중인(연체된) 복습 수를 반환합니다

    Args:
        user: 사용자 인스턴스
        category: 카테고리 인스턴스 (선택)

    Returns:
        int: 대기 중인(연체된) 복습 수
    """
    from .models import ReviewSchedule

    today = timezone.now().date()
    schedules = ReviewSchedule.objects.filter(
        user=user, is_active=True, next_review_date__date__lt=today
    )

    if category:
        schedules = schedules.filter(content__category=category)

    return schedules.count()
