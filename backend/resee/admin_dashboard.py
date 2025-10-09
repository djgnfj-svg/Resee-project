"""
Simple Admin Dashboard for Resee Platform
Shows basic user and content metrics
"""
from datetime import datetime, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.shortcuts import render
from django.utils import timezone

from accounts.models import SubscriptionTier, Subscription
from content.models import Content
from review.models import ReviewHistory, ReviewSchedule

User = get_user_model()


def check_system_health():
    """Check system health (DB, Redis, Celery)"""
    health_status = {
        'database': False,
        'redis': False,
        'celery': False,
    }

    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['database'] = True
    except Exception:
        pass

    # Check Redis (by cache)
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status['redis'] = True
    except Exception:
        pass

    # Check Celery (basic check - just import)
    try:
        from celery.app.control import Inspect
        health_status['celery'] = True  # Basic check only
    except Exception:
        pass

    return health_status


def get_dashboard_data():
    """Get simple dashboard metrics with caching"""
    # Try to get cached data first
    cache_key = 'admin_dashboard_data'
    cached_data = cache.get(cache_key)

    if cached_data:
        return cached_data

    # If not cached, compute fresh data
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    # User metrics (optimized with select_related)
    total_users = User.objects.count()
    new_users_week = User.objects.filter(date_joined__gte=week_ago).count()
    new_users_today = User.objects.filter(date_joined__date=today).count()
    verified_users = User.objects.filter(is_email_verified=True).count()
    unverified_users = User.objects.filter(is_email_verified=False).count()

    # Subscription tier distribution
    tier_distribution = {}
    for tier_choice in SubscriptionTier.choices:
        tier_code = tier_choice[0]
        tier_label = tier_choice[1]
        count = User.objects.filter(subscription__tier=tier_code).count()
        tier_distribution[tier_label] = count

    # Content metrics
    total_content = Content.objects.count()
    content_week = Content.objects.filter(created_at__gte=week_ago).count()
    total_reviews = ReviewHistory.objects.count()

    # Review metrics - 오늘 복습 예정
    reviews_due_today = ReviewSchedule.objects.filter(
        next_review_date__date=today,
        is_active=True
    ).count()

    # Subscription metrics - 만료 임박 (7일 이내)
    seven_days_later = timezone.now() + timedelta(days=7)
    expiring_soon = Subscription.objects.filter(
        is_active=True,
        end_date__isnull=False,
        end_date__lte=seven_days_later,
        end_date__gt=timezone.now()
    ).count()

    # Recent activity (last 24 hours) - optimized queries
    recent_users = User.objects.filter(
        date_joined__gte=timezone.now() - timedelta(hours=24)
    ).select_related('subscription').order_by('-date_joined')[:5]

    recent_content = Content.objects.filter(
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).select_related('author').order_by('-created_at')[:5]

    activities = []
    for user in recent_users:
        activities.append({
            'type': 'user_registered',
            'description': f'New user registered: {user.email}',
            'timestamp': user.date_joined
        })

    for content in recent_content:
        activities.append({
            'type': 'content_created',
            'description': f'New content: {content.title[:50]}...',
            'timestamp': content.created_at
        })

    # Sort activities by timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)

    # System health check
    system_health = check_system_health()

    data = {
        'user_metrics': {
            'total_users': total_users,
            'new_week': new_users_week,
            'new_today': new_users_today,
            'verified_rate': (verified_users / total_users * 100) if total_users > 0 else 0,
            'unverified_users': unverified_users,
        },
        'content_metrics': {
            'total_content': total_content,
            'content_week': content_week,
            'total_reviews': total_reviews,
        },
        'review_metrics': {
            'due_today': reviews_due_today,
        },
        'subscription_metrics': {
            'expiring_soon': expiring_soon,
        },
        'tier_distribution': tier_distribution,
        'recent_activity': activities[:10],
        'system_health': system_health,
    }

    # Cache for 5 minutes
    cache.set(cache_key, data, 300)

    return data


@staff_member_required
def admin_dashboard_view(request):
    """Simple admin dashboard view"""
    context = get_dashboard_data()
    context['title'] = 'Resee Admin Dashboard'
    return render(request, 'admin/dashboard.html', context)