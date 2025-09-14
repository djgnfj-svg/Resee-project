"""
Simple Admin Dashboard for Resee Platform
Shows basic user and content metrics
"""
from datetime import datetime, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.utils import timezone

from content.models import Content
from review.models import ReviewHistory

User = get_user_model()


def get_dashboard_data():
    """Get simple dashboard metrics"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    # User metrics
    total_users = User.objects.count()
    new_users_week = User.objects.filter(date_joined__gte=week_ago).count()
    verified_users = User.objects.filter(is_email_verified=True).count()

    # Content metrics
    total_content = Content.objects.count()
    content_week = Content.objects.filter(created_at__gte=week_ago).count()
    total_reviews = ReviewHistory.objects.count()

    # Recent activity (last 24 hours)
    recent_users = User.objects.filter(
        date_joined__gte=timezone.now() - timedelta(hours=24)
    ).order_by('-date_joined')[:5]

    recent_content = Content.objects.filter(
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).order_by('-created_at')[:5]

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

    return {
        'user_metrics': {
            'total_users': total_users,
            'new_week': new_users_week,
            'verified_rate': (verified_users / total_users * 100) if total_users > 0 else 0,
        },
        'content_metrics': {
            'total_content': total_content,
            'content_week': content_week,
            'total_reviews': total_reviews,
        },
        'recent_activity': activities[:10]
    }


@staff_member_required
def admin_dashboard_view(request):
    """Simple admin dashboard view"""
    context = get_dashboard_data()
    context['title'] = 'Resee Admin Dashboard'
    return render(request, 'admin/dashboard.html', context)