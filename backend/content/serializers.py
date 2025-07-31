from rest_framework import serializers
from .models import Category, Content


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer"""
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'created_at')
        read_only_fields = ('id', 'slug', 'created_at')


class ContentSerializer(serializers.ModelSerializer):
    """Content serializer"""
    author = serializers.StringRelatedField(read_only=True)
    category = CategorySerializer(read_only=True)
    
    class Meta:
        model = Content
        fields = ('id', 'title', 'content', 'author', 'category',
                 'priority', 'created_at', 'updated_at')
        read_only_fields = ('id', 'author', 'created_at', 'updated_at')