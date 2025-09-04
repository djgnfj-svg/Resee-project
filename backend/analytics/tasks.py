"""
Celery tasks for business intelligence data collection and analysis
"""
import logging
from datetime import timedelta, date
from decimal import Decimal
from typing import Dict, Any

from celery import shared_task
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Sum, Q, F, Max
from django.db.models.functions import Coalesce
from django.utils import timezone

from accounts.models import Subscription
from content.models import Content
from review.models import ReviewHistory, ReviewSchedule
# from ai_review.models import AIUsageTracking  # Model doesn't exist yet
# Note: monitoring.models removed with monitoring app deletion

from .models import (
    LearningPattern, 
    # ContentEffectiveness,  # Commented out in models.py
    SubscriptionAnalytics, SystemUsageMetrics
)

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(name='bi.collect_daily_learning_patterns')
def collect_daily_learning_patterns(target_date=None):
    """
    Collect and update daily learning patterns for all users
    """
    if target_date is None:
        target_date = timezone.now().date()
    elif isinstance(target_date, str):
        from datetime import datetime
        target_date = datetime.fromisoformat(target_date).date()
    
    logger.info(f"Collecting learning patterns for {target_date}")
    
    users_processed = 0
    patterns_created = 0
    patterns_updated = 0
    
    try:
        # Get all users who had activity on the target date
        active_users = User.objects.filter(
            Q(contents__created_at__date=target_date) |
            Q(review_history__review_date__date=target_date) |
            Q(ai_usage_tracking__usage_date=target_date)
        ).distinct()
        
        for user in active_users:
            pattern_data = _collect_user_daily_pattern(user, target_date)
            
            # Get or create learning pattern
            pattern, created = LearningPattern.objects.get_or_create(
                user=user,
                date=target_date,
                defaults=pattern_data
            )
            
            if created:
                patterns_created += 1
                logger.debug(f"Created pattern for user {user.id} on {target_date}")
            else:
                # Update existing pattern with new data
                for key, value in pattern_data.items():
                    if hasattr(pattern, key):
                        setattr(pattern, key, value)
                pattern.save()
                patterns_updated += 1
                logger.debug(f"Updated pattern for user {user.id} on {target_date}")
            
            users_processed += 1
        
        logger.info(
            f"Learning pattern collection completed: "
            f"{users_processed} users processed, "
            f"{patterns_created} created, {patterns_updated} updated"
        )
        
        return {
            'date': target_date.isoformat(),
            'users_processed': users_processed,
            'patterns_created': patterns_created,
            'patterns_updated': patterns_updated
        }
        
    except Exception as e:
        logger.error(f"Error collecting learning patterns: {e}")
        raise


@shared_task(name='bi.update_content_effectiveness')
def update_content_effectiveness():
    """
    Update content effectiveness metrics for all content
    """
    logger.info("Starting content effectiveness update")
    
    updated_count = 0
    created_count = 0
    
    try:
        # Get all content that has reviews
        content_with_reviews = Content.objects.filter(
            reviews__isnull=False
        ).distinct()
        
        for content in content_with_reviews:
            effectiveness_data = _calculate_content_effectiveness(content)
            
            # Get or create effectiveness record
            effectiveness, created = ContentEffectiveness.objects.get_or_create(
                content=content,
                defaults=effectiveness_data
            )
            
            if created:
                created_count += 1
                logger.debug(f"Created effectiveness record for content {content.id}")
            else:
                # Update existing record
                for key, value in effectiveness_data.items():
                    if hasattr(effectiveness, key) and value is not None:
                        setattr(effectiveness, key, value)
                effectiveness.save()
                updated_count += 1
                logger.debug(f"Updated effectiveness record for content {content.id}")
        
        logger.info(
            f"Content effectiveness update completed: "
            f"{created_count} created, {updated_count} updated"
        )
        
        return {
            'created_count': created_count,
            'updated_count': updated_count
        }
        
    except Exception as e:
        logger.error(f"Error updating content effectiveness: {e}")
        raise


@shared_task(name='bi.update_subscription_analytics')
def update_subscription_analytics():
    """
    Update subscription analytics for all users with subscriptions
    """
    logger.info("Starting subscription analytics update")
    
    updated_count = 0
    created_count = 0
    
    try:
        # Get all active subscriptions
        active_subscriptions = Subscription.objects.filter(is_active=True)
        
        for subscription in active_subscriptions:
            analytics_data = _calculate_subscription_analytics(subscription.user, subscription)
            
            # Get or create analytics record
            analytics, created = SubscriptionAnalytics.objects.get_or_create(
                user=subscription.user,
                subscription_tier=subscription.tier,
                tier_start_date=subscription.created_at,
                defaults=analytics_data
            )
            
            if created:
                created_count += 1
                logger.debug(f"Created subscription analytics for user {subscription.user.id}")
            else:
                # Update existing record
                for key, value in analytics_data.items():
                    if hasattr(analytics, key) and value is not None:
                        setattr(analytics, key, value)
                analytics.save()
                updated_count += 1
                logger.debug(f"Updated subscription analytics for user {subscription.user.id}")
        
        logger.info(
            f"Subscription analytics update completed: "
            f"{created_count} created, {updated_count} updated"
        )
        
        return {
            'created_count': created_count,
            'updated_count': updated_count
        }
        
    except Exception as e:
        logger.error(f"Error updating subscription analytics: {e}")
        raise


@shared_task(name='bi.collect_system_metrics')
def collect_system_metrics(target_date=None):
    """
    Collect system-wide usage metrics
    """
    if target_date is None:
        target_date = timezone.now().date()
    elif isinstance(target_date, str):
        from datetime import datetime
        target_date = datetime.fromisoformat(target_date).date()
    
    logger.info(f"Collecting system metrics for {target_date}")
    
    try:
        metrics_data = _collect_system_metrics_data(target_date)
        
        # Get or create system metrics record
        metrics, created = SystemUsageMetrics.objects.get_or_create(
            date=target_date,
            defaults=metrics_data
        )
        
        if not created:
            # Update existing record
            for key, value in metrics_data.items():
                if hasattr(metrics, key) and value is not None:
                    setattr(metrics, key, value)
            metrics.save()
        
        action = "created" if created else "updated"
        logger.info(f"System metrics {action} for {target_date}")
        
        return {
            'date': target_date.isoformat(),
            'action': action,
            'metrics': metrics_data
        }
        
    except Exception as e:
        logger.error(f"Error collecting system metrics: {e}")
        raise


@shared_task(name='bi.cleanup_old_analytics_data')
def cleanup_old_analytics_data(days_to_keep=365):
    """
    Clean up old analytics data beyond retention period
    """
    cutoff_date = timezone.now().date() - timedelta(days=days_to_keep)
    
    logger.info(f"Cleaning up analytics data older than {cutoff_date}")
    
    try:
        # Clean up learning patterns
        deleted_patterns = LearningPattern.objects.filter(
            date__lt=cutoff_date
        ).delete()
        
        # Clean up system metrics
        deleted_metrics = SystemUsageMetrics.objects.filter(
            date__lt=cutoff_date
        ).delete()
        
        logger.info(
            f"Cleanup completed: "
            f"{deleted_patterns[0]} learning patterns, "
            f"{deleted_metrics[0]} system metrics deleted"
        )
        
        return {
            'cutoff_date': cutoff_date.isoformat(),
            'deleted_patterns': deleted_patterns[0],
            'deleted_metrics': deleted_metrics[0]
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up analytics data: {e}")
        raise


def _collect_user_daily_pattern(user, target_date) -> Dict[str, Any]:
    """Collect daily learning pattern data for a user"""
    
    # Content creation
    contents_created = Content.objects.filter(
        user=user,
        created_at__date=target_date
    ).count()
    
    # Reviews completed
    reviews = ReviewHistory.objects.filter(
        user=user,
        review_date__date=target_date
    )
    reviews_completed = reviews.count()
    
    # Success rate
    if reviews_completed > 0:
        successful_reviews = reviews.filter(result='remembered').count()
        success_rate = (successful_reviews / reviews_completed) * 100
        
        # Average review time
        avg_review_time = reviews.aggregate(
            avg_time=Coalesce(Avg('time_spent'), 0)
        )['avg_time'] or 0
    else:
        success_rate = 0.0
        avg_review_time = 0
    
    # AI questions generated - using ai_review models directly
    # Note: AIUsageTracking model doesn't exist, using alternative approach
    from ai_review.models import AIQuestion
    ai_questions = AIQuestion.objects.filter(
        content__author=user,
        created_at__date=target_date,
        is_active=True
    ).count()
    
    # Peak activity hour (from review times)
    peak_hour = None
    if reviews_completed > 0:
        hourly_activity = reviews.extra(
            select={'hour': "EXTRACT(hour FROM review_date)"}
        ).values('hour').annotate(count=Count('id')).order_by('-count')
        
        if hourly_activity:
            peak_hour = int(hourly_activity[0]['hour'])
    
    # Calculate consecutive days streak
    consecutive_days = _calculate_user_streak(user, target_date)
    
    return {
        'contents_created': contents_created,
        'reviews_completed': reviews_completed,
        'ai_questions_generated': ai_questions,
        'session_duration_minutes': 0,  # Would need session tracking
        'success_rate': round(success_rate, 2),
        'average_review_time_seconds': int(avg_review_time),
        'peak_activity_hour': peak_hour,
        'login_count': 1,  # Simplified - would need proper session tracking
        'consecutive_days': consecutive_days,
    }


def _calculate_content_effectiveness(content) -> Dict[str, Any]:
    """Calculate effectiveness metrics for a content item"""
    
    reviews = ReviewHistory.objects.filter(content=content)
    total_reviews = reviews.count()
    
    if total_reviews == 0:
        return {
            'total_reviews': 0,
            'successful_reviews': 0,
            'average_difficulty_rating': 3.0,
            'average_review_time_seconds': 0,
            'time_to_master_days': None,
            'ai_questions_generated': 0,
            'ai_questions_success_rate': 0.0,
            'last_reviewed': None,
            'abandonment_risk_score': 50.0,
        }
    
    successful_reviews = reviews.filter(result='remembered').count()
    
    # Average review time
    avg_review_time = reviews.aggregate(
        avg_time=Coalesce(Avg('time_spent'), 0)
    )['avg_time'] or 0
    
    # Time to master calculation
    time_to_master = _calculate_time_to_master(reviews)
    
    # AI questions for this content
    ai_questions_count = 0  # Would need to track AI questions per content
    
    # Last reviewed date
    last_reviewed = reviews.aggregate(
        last_date=Max('review_date')
    )['last_date']
    
    # Abandonment risk score
    abandonment_risk = _calculate_abandonment_risk(content, reviews, last_reviewed)
    
    # Average difficulty (would come from user ratings, defaulting to content difficulty)
    avg_difficulty = getattr(content, 'difficulty_level', 3.0)
    
    return {
        'total_reviews': total_reviews,
        'successful_reviews': successful_reviews,
        'average_difficulty_rating': avg_difficulty,
        'average_review_time_seconds': int(avg_review_time),
        'time_to_master_days': time_to_master,
        'ai_questions_generated': ai_questions_count,
        'ai_questions_success_rate': 0.0,  # Would need AI question tracking
        'last_reviewed': last_reviewed,
        'abandonment_risk_score': round(abandonment_risk, 2),
    }


def _calculate_subscription_analytics(user, subscription) -> Dict[str, Any]:
    """Calculate subscription analytics for a user"""
    
    # Basic subscription info
    tier_start = subscription.created_at
    
    # Usage metrics since subscription start
    content_created = Content.objects.filter(
        user=user,
        created_at__gte=tier_start
    ).count()
    
    reviews_completed = ReviewHistory.objects.filter(
        user=user,
        review_date__gte=tier_start
    ).count()
    
    # AI questions used - count from ai_review models
    from ai_review.models import AIQuestion
    ai_questions_used = AIQuestion.objects.filter(
        content__author=user,
        created_at__gte=tier_start,
        is_active=True
    ).count()
    
    # Days active (simplified)
    days_active = LearningPattern.objects.filter(
        user=user,
        date__gte=tier_start.date(),
        reviews_completed__gt=0
    ).count()
    
    # Average daily reviews
    subscription_days = (timezone.now() - tier_start).days + 1
    avg_daily_reviews = reviews_completed / subscription_days if subscription_days > 0 else 0
    
    # Feature adoption score (simplified)
    feature_score = min(100, 
        (content_created * 10) + 
        (min(reviews_completed, 100) * 0.5) + 
        (ai_questions_used * 2)
    )
    
    # Upgrade probability (simplified heuristic)
    if subscription.tier == 'FREE':
        upgrade_prob = min(90, reviews_completed * 2 + content_created * 5)
    elif subscription.tier == 'BASIC':
        upgrade_prob = min(90, ai_questions_used * 0.5 + reviews_completed * 0.3)
    else:
        upgrade_prob = 0  # Already at highest tier
    
    # Churn risk (inverse of activity)
    recent_activity = LearningPattern.objects.filter(
        user=user,
        date__gte=timezone.now().date() - timedelta(days=7),
        reviews_completed__gt=0
    ).count()
    
    churn_risk = max(0, 100 - (recent_activity * 15) - (avg_daily_reviews * 10))
    
    return {
        'tier_start_date': tier_start,
        'total_content_created': content_created,
        'total_reviews_completed': reviews_completed,
        'total_ai_questions_used': ai_questions_used,
        'total_session_time_hours': 0.0,  # Would need session tracking
        'days_active': days_active,
        'average_daily_reviews': round(avg_daily_reviews, 2),
        'feature_adoption_score': round(feature_score, 2),
        'upgrade_probability': round(upgrade_prob, 2),
        'churn_risk_score': round(churn_risk, 2),
    }


def _collect_system_metrics_data(target_date) -> Dict[str, Any]:
    """Collect system-wide metrics for a given date"""
    
    # User metrics
    total_users = User.objects.count()
    active_users_daily = User.objects.filter(
        last_login__date=target_date
    ).count()
    new_users = User.objects.filter(
        date_joined__date=target_date
    ).count()
    
    # Subscription metrics
    active_subs = Subscription.objects.filter(is_active=True)
    tier_counts = active_subs.values('tier').annotate(count=Count('id'))
    
    free_users = total_users - active_subs.count()
    basic_users = next((item['count'] for item in tier_counts if item['tier'] == 'BASIC'), 0)
    pro_users = next((item['count'] for item in tier_counts if item['tier'] == 'PRO'), 0)
    
    # Revenue
    subscription_revenue = active_subs.aggregate(
        total=Coalesce(Sum('amount_paid'), Decimal('0.00'))
    )['total'] or Decimal('0.00')
    
    # Content metrics
    content_created = Content.objects.filter(
        created_at__date=target_date
    ).count()
    
    reviews_completed = ReviewHistory.objects.filter(
        review_date__date=target_date
    ).count()
    
    # Success rate
    if reviews_completed > 0:
        successful_reviews = ReviewHistory.objects.filter(
            review_date__date=target_date,
            result='remembered'
        ).count()
        avg_success_rate = (successful_reviews / reviews_completed) * 100
    else:
        avg_success_rate = 0.0
    
    # AI metrics - simplified approach using existing models
    from ai_review.models import AIQuestion
    ai_questions_count = AIQuestion.objects.filter(
        created_at__date=target_date,
        is_active=True
    ).count()
    
    ai_usage = {
        'questions': ai_questions_count,
        'cost': Decimal('0.0000'),  # Cost tracking not implemented
        'tokens': 0  # Token tracking not implemented
    }
    
    # System performance metrics
    api_metrics = APIMetrics.objects.filter(
        timestamp__date=target_date
    ).aggregate(
        avg_response_time=Coalesce(Avg('response_time_ms'), 0),
        error_count=Count('id', filter=Q(status_code__gte=400)),
        total_requests=Count('id')
    )
    
    avg_response_time = int(api_metrics['avg_response_time'] or 0)
    error_rate = (api_metrics['error_count'] / api_metrics['total_requests'] * 100) if api_metrics['total_requests'] > 0 else 0
    
    # System uptime (simplified)
    uptime = 100.0  # Would be calculated from actual monitoring data
    
    return {
        'total_users': total_users,
        'active_users_daily': active_users_daily,
        'new_users': new_users,
        'churned_users': 0,  # Would need proper tracking
        'free_users': free_users,
        'basic_users': basic_users,
        'pro_users': pro_users,
        'subscription_revenue_usd': subscription_revenue,
        'total_content_created': content_created,
        'total_reviews_completed': reviews_completed,
        'average_success_rate': round(avg_success_rate, 2),
        'ai_questions_generated': ai_usage['questions'],
        'ai_cost_usd': ai_usage['cost'],
        'ai_tokens_used': ai_usage['tokens'],
        'average_api_response_time_ms': avg_response_time,
        'error_rate_percentage': round(error_rate, 2),
        'uptime_percentage': uptime,
    }


def _calculate_user_streak(user, target_date):
    """Calculate consecutive learning days streak for user up to target_date"""
    
    # Get all learning pattern dates for user in reverse chronological order
    patterns = LearningPattern.objects.filter(
        user=user,
        date__lte=target_date,
        reviews_completed__gt=0
    ).order_by('-date').values_list('date', flat=True)
    
    if not patterns:
        return 0
    
    patterns_list = list(patterns)
    streak = 1  # At least 1 day if we have any data
    
    # Count consecutive days
    for i in range(1, len(patterns_list)):
        current_date = patterns_list[i]
        previous_date = patterns_list[i-1]
        
        # Check if dates are consecutive
        if (previous_date - current_date).days == 1:
            streak += 1
        else:
            break  # Streak broken
    
    return streak


def _calculate_time_to_master(reviews):
    """Calculate days taken to master content (3 consecutive successful reviews)"""
    
    # Order reviews by date
    review_list = list(reviews.order_by('review_date').values('review_date', 'result'))
    
    if len(review_list) < 3:
        return None
    
    consecutive_success = 0
    first_review_date = review_list[0]['review_date']
    
    for review in review_list:
        if review['result'] == 'remembered':
            consecutive_success += 1
            if consecutive_success >= 3:
                mastery_date = review['review_date']
                return (mastery_date.date() - first_review_date.date()).days
        else:
            consecutive_success = 0  # Reset counter
    
    return None  # Not mastered yet


def _calculate_abandonment_risk(content, reviews, last_reviewed):
    """Calculate abandonment risk score for content"""
    
    if not last_reviewed:
        return 100.0  # Never reviewed
    
    # Days since last review
    days_since_review = (timezone.now().date() - last_reviewed.date()).days
    
    # Base risk increases with time
    risk = min(days_since_review * 2, 100)
    
    # Adjust based on review history
    total_reviews = reviews.count()
    if total_reviews > 0:
        success_rate = (reviews.filter(result='remembered').count() / total_reviews) * 100
        # Higher success rate reduces risk
        risk = risk * (1 - (success_rate / 200))  # Scale down based on success
    
    # Content age factor
    content_age_days = (timezone.now().date() - content.created_at.date()).days
    if content_age_days > 30 and total_reviews < 3:
        risk += 20  # Old content with few reviews is higher risk
    
    return min(100, max(0, risk))