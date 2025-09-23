"""
Common mixins for Django REST Framework ViewSets
"""
import logging
from functools import wraps

from django.db import models
from rest_framework import viewsets, status
from rest_framework.response import Response

from .error_handlers import APIErrorHandler

logger = logging.getLogger(__name__)


def handle_api_errors(log_message=None, custom_error_response=None):
    """
    Decorator to handle common API errors with consistent logging and response format.

    Args:
        log_message (str): Custom log message template (can use {error} placeholder)
        custom_error_response (str): Custom error message for the response

    Usage:
        @handle_api_errors("User registration failed: {error}")
        def post(self, request):
            # your API logic here
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Log the error
                default_log_msg = f"{func.__name__} failed: {{error}}"
                log_msg = log_message or default_log_msg
                logger.error(log_msg.format(error=str(e)))

                # Return standardized error response
                error_msg = custom_error_response or "요청 처리 중 오류가 발생했습니다."
                return APIErrorHandler.server_error(error_msg)
        return wrapper
    return decorator


def require_ai_features(error_message="AI 기능을 사용할 수 없습니다."):
    """
    Decorator to check if user can use AI features.

    Usage:
        @require_ai_features("AI 질문 생성을 사용할 수 없습니다.")
        def post(self, request):
            # AI feature logic here
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            if not request.user.can_use_ai_features():
                return APIErrorHandler.forbidden(error_message)
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator


class UserOwnershipMixin:
    """
    Mixin to handle user ownership for ViewSets
    
    Automatically sets the user field when creating objects
    and filters queryset to only show user's own objects.
    """
    user_field = 'user'  # Override if the foreign key field name is different
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user_filter = {self.user_field: self.request.user}
        return queryset.filter(**user_filter)
    
    def perform_create(self, serializer):
        save_kwargs = {self.user_field: self.request.user}
        serializer.save(**save_kwargs)


class AuthorOwnershipMixin:
    """
    Mixin to handle author ownership for ViewSets
    
    Specifically for models with 'author' field instead of 'user'.
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(author=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class OptimizedQueryMixin:
    """
    Mixin to handle common query optimizations
    
    Provides select_related and prefetch_related optimizations
    based on model relationships.
    """
    select_related_fields = []
    prefetch_related_fields = []
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if self.select_related_fields:
            queryset = queryset.select_related(*self.select_related_fields)
        
        if self.prefetch_related_fields:
            queryset = queryset.prefetch_related(*self.prefetch_related_fields)
        
        return queryset


class BaseViewSetMixin(UserOwnershipMixin, OptimizedQueryMixin):
    """
    Base mixin combining common patterns for user-owned content
    
    Combines user ownership and query optimization.
    Use this for most standard ViewSets.
    """
    pass


class AuthorViewSetMixin(AuthorOwnershipMixin, OptimizedQueryMixin):
    """
    Base mixin for author-owned content with query optimization
    
    Use this for ViewSets where the ownership field is 'author'.
    """
    pass