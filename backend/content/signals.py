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
        from review.tasks import create_review_schedule_for_content

        # Create review schedule asynchronously
        create_review_schedule_for_content.delay(
            content_id=instance.id,
            user_id=instance.author.id
        )