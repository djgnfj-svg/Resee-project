"""
Base model classes for the Resee application.
"""
from django.db import models
from django.contrib.auth.models import User


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
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class BaseModel(TimestampMixin):
    """
    Base model that includes timestamps.
    Use this for models that don't need user ownership.
    """
    class Meta:
        abstract = True


class BaseUserModel(TimestampMixin, UserOwnedMixin):
    """
    Base model for user-owned entities with timestamps.
    """
    class Meta:
        abstract = True