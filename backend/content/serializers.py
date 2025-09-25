from rest_framework import serializers

from .models import Category, Content


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer"""
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'created_at', 'user')
        read_only_fields = ('id', 'slug', 'created_at', 'user')


class ContentSerializer(serializers.ModelSerializer):
    """Content serializer"""
    author = serializers.StringRelatedField(read_only=True)
    category = CategorySerializer(read_only=True)
    review_count = serializers.SerializerMethodField()
    next_review_date = serializers.SerializerMethodField()
    
    class Meta:
        model = Content
        fields = ('id', 'title', 'content', 'author', 'category',
                 'created_at', 'updated_at', 'review_count',
                 'next_review_date')
        read_only_fields = ('id', 'author', 'created_at', 'updated_at')
    
    def get_review_count(self, obj):
        """Get the number of completed reviews for this content"""
        return obj.review_history.count()
    
    def get_next_review_date(self, obj):
        """Get next review date"""
        try:
            schedule = obj.review_schedules.filter(user=self.context['request'].user).first()
            return schedule.next_review_date if schedule else None
        except:
            return None