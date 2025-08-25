"""
Analytics API serializers - includes both basic analytics and business intelligence
"""
from rest_framework import serializers
from django.db.models import Avg, Count, Sum, F
from django.utils import timezone
from datetime import timedelta

from .models import LearningPattern, ContentEffectiveness, SubscriptionAnalytics, SystemUsageMetrics


class LearningPatternSerializer(serializers.ModelSerializer):
    """Serializer for learning pattern data"""
    
    class Meta:
        model = LearningPattern
        fields = [
            'id', 'date', 'contents_created', 'reviews_completed', 
            'ai_questions_generated', 'session_duration_minutes',
            'success_rate', 'average_review_time_seconds', 
            'peak_activity_hour', 'login_count', 'consecutive_days'
        ]
        read_only_fields = ['id']


class ContentEffectivenessSerializer(serializers.ModelSerializer):
    """Serializer for content effectiveness data"""
    content_title = serializers.CharField(source='content.title', read_only=True)
    content_type = serializers.CharField(source='content.content_type', read_only=True)
    category_name = serializers.CharField(source='content.category.name', read_only=True)
    success_rate = serializers.FloatField(read_only=True)
    
    class Meta:
        model = ContentEffectiveness
        fields = [
            'id', 'content_title', 'content_type', 'category_name',
            'total_reviews', 'successful_reviews', 'success_rate',
            'average_difficulty_rating', 'average_review_time_seconds',
            'time_to_master_days', 'ai_questions_generated',
            'ai_questions_success_rate', 'last_reviewed', 
            'abandonment_risk_score'
        ]
        read_only_fields = ['id', 'success_rate']


class SubscriptionAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for subscription analytics"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = SubscriptionAnalytics
        fields = [
            'id', 'user_email', 'subscription_tier', 'tier_start_date', 
            'tier_end_date', 'is_active', 'total_content_created',
            'total_reviews_completed', 'total_ai_questions_used',
            'total_session_time_hours', 'days_active', 
            'average_daily_reviews', 'feature_adoption_score',
            'upgrade_probability', 'churn_risk_score'
        ]
        read_only_fields = ['id']


class SystemUsageMetricsSerializer(serializers.ModelSerializer):
    """Serializer for system-wide usage metrics"""
    
    class Meta:
        model = SystemUsageMetrics
        fields = [
            'id', 'date', 'total_users', 'active_users_daily',
            'new_users', 'churned_users', 'free_users',
            'basic_users', 'pro_users', 'subscription_revenue_usd',
            'total_content_created', 'total_reviews_completed',
            'average_success_rate', 'ai_questions_generated',
            'ai_cost_usd', 'ai_tokens_used', 
            'average_api_response_time_ms', 'error_rate_percentage',
            'uptime_percentage'
        ]
        read_only_fields = ['id']


class LearningInsightSerializer(serializers.Serializer):
    """Serializer for learning insights summary"""
    total_days_active = serializers.IntegerField()
    current_streak = serializers.IntegerField()
    average_success_rate = serializers.FloatField()
    total_reviews = serializers.IntegerField()
    most_productive_hour = serializers.IntegerField()
    improvement_areas = serializers.ListField(
        child=serializers.CharField(), 
        read_only=True
    )


class PerformanceTrendSerializer(serializers.Serializer):
    """Serializer for performance trend data"""
    date = serializers.DateField()
    success_rate = serializers.FloatField()
    reviews_completed = serializers.IntegerField()
    session_duration_minutes = serializers.IntegerField()


class BusinessMetricsSerializer(serializers.Serializer):
    """Serializer for business dashboard metrics"""
    total_users = serializers.IntegerField()
    active_users_today = serializers.IntegerField()
    monthly_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    conversion_rate = serializers.FloatField()
    churn_rate = serializers.FloatField()
    ai_cost_per_user = serializers.DecimalField(max_digits=8, decimal_places=4)