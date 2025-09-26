"""
Common validation utilities and validators with enhanced data integrity
"""
import re
from decimal import Decimal, InvalidOperation
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


class BaseValidator:
    """
    Base validator class for reusable validation logic
    """
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def validate(self, value):
        """
        Override this method in subclasses
        """
        raise NotImplementedError("Subclasses must implement validate method")
    
    def __call__(self, value):
        return self.validate(value)


class JSONFieldValidator(BaseValidator):
    """
    Validator for JSON fields with specific structure requirements
    """
    
    def __init__(self, required_keys=None, optional_keys=None, **kwargs):
        super().__init__(**kwargs)
        self.required_keys = required_keys or []
        self.optional_keys = optional_keys or []
    
    def validate(self, value):
        if not isinstance(value, dict):
            raise ValidationError("Value must be a dictionary")
        
        # Check required keys
        missing_keys = set(self.required_keys) - set(value.keys())
        if missing_keys:
            raise ValidationError(
                f"Missing required keys: {', '.join(missing_keys)}"
            )
        
        # Check for unexpected keys if we have a whitelist
        if self.required_keys or self.optional_keys:
            allowed_keys = set(self.required_keys + self.optional_keys)
            unexpected_keys = set(value.keys()) - allowed_keys
            if unexpected_keys:
                raise ValidationError(
                    f"Unexpected keys: {', '.join(unexpected_keys)}"
                )
        
        return value


# Enhanced validators for data integrity
def validate_email_domain(email):
    """Validate email domain to prevent obvious fake/temp emails"""
    blocked_domains = [
        'tempmail.com',
        '10minutemail.com',
        'guerrillamail.com',
        'mailinator.com',
        'yopmail.com',
        'throwaway.email',
        'temp-mail.org',
    ]

    if '@' in email:
        domain = email.split('@')[1].lower()
        if domain in blocked_domains:
            raise ValidationError(
                _('Email from this domain is not allowed.'),
                code='blocked_domain'
            )


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


def validate_username(username):
    """Validate username format if provided"""
    if not username:
        return  # Username is optional

    if len(username) < 3:
        raise ValidationError(
            _('Username must be at least 3 characters long.'),
            code='username_too_short'
        )

    if len(username) > 30:
        raise ValidationError(
            _('Username cannot exceed 30 characters.'),
            code='username_too_long'
        )

    # Allow alphanumeric, underscore, hyphen, and dot
    if not re.match(r'^[a-zA-Z0-9._-]+$', username):
        raise ValidationError(
            _('Username can only contain letters, numbers, periods, hyphens, and underscores.'),
            code='invalid_username_chars'
        )

    # Prevent usernames that look like email addresses
    if '@' in username:
        raise ValidationError(
            _('Username cannot contain @ symbol.'),
            code='username_like_email'
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


class DataIntegrityValidator:
    """Centralized validator for complex data integrity checks"""

    @staticmethod
    def validate_user_subscription_consistency(user):
        """Validate user's subscription data consistency"""
        errors = []

        if not hasattr(user, 'subscription'):
            errors.append(ValidationError(
                _('User must have a subscription.'),
                code='missing_subscription'
            ))
            return errors

        subscription = user.subscription

        # Check subscription dates
        if subscription.end_date and subscription.start_date >= subscription.end_date:
            errors.append(ValidationError(
                _('Subscription end date must be after start date.'),
                code='invalid_subscription_dates'
            ))

        # Check tier consistency
        if subscription.tier == 'free' and subscription.amount_paid and subscription.amount_paid > 0:
            errors.append(ValidationError(
                _('Free tier should not have amount paid.'),
                code='free_tier_with_payment'
            ))

        # Check billing schedule consistency
        if subscription.auto_renewal and not subscription.next_billing_date:
            errors.append(ValidationError(
                _('Auto-renewal enabled but no next billing date set.'),
                code='auto_renewal_no_billing_date'
            ))

        return errors

    @staticmethod
    def validate_review_schedule_consistency(schedule):
        """Validate review schedule data consistency"""
        errors = []

        # Check user subscription limits
        try:
            validate_review_interval_index(schedule.interval_index, schedule.user)
        except ValidationError as e:
            errors.append(e)

        # Check date consistency
        if schedule.next_review_date and schedule.created_at and schedule.next_review_date < schedule.created_at:
            errors.append(ValidationError(
                _('Next review date cannot be before creation date.'),
                code='review_date_before_creation'
            ))

        # Check content relationship
        if schedule.content.author != schedule.user:
            errors.append(ValidationError(
                _('Review schedule user must match content author.'),
                code='schedule_user_content_mismatch'
            ))

        return errors

    @staticmethod
    def validate_payment_consistency(payment_history):
        """Validate payment history consistency"""
        errors = []

        # Check tier transition validity
        if payment_history.from_tier and payment_history.to_tier:
            tier_hierarchy = {'free': 0, 'basic': 1, 'pro': 2}
            from_level = tier_hierarchy.get(payment_history.from_tier, 0)
            to_level = tier_hierarchy.get(payment_history.to_tier, 0)

            if payment_history.payment_type == 'upgrade' and to_level <= from_level:
                errors.append(ValidationError(
                    _('Upgrade payment must increase tier level.'),
                    code='invalid_upgrade'
                ))

            if payment_history.payment_type == 'downgrade' and to_level >= from_level:
                errors.append(ValidationError(
                    _('Downgrade payment must decrease tier level.'),
                    code='invalid_downgrade'
                ))

        return errors


# Database constraint validators
def validate_foreign_key_exists(model_class, field_name, value):
    """Validate that foreign key reference exists"""
    if value is None:
        return  # Allow null if field allows it

    try:
        model_class.objects.get(pk=value)
    except model_class.DoesNotExist:
        raise ValidationError(
            _('Referenced %(model)s with id %(id)s does not exist.'),
            params={'model': model_class.__name__, 'id': value},
            code='foreign_key_not_found'
        )


def validate_unique_together(model_class, instance, fields):
    """Validate unique_together constraints"""
    filter_kwargs = {}
    for field in fields:
        filter_kwargs[field] = getattr(instance, field)

    queryset = model_class.objects.filter(**filter_kwargs)
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    if queryset.exists():
        field_names = ', '.join(fields)
        raise ValidationError(
            _('Fields (%(fields)s) must be unique together.'),
            params={'fields': field_names},
            code='unique_together'
        )