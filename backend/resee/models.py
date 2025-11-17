"""
Base model classes for the Resee application.
"""
from django.conf import settings
from django.db import models


class TimestampMixin(models.Model):
    """
    Abstract model that provides created_at and updated_at timestamps.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserOwnedMixin(models.Model):
    """
    Abstract model for models that belong to a user.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        abstract = True