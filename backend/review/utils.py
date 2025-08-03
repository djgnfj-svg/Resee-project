"""
Review system utility functions
"""
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import ReviewHistory


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
        SubscriptionTier.FREE: [1, 3, 7],  # Basic spaced repetition (max 7 days)
        SubscriptionTier.BASIC: [1, 3, 7, 14, 30],  # Medium-term memory (max 30 days)
        SubscriptionTier.PREMIUM: [1, 3, 7, 14, 30, 60],  # Long-term memory (max 60 days)
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


def calculate_success_rate(user, category=None, days=30):
    """
    Calculate success rate for a user within specified days
    
    Args:
        user: User instance
        category: Category instance (optional)
        days: Number of days to look back (default: 30)
    
    Returns:
        tuple: (success_rate, total_reviews, successful_reviews)
    """
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
    
    return round(success_rate, 1), total_reviews, successful_reviews


def get_today_reviews_count(user, category=None):
    """
    Get count of today's reviews for a user
    
    Args:
        user: User instance
        category: Category instance (optional)
    
    Returns:
        int: Number of reviews due today
    """
    from .models import ReviewSchedule
    
    today = timezone.now().date()
    schedules = ReviewSchedule.objects.filter(
        user=user,
        is_active=True,
        next_review_date__date__lte=today
    )
    
    if category:
        schedules = schedules.filter(content__category=category)
    
    return schedules.count()


def get_pending_reviews_count(user, category=None):
    """
    Get count of pending reviews for a user
    
    Args:
        user: User instance
        category: Category instance (optional)
    
    Returns:
        int: Number of pending reviews
    """
    from .models import ReviewSchedule
    
    today = timezone.now().date()
    schedules = ReviewSchedule.objects.filter(
        user=user,
        is_active=True,
        next_review_date__date__gt=today
    )
    
    if category:
        schedules = schedules.filter(content__category=category)
    
    return schedules.count()