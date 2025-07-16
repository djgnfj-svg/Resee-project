"""
Review system utility functions
"""
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import ReviewHistory


def get_review_intervals():
    """Get review intervals from settings with fallback"""
    return getattr(settings, 'REVIEW_INTERVALS', [1, 3, 7, 14, 30])


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