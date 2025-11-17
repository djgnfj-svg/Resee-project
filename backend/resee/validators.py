"""
Common validation utilities and validators with enhanced data integrity
"""
import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response


def validate_required_fields(data, required_fields):
    """
    Validate that all required fields are present in data

    Args:
        data (dict): Data to validate
        required_fields (list): List of required field names

    Raises:
        ValidationError: If any required field is missing
    """
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            missing_fields.append(field)

    if missing_fields:
        raise ValidationError(
            f"Required fields missing: {', '.join(missing_fields)}"
        )


def validate_choice_field(value, choices, field_name=None):
    """
    Validate that value is in allowed choices

    Args:
        value: Value to validate
        choices: List or tuple of valid choices
        field_name: Name of the field (for error message)

    Raises:
        ValidationError: If value is not in choices
    """
    valid_choices = [choice[0] if isinstance(choice, tuple) else choice for choice in choices]

    if value not in valid_choices:
        field_part = f" for {field_name}" if field_name else ""
        raise ValidationError(
            f"Invalid choice{field_part}. Must be one of: {', '.join(map(str, valid_choices))}"
        )


def validate_positive_integer(value, field_name=None):
    """
    Validate that value is a positive integer

    Args:
        value: Value to validate
        field_name: Name of the field (for error message)

    Raises:
        ValidationError: If value is not a positive integer
    """
    try:
        int_value = int(value)
        if int_value <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        field_part = f" for {field_name}" if field_name else ""
        raise ValidationError(f"Value{field_part} must be a positive integer")


def handle_validation_error(func):
    """
    Decorator to handle ValidationError and return proper API response

    Usage:
        @handle_validation_error
        def create(self, request, *args, **kwargs):
            # Your view logic here
            return super().create(request, *args, **kwargs)
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    return wrapper


def validate_subscription_tier_consistency(user, tier):
    """Validate subscription tier changes are logical"""
    if not hasattr(user, 'subscription'):
        return  # First subscription is always valid

    current_tier = user.subscription.tier
    tier_hierarchy = {'free': 0, 'basic': 1, 'pro': 2}
    current_level = tier_hierarchy.get(current_tier, 0)
    new_level = tier_hierarchy.get(tier, 0)

    # Log suspicious downgrades for monitoring
    if new_level < current_level:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'User {user.email} downgrading from {current_tier} to {tier}')


def validate_review_interval_index(interval_index, user=None):
    """Validate that interval index is within allowed range for user's subscription"""
    if interval_index < 0:
        raise ValidationError(
            _('Interval index cannot be negative.'),
            code='negative_interval'
        )

    if user:
        from review.utils import get_review_intervals
        allowed_intervals = get_review_intervals(user)

        if interval_index >= len(allowed_intervals):
            raise ValidationError(
                _('Interval index %(index)s exceeds maximum allowed for subscription (%(max)s).'),
                params={'index': interval_index, 'max': len(allowed_intervals) - 1},
                code='interval_exceeds_subscription'
            )


def validate_content_length(content):
    """Validate content length is reasonable"""
    if not content or not content.strip():
        raise ValidationError(
            _('Content cannot be empty.'),
            code='empty_content'
        )

    if len(content) < 1:  # 최소 1글자 이상
        raise ValidationError(
            _('Content must be at least 1 character long.'),
            code='content_too_short'
        )

    if len(content) > 50000:  # 50KB limit
        raise ValidationError(
            _('Content cannot exceed 50,000 characters.'),
            code='content_too_long'
        )


def validate_weekly_goal(goal):
    """Validate weekly goal is reasonable"""
    if goal < 1:
        raise ValidationError(
            _('Weekly goal must be at least 1.'),
            code='goal_too_low'
        )

    if goal > 50:  # Reasonable upper limit
        raise ValidationError(
            _('Weekly goal cannot exceed 50 reviews.'),
            code='goal_too_high'
        )


def validate_category_name(name):
    """Validate category name"""
    if not name or not name.strip():
        raise ValidationError(
            _('Category name cannot be empty.'),
            code='empty_name'
        )

    if len(name) > 100:
        raise ValidationError(
            _('Category name cannot exceed 100 characters.'),
            code='name_too_long'
        )

    # Prevent names with only special characters
    if not re.search(r'[a-zA-Z0-9가-힣]', name):
        raise ValidationError(
            _('Category name must contain at least one letter or number.'),
            code='name_no_alphanumeric'
        )
