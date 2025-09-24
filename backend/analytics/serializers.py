"""
Simple analytics serializers for basic statistics
"""
from rest_framework import serializers
from .models import DailyStats


class DailyStatsSerializer(serializers.ModelSerializer):
    """Serializer for daily learning statistics"""

    class Meta:
        model = DailyStats
        fields = [
            'id', 'date', 'contents_created', 'reviews_completed',
            'success_rate'
        ]
        read_only_fields = ['id']


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard overview statistics"""
    today_reviews = serializers.IntegerField()
    pending_reviews = serializers.IntegerField()
    total_content = serializers.IntegerField()
    success_rate = serializers.FloatField()
    total_reviews_30_days = serializers.IntegerField()
