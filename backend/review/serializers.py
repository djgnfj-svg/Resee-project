from rest_framework import serializers
from .models import ReviewSchedule, ReviewHistory
from content.serializers import ContentSerializer


class ReviewScheduleSerializer(serializers.ModelSerializer):
    """Review schedule serializer"""
    content = ContentSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = ReviewSchedule
        fields = ('id', 'content', 'user', 'next_review_date', 'interval_index', 
                 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')


class ReviewHistorySerializer(serializers.ModelSerializer):
    """Review history serializer"""
    content = ContentSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = ReviewHistory
        fields = ('id', 'content', 'user', 'review_date', 'result', 
                 'time_spent', 'notes')
        read_only_fields = ('id', 'user', 'review_date')