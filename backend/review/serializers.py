from rest_framework import serializers

from content.serializers import ContentSerializer, ReviewContentSerializer

from .models import ReviewHistory, ReviewSchedule


class ReviewScheduleSerializer(serializers.ModelSerializer):
    """Review schedule serializer - uses lightweight ReviewContentSerializer"""
    content = ReviewContentSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ReviewSchedule
        fields = ('id', 'content', 'user', 'next_review_date', 'interval_index',
                  'is_active', 'initial_review_completed', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')


class ReviewHistorySerializer(serializers.ModelSerializer):
    """Review history serializer"""
    content = ContentSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ReviewHistory
        fields = ('id', 'content', 'user', 'review_date', 'result',
                  'time_spent', 'notes', 'descriptive_answer', 'ai_score', 'ai_feedback')
        read_only_fields = ('id', 'user', 'review_date', 'ai_score', 'ai_feedback')
