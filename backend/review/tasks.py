"""
Celery tasks for review app
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from content.models import Content
from .models import ReviewSchedule

User = get_user_model()


@shared_task
def create_review_schedule_for_content(content_id, user_id):
    """Create initial review schedule when content is created"""
    try:
        content = Content.objects.get(id=content_id)
        user = User.objects.get(id=user_id)
        
        # Create review schedule with first interval (1 day)
        next_review_date = timezone.now() + timedelta(days=1)
        
        schedule, created = ReviewSchedule.objects.get_or_create(
            content=content,
            user=user,
            defaults={
                'next_review_date': next_review_date,
                'interval_index': 0,
                'is_active': True
            }
        )
        
        return f"Review schedule created for content '{content.title}'"
    except (Content.DoesNotExist, User.DoesNotExist) as e:
        return f"Error creating review schedule: {str(e)}"


@shared_task
def send_daily_review_notifications():
    """Send daily review notifications to users"""
    today = timezone.now().date()
    
    # Get all users who have reviews due today
    due_schedules = ReviewSchedule.objects.filter(
        is_active=True,
        next_review_date__date__lte=today
    ).select_related('user', 'content')
    
    # Group by user
    user_schedules = {}
    for schedule in due_schedules:
        user_id = schedule.user.id
        if user_id not in user_schedules:
            user_schedules[user_id] = {
                'user': schedule.user,
                'schedules': []
            }
        user_schedules[user_id]['schedules'].append(schedule)
    
    # Send notifications (for now, just log to console)
    notifications_sent = 0
    for user_id, data in user_schedules.items():
        user = data['user']
        count = len(data['schedules'])
        
        if user.notification_enabled:
            # TODO: Send actual email notification
            print(f"📧 Notification sent to {user.email}: {count} items to review today")
            notifications_sent += 1
    
    return f"Sent notifications to {notifications_sent} users"


@shared_task
def cleanup_old_review_history():
    """Clean up old review history records (older than 1 year)"""
    from .models import ReviewHistory
    
    one_year_ago = timezone.now() - timedelta(days=365)
    
    deleted_count, _ = ReviewHistory.objects.filter(
        review_date__lt=one_year_ago
    ).delete()
    
    return f"Cleaned up {deleted_count} old review history records"


@shared_task
def update_review_schedules():
    """Update review schedules based on completion"""
    # This is a placeholder task that could be used to:
    # 1. Check for completed reviews
    # 2. Update schedules accordingly
    # 3. Handle adaptive spacing based on performance
    
    return "Review schedules updated"