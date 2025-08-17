"""
Common mixins for Django REST Framework ViewSets
"""
from django.db import models
from rest_framework import viewsets


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