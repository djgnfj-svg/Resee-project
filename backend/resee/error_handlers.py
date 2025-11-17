"""
Centralized error handling utilities for the Resee application.
"""
from functools import wraps

from django.core.exceptions import ValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response


class APIErrorHandler:
    """Centralized error response handler."""
    
    @staticmethod
    def not_found(message="리소스를 찾을 수 없습니다."):
        return Response(
            {'error': message}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    @staticmethod
    def validation_error(errors):
        if isinstance(errors, dict):
            return Response(
                {'field_errors': errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {'error': str(errors)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def permission_denied(message="권한이 없습니다."):
        return Response(
            {'error': message}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    @staticmethod
    def unauthorized(message="인증이 필요합니다."):
        return Response(
            {'error': message}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    @staticmethod
    def server_error(message="서버 오류가 발생했습니다."):
        return Response(
            {'error': message}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @staticmethod
    def success(data=None, message="성공"):
        response_data = {'message': message}
        if data:
            response_data['data'] = data
        return Response(response_data, status=status.HTTP_200_OK)


def handle_api_exceptions(view_func):
    """
    Decorator to handle common API exceptions.
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        try:
            return view_func(*args, **kwargs)
        except Http404:
            return APIErrorHandler.not_found()
        except ValidationError as e:
            return APIErrorHandler.validation_error(e.message_dict if hasattr(e, 'message_dict') else str(e))
        except PermissionError:
            return APIErrorHandler.permission_denied()
        except Exception as e:
            # Log the exception in production
            return APIErrorHandler.server_error(f"예상치 못한 오류: {str(e)}")
    
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