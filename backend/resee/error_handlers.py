"""
Centralized error handling utilities for the Resee application.

Standardized Error Response Format:
{
    "error": {
        "code": "ERROR_CODE",
        "message": "User-friendly message",
        "details": {...}  # Optional, for field-specific errors
    }
}
"""
from functools import wraps
from typing import Any, Dict, Optional

from django.core.exceptions import ValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response


class ErrorCode:
    """Standard error codes for the API"""
    # Client errors (4xx)
    VALIDATION_ERROR = 'VALIDATION_ERROR'
    NOT_FOUND = 'NOT_FOUND'
    UNAUTHORIZED = 'UNAUTHORIZED'
    PERMISSION_DENIED = 'PERMISSION_DENIED'
    RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED'
    DUPLICATE_RESOURCE = 'DUPLICATE_RESOURCE'
    INVALID_TOKEN = 'INVALID_TOKEN'

    # Server errors (5xx)
    INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR'
    SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE'
    DATABASE_ERROR = 'DATABASE_ERROR'

    # Business logic errors
    SUBSCRIPTION_REQUIRED = 'SUBSCRIPTION_REQUIRED'
    SUBSCRIPTION_EXPIRED = 'SUBSCRIPTION_EXPIRED'
    AI_SERVICE_ERROR = 'AI_SERVICE_ERROR'
    EXAM_GENERATION_FAILED = 'EXAM_GENERATION_FAILED'


class APIErrorHandler:
    """Centralized error response handler with standardized format."""

    @staticmethod
    def _format_error(
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Format error response according to standard schema"""
        error_response = {
            'error': {
                'code': code,
                'message': message
            }
        }
        if details:
            error_response['error']['details'] = details
        return error_response

    @staticmethod
    def not_found(message: str = "Resource not found", details: Optional[Dict] = None):
        return Response(
            APIErrorHandler._format_error(ErrorCode.NOT_FOUND, message, details),
            status=status.HTTP_404_NOT_FOUND
        )

    @staticmethod
    def validation_error(message: str = "Validation failed", errors: Optional[Dict] = None):
        """
        Validation error with optional field-specific errors.

        Args:
            message: User-friendly error message
            errors: Dictionary of field-specific errors (e.g., {"email": ["Invalid format"]})
        """
        return Response(
            APIErrorHandler._format_error(
                ErrorCode.VALIDATION_ERROR,
                message,
                errors
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    @staticmethod
    def permission_denied(message: str = "Permission denied", details: Optional[Dict] = None):
        return Response(
            APIErrorHandler._format_error(ErrorCode.PERMISSION_DENIED, message, details),
            status=status.HTTP_403_FORBIDDEN
        )

    @staticmethod
    def unauthorized(message: str = "Authentication required", details: Optional[Dict] = None):
        return Response(
            APIErrorHandler._format_error(ErrorCode.UNAUTHORIZED, message, details),
            status=status.HTTP_401_UNAUTHORIZED
        )

    @staticmethod
    def server_error(message: str = "Internal server error", details: Optional[Dict] = None):
        return Response(
            APIErrorHandler._format_error(ErrorCode.INTERNAL_SERVER_ERROR, message, details),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    @staticmethod
    def custom_error(
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict] = None
    ):
        """Create a custom error response"""
        return Response(
            APIErrorHandler._format_error(code, message, details),
            status=status_code
        )

    @staticmethod
    def rate_limit_exceeded(message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        details = {'retry_after': retry_after} if retry_after else None
        return Response(
            APIErrorHandler._format_error(ErrorCode.RATE_LIMIT_EXCEEDED, message, details),
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    @staticmethod
    def subscription_required(message: str = "Subscription required for this feature"):
        return Response(
            APIErrorHandler._format_error(ErrorCode.SUBSCRIPTION_REQUIRED, message),
            status=status.HTTP_403_FORBIDDEN
        )

    # Legacy method for backward compatibility
    @staticmethod
    def success(data=None, message="Success"):
        """Deprecated: Use StandardAPIResponse.success() instead"""
        response_data = {'message': message}
        if data:
            response_data['data'] = data
        return Response(response_data, status=status.HTTP_200_OK)


def handle_api_exceptions(view_func):
    """
    Decorator to handle common API exceptions with standardized error responses.
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        try:
            return view_func(*args, **kwargs)
        except Http404:
            return APIErrorHandler.not_found()
        except ValidationError as e:
            errors = e.message_dict if hasattr(e, 'message_dict') else {'error': str(e)}
            return APIErrorHandler.validation_error(
                message="Validation failed",
                errors=errors
            )
        except PermissionError:
            return APIErrorHandler.permission_denied()
        except Exception as e:
            # Log the exception (will be enhanced with structured logging)
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Unexpected error occurred")

            return APIErrorHandler.server_error(
                message="An unexpected error occurred",
                details={'error_type': type(e).__name__} if not getattr(args[0].request, 'user', None) else None
            )

    return wrapper


class StandardAPIResponse:
    """Standard response format for API endpoints."""

    @staticmethod
    def success(data=None, message="성공"):
        response = {'success': True, 'message': message}
        if data is not None:
            response['data'] = data
        return Response(response, status=status.HTTP_200_OK)

    @staticmethod
    def created(data=None, message="생성되었습니다."):
        response = {'success': True, 'message': message}
        if data is not None:
            response['data'] = data
        return Response(response, status=status.HTTP_201_CREATED)

    @staticmethod
    def error(message, status_code=status.HTTP_400_BAD_REQUEST, errors=None):
        response = {'success': False, 'message': message}
        if errors:
            response['errors'] = errors
        return Response(response, status=status_code)
