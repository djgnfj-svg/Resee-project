"""
Common mixins for Django REST Framework ViewSets
"""


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


class AuthorViewSetMixin(AuthorOwnershipMixin):
    """
    Base mixin for author-owned content

    Use this for ViewSets where the ownership field is 'author'.
    """
