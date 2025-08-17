"""
Common validation utilities and validators
"""
from django.core.exceptions import ValidationError
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