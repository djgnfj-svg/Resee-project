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
    review_count = serializers.SerializerMethodField()
    current_interval = serializers.SerializerMethodField()
    next_review_date = serializers.SerializerMethodField()
    
    class Meta:
        model = Content
        fields = ('id', 'title', 'content', 'author', 'category',
                 'priority', 'created_at', 'updated_at', 'review_count', 
                 'current_interval', 'next_review_date')
        read_only_fields = ('id', 'author', 'created_at', 'updated_at')
    
    def get_review_count(self, obj):
        """Get the number of completed reviews for this content"""
        return obj.review_history.count()
    
    def get_current_interval(self, obj):
        """Get current review interval in days"""
        try:
            schedule = obj.review_schedules.filter(user=self.context['request'].user).first()
            if schedule:
                from review.utils import get_review_intervals
                intervals = get_review_intervals(self.context['request'].user)
                if schedule.interval_index < len(intervals):
                    return intervals[schedule.interval_index]
            return None
        except:
            return None
    
    def get_next_review_date(self, obj):
        """Get next review date"""
        try:
            schedule = obj.review_schedules.filter(user=self.context['request'].user).first()
            return schedule.next_review_date if schedule else None
        except:
            return None