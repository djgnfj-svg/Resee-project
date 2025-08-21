"""
Signal handlers for alert system
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from .models import AlertRule

logger = logging.getLogger(__name__)


@receiver(post_save, sender=AlertRule)
def invalidate_alert_rules_cache(sender, instance, created, **kwargs):
    """
    Clear cached alert rules when they are created or updated
    """
    cache.delete('active_alert_rules')
    cache.delete(f'alert_rule_{instance.id}')
    
    if created:
        logger.info(f"New alert rule created: {instance.name}")
    else:
        logger.info(f"Alert rule updated: {instance.name}")


@receiver(post_delete, sender=AlertRule)
def invalidate_alert_rules_cache_on_delete(sender, instance, **kwargs):
    """
    Clear cached alert rules when they are deleted
    """
    cache.delete('active_alert_rules')
    cache.delete(f'alert_rule_{instance.id}')
    
    logger.info(f"Alert rule deleted: {instance.name}")