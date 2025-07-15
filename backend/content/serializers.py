from rest_framework import serializers
from .models import Category, Tag, Content


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer"""
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'created_at')
        read_only_fields = ('id', 'slug', 'created_at')


class TagSerializer(serializers.ModelSerializer):
    """Tag serializer"""
    
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'created_at')
        read_only_fields = ('id', 'slug', 'created_at')


class ContentSerializer(serializers.ModelSerializer):
    """Content serializer"""
    author = serializers.StringRelatedField(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Content
        fields = ('id', 'title', 'content', 'author', 'category', 'tags', 'tag_ids',
                 'priority', 'created_at', 'updated_at')
        read_only_fields = ('id', 'author', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        content = Content.objects.create(**validated_data)
        content.tags.set(tag_ids)
        return content
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        
        return instance