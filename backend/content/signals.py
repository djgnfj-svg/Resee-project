"""
Signals for content app
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Content


@receiver(post_save, sender=Content)
def create_review_schedule_on_content_creation(sender, instance, created, **kwargs):
    """Create review schedule when new content is created"""
    if created:
        # Import here to avoid circular imports
        from review.models import ReviewSchedule
        from django.utils import timezone

        # Create review schedule (available immediately, +1 second for DB constraint)
        next_review_date = timezone.now() + timezone.timedelta(seconds=1)
        ReviewSchedule.objects.create(
            content=instance,
            user=instance.author,
            next_review_date=next_review_date,
            interval_index=0  # First interval
        )