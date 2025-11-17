"""
Signals for content app
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Content

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Content)
def create_review_schedule_on_content_creation(sender, instance, created, **kwargs):
    """Create review schedule when new content is created"""
    if created:
        # Import here to avoid circular imports
        from django.utils import timezone

        from review.models import ReviewSchedule

        # Create review schedule (available immediately, +1 second for DB constraint)
        next_review_date = timezone.now() + timezone.timedelta(seconds=1)
        ReviewSchedule.objects.create(
            content=instance,
            user=instance.author,
            next_review_date=next_review_date,
            interval_index=0  # First interval
        )


@receiver(post_save, sender=Content)
def generate_mc_choices_for_multiple_choice(sender, instance, created, **kwargs):
    """Generate multiple choice options when multiple_choice content is created"""
    if created and instance.review_mode == 'multiple_choice' and not instance.mc_choices:
        # Import here to avoid circular imports
        from ai_services import generate_multiple_choice_options

        logger.info(f"Generating MC choices for content {instance.id}: {instance.title}")

        try:
            mc_options = generate_multiple_choice_options(instance.title, instance.content)
            if mc_options:
                instance.mc_choices = mc_options
                instance.save(update_fields=['mc_choices'])
                logger.info(f"Successfully generated MC choices for content {instance.id}")
            else:
                logger.warning(f"Failed to generate MC options for content {instance.id}")
        except Exception as e:
            logger.error(f"Error generating MC options for content {instance.id}: {e}", exc_info=True)
