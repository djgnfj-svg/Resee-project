"""
Review system utility functions
"""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import ReviewHistory
from accounts.subscription.services import SubscriptionService


def get_review_intervals(user=None):
    """Get review intervals based on user's subscription tier using Ebbinghaus forgetting curve
    
    Based on Hermann Ebbinghaus's research on optimal spaced repetition intervals:
    - 1 day: Initial reinforcement
    - 3 days: Short-term consolidation  
    - 7 days: Working memory to long-term transfer
    - 14 days: Long-term memory strengthening
    - 30 days: Monthly reinforcement
    - 60 days: Bi-monthly consolidation
    - 120 days: Quarterly review (4 months)
    - 180 days: Semi-annual review (6 months)
    
    Args:
        user: User instance (optional). If not provided, returns default intervals.
    
    Returns:
        list: Review intervals in days based on subscription tier
    """
    # Return intervals based on subscription tier
    from accounts.models import SubscriptionTier

    # Ebbinghaus-optimized intervals for each tier
    tier_intervals = {
        SubscriptionTier.FREE: [1, 3],  # Basic spaced repetition (max 3 days)
        SubscriptionTier.BASIC: [1, 3, 7, 14, 30, 60, 90],  # Medium-term memory (max 90 days)
        SubscriptionTier.PRO: [1, 3, 7, 14, 30, 60, 120, 180],  # Complete long-term retention (max 180 days)
    }
    
    # Default to free tier intervals if no user
    if not user:
        return tier_intervals[SubscriptionTier.FREE]
    
    # Check if user has active subscription
    if not hasattr(user, 'subscription'):
        return tier_intervals[SubscriptionTier.FREE]
    
    subscription = user.subscription
    
    # Check if subscription is active and not expired
    if not subscription.is_active or subscription.is_expired():
        return tier_intervals[SubscriptionTier.FREE]
    
    # Return intervals for user's tier
    return tier_intervals.get(subscription.tier, tier_intervals[SubscriptionTier.FREE])


def calculate_next_review_date(user, interval_index, result='remembered'):
    """
    Calculate next review date using Ebbinghaus forgetting curve intervals

    Args:
        user: User instance
        interval_index: Current interval index
        result: Review result ('remembered' or 'forgotten')

    Returns:
        tuple: (next_review_date, new_interval_index)
    """
    intervals = get_review_intervals(user)

    if result == 'forgotten':
        # Reset to first interval on failure
        new_interval_index = 0
    else:
        # Progress to next interval on success
        new_interval_index = min(interval_index + 1, len(intervals) - 1)

    # Get the interval in days
    interval_days = intervals[new_interval_index]
    next_review_date = timezone.now() + timedelta(days=interval_days)

    return next_review_date, new_interval_index


def calculate_success_rate(user, category=None, days=30):
    """
    Calculate success rate for a user within specified days

    Args:
        user: User instance
        category: Category instance (optional)
        days: Number of days to look back (default: 30)

    Returns:
        tuple: (success_rate, total_reviews, details)
    """
    from .models import ReviewHistory

    start_date = timezone.now().date() - timedelta(days=days)

    # Base queryset
    reviews = ReviewHistory.objects.filter(
        user=user,
        review_date__date__gte=start_date
    )

    # Filter by category if provided
    if category:
        reviews = reviews.filter(content__category=category)

    total_reviews = reviews.count()
    successful_reviews = reviews.filter(result='remembered').count()

    success_rate = (successful_reviews / total_reviews * 100) if total_reviews > 0 else 0

    # Create details dict with breakdown by result
    details = {}
    for result_choice, _ in ReviewHistory.RESULT_CHOICES:
        count = reviews.filter(result=result_choice).count()
        details[result_choice] = count

    return round(success_rate, 1), total_reviews, details


def get_today_reviews_count(user, category=None):
    """
    Get count of today's reviews for a user

    This function should match the logic used in TodayReviewView to ensure consistency
    between dashboard and review page counts.

    Args:
        user: User instance
        category: Category instance (optional)

    Returns:
        int: Number of reviews due today (including initial reviews not yet completed)
    """
    from django.db.models import Q
    from datetime import timedelta
    from .models import ReviewSchedule

    today = timezone.now().date()

    # Get user's subscription tier and determine overdue limit (same as TodayReviewView)
    max_overdue_days = SubscriptionService(user).get_max_review_interval()
    if not max_overdue_days:
        max_overdue_days = 7  # Default to FREE tier

    # Calculate cutoff date for overdue reviews based on subscription
    cutoff_date = timezone.now() - timedelta(days=max_overdue_days)

    schedules = ReviewSchedule.objects.filter(
        user=user,
        is_active=True
    ).filter(
        # Same logic as TodayReviewView: due today/overdue OR initial review not completed
        Q(next_review_date__date__lte=today, next_review_date__gte=cutoff_date) |
        Q(initial_review_completed=False)
    )

    if category:
        schedules = schedules.filter(content__category=category)

    return schedules.count()


def get_pending_reviews_count(user, category=None):
    """
    Get count of pending (overdue) reviews for a user

    Args:
        user: User instance
        category: Category instance (optional)

    Returns:
        int: Number of pending (overdue) reviews
    """
    from .models import ReviewSchedule

    today = timezone.now().date()
    schedules = ReviewSchedule.objects.filter(
        user=user,
        is_active=True,
        next_review_date__date__lt=today
    )

    if category:
        schedules = schedules.filter(content__category=category)

    return schedules.count()