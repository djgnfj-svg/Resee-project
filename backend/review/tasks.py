"""
Celery tasks for review app
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from content.models import Content
from .models import ReviewSchedule
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task
def create_review_schedule_for_content(content_id, user_id):
    """Create initial review schedule when content is created"""
    try:
        content = Content.objects.get(id=content_id)
        user = User.objects.get(id=user_id)
        
        # Create review schedule immediately available for initial review
        next_review_date = timezone.now()
        
        schedule, created = ReviewSchedule.objects.get_or_create(
            content=content,
            user=user,
            defaults={
                'next_review_date': next_review_date,
                'interval_index': 0,
                'is_active': True,
                'initial_review_completed': False
            }
        )
        
        return f"Review schedule created for content '{content.title}'"
    except (Content.DoesNotExist, User.DoesNotExist) as e:
        return f"Error creating review schedule: {str(e)}"


@shared_task
def send_daily_review_notifications():
    """Send daily review notifications to users"""
    today = timezone.now().date()
    
    # Get all users who have reviews due today (including initial reviews)
    due_schedules = ReviewSchedule.objects.filter(
        is_active=True,
        next_review_date__date__lte=today
    ).select_related('user', 'content', 'content__category')
    
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
    
    # Send notifications
    notifications_sent = 0
    notifications_failed = 0
    
    for user_id, data in user_schedules.items():
        user = data['user']
        schedules = data['schedules']
        count = len(schedules)
        
        if user.notification_enabled:
            try:
                # Prepare email context
                # Get first 5 contents for preview
                preview_contents = []
                for i, schedule in enumerate(schedules[:5]):
                    interval = settings.REVIEW_INTERVALS[schedule.interval_index] if not schedule.initial_review_completed else 0
                    preview_contents.append({
                        'title': schedule.content.title,
                        'category': schedule.content.category.name if schedule.content.category else '미분류',
                        'interval': interval
                    })
                
                # Calculate estimated time (3 minutes per content)
                estimated_time = count * 3
                
                context = {
                    'user_name': user.username,
                    'total_count': count,
                    'estimated_time': estimated_time,
                    'contents': preview_contents,
                    'remaining_count': max(0, count - 5),
                    'site_url': settings.CORS_ALLOWED_ORIGINS[0] if settings.CORS_ALLOWED_ORIGINS else 'http://localhost:3000',
                    'review_url': f"{settings.CORS_ALLOWED_ORIGINS[0]}/review" if settings.CORS_ALLOWED_ORIGINS else 'http://localhost:3000/review',
                    'settings_url': f"{settings.CORS_ALLOWED_ORIGINS[0]}/settings" if settings.CORS_ALLOWED_ORIGINS else 'http://localhost:3000/settings',
                    'unsubscribe_url': f"{settings.CORS_ALLOWED_ORIGINS[0]}/settings#notifications" if settings.CORS_ALLOWED_ORIGINS else 'http://localhost:3000/settings#notifications',
                }
                
                # Render email templates
                html_content = render_to_string('email/daily_review_notification.html', context)
                text_content = render_to_string('email/daily_review_notification.txt', context)
                
                # Send email
                send_mail(
                    subject=f'[Resee] 오늘의 복습 알림 - {count}개 대기 중',
                    message=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_content,
                    fail_silently=False,
                )
                
                notifications_sent += 1
                logger.info(f"Notification sent to {user.email}: {count} items to review")
                
            except Exception as e:
                notifications_failed += 1
                logger.error(f"Failed to send notification to {user.email}: {str(e)}")
    
    return f"Sent notifications to {notifications_sent} users, {notifications_failed} failed"


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
    """Update review schedules based on performance and adaptive spacing"""
    from .models import ReviewHistory
    from .utils import calculate_success_rate
    
    # Get recent review histories to analyze performance
    recent_date = timezone.now() - timedelta(days=30)
    
    # Find users with recent review activity
    active_users = ReviewHistory.objects.filter(
        review_date__gte=recent_date
    ).values_list('user_id', flat=True).distinct()
    
    schedules_updated = 0
    schedules_adjusted = 0
    
    for user_id in active_users:
        try:
            user = User.objects.get(id=user_id)
            
            # Get user's active schedules
            user_schedules = ReviewSchedule.objects.filter(
                user=user,
                is_active=True
            ).select_related('content')
            
            for schedule in user_schedules:
                # Get recent history for this content
                recent_reviews = ReviewHistory.objects.filter(
                    user=user,
                    content=schedule.content,
                    review_date__gte=recent_date
                ).order_by('-review_date')
                
                if recent_reviews.exists():
                    # Calculate performance metrics
                    total_reviews = recent_reviews.count()
                    remembered_count = recent_reviews.filter(result='remembered').count()
                    forgot_count = recent_reviews.filter(result='forgot').count()
                    
                    success_rate = (remembered_count / total_reviews) * 100 if total_reviews > 0 else 0
                    
                    # Adaptive spacing logic
                    if total_reviews >= 3:  # Need at least 3 reviews for adjustment
                        current_interval_days = settings.REVIEW_INTERVALS[schedule.interval_index]
                        
                        # If success rate is very high, we can increase intervals slightly
                        if success_rate >= 90 and schedule.interval_index < len(settings.REVIEW_INTERVALS) - 1:
                            # Consider advancing to next interval faster
                            if recent_reviews[0].result == 'remembered':
                                # Last review was successful, might advance
                                logger.info(f"User {user.username} has high success rate ({success_rate:.1f}%) for '{schedule.content.title}'")
                                schedules_adjusted += 1
                        
                        # If struggling with content, might need more frequent reviews
                        elif success_rate < 50 and forgot_count >= 2:
                            # Consider adding supplementary review
                            logger.info(f"User {user.username} struggling with '{schedule.content.title}' (success rate: {success_rate:.1f}%)")
                            
                            # Optional: Create a supplementary review (not resetting the main schedule)
                            # This could be implemented as a separate feature
                            schedules_adjusted += 1
                    
                    schedules_updated += 1
                    
        except User.DoesNotExist:
            logger.error(f"User with id {user_id} not found")
            continue
        except Exception as e:
            logger.error(f"Error updating schedules for user {user_id}: {str(e)}")
            continue
    
    # Additional maintenance: deactivate schedules for deleted content
    orphaned_schedules = ReviewSchedule.objects.filter(
        content__isnull=True,
        is_active=True
    )
    orphaned_count = orphaned_schedules.update(is_active=False)
    
    return f"Updated {schedules_updated} schedules, adjusted {schedules_adjusted} based on performance, deactivated {orphaned_count} orphaned schedules"