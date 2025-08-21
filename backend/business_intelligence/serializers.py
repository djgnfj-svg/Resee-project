"""
Business Intelligence API serializers
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
    success_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = ContentEffectiveness
        fields = [
            'id', 'content_title', 'content_type', 'category_name',
            'total_reviews', 'successful_reviews', 'success_rate',
            'average_difficulty_rating', 'average_review_time_seconds',
            'time_to_master_days', 'ai_questions_generated',
            'ai_questions_success_rate', 'abandonment_risk_score',
            'last_reviewed'
        ]


class SubscriptionAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for subscription analytics"""
    
    class Meta:
        model = SubscriptionAnalytics
        fields = [
            'id', 'subscription_tier', 'tier_start_date', 'tier_end_date',
            'is_active', 'total_content_created', 'total_reviews_completed',
            'total_ai_questions_used', 'total_session_time_hours',
            'days_active', 'average_daily_reviews', 'feature_adoption_score',
            'upgrade_probability', 'churn_risk_score'
        ]


class LearningInsightsSerializer(serializers.Serializer):
    """Serializer for learning insights summary"""
    total_learning_days = serializers.IntegerField()
    current_streak = serializers.IntegerField()
    longest_streak = serializers.IntegerField()
    average_daily_reviews = serializers.FloatField()
    average_success_rate = serializers.FloatField()
    most_productive_hour = serializers.IntegerField()
    total_study_hours = serializers.FloatField()
    learning_consistency_score = serializers.FloatField()


class ContentAnalyticsSerializer(serializers.Serializer):
    """Serializer for content analytics summary"""
    total_content = serializers.IntegerField()
    mastered_content = serializers.IntegerField()
    struggling_content = serializers.IntegerField()
    abandoned_content = serializers.IntegerField()
    average_mastery_time_days = serializers.FloatField()
    most_effective_content_type = serializers.CharField()
    least_effective_content_type = serializers.CharField()
    category_performance = serializers.DictField()


class SubscriptionInsightsSerializer(serializers.Serializer):
    """Serializer for subscription insights"""
    current_tier = serializers.CharField()
    tier_duration_days = serializers.IntegerField()
    feature_utilization_rate = serializers.FloatField()
    upgrade_recommendation = serializers.CharField()
    usage_efficiency_score = serializers.FloatField()
    cost_per_review = serializers.FloatField()
    projected_monthly_value = serializers.FloatField()


class SystemMetricsSerializer(serializers.ModelSerializer):
    """Serializer for system usage metrics"""
    
    class Meta:
        model = SystemUsageMetrics
        fields = [
            'date', 'total_users', 'active_users_daily', 'new_users',
            'free_users', 'basic_users', 'pro_users', 'subscription_revenue_usd',
            'total_content_created', 'total_reviews_completed', 'average_success_rate',
            'ai_questions_generated', 'ai_cost_usd', 'ai_tokens_used',
            'average_api_response_time_ms', 'error_rate_percentage', 'uptime_percentage'
        ]


class BusinessDashboardSerializer(serializers.Serializer):
    """Comprehensive business dashboard data"""
    
    # Overview metrics
    total_users = serializers.IntegerField()
    active_users_today = serializers.IntegerField()
    new_users_this_month = serializers.IntegerField()
    monthly_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # User engagement
    average_session_duration = serializers.FloatField()
    daily_active_users_trend = serializers.ListField(child=serializers.IntegerField())
    user_retention_rate = serializers.FloatField()
    
    # Content metrics
    total_content_created = serializers.IntegerField()
    average_reviews_per_user = serializers.FloatField()
    content_completion_rate = serializers.FloatField()
    
    # Subscription metrics
    conversion_rate = serializers.FloatField()
    churn_rate = serializers.FloatField()
    average_revenue_per_user = serializers.FloatField()
    tier_distribution = serializers.DictField()
    
    # AI usage
    ai_adoption_rate = serializers.FloatField()
    ai_cost_efficiency = serializers.FloatField()
    ai_questions_per_user = serializers.FloatField()
    
    # Performance indicators
    system_uptime = serializers.FloatField()
    average_response_time = serializers.IntegerField()
    error_rate = serializers.FloatField()


class LearningRecommendationSerializer(serializers.Serializer):
    """Serializer for AI-powered learning recommendations"""
    recommendation_type = serializers.ChoiceField(choices=[
        ('schedule', 'Schedule Optimization'),
        ('content', 'Content Recommendation'),
        ('difficulty', 'Difficulty Adjustment'),
        ('engagement', 'Engagement Improvement'),
    ])
    title = serializers.CharField()
    description = serializers.CharField()
    confidence_score = serializers.FloatField()
    expected_improvement = serializers.CharField()
    action_items = serializers.ListField(child=serializers.CharField())
    priority = serializers.ChoiceField(choices=[
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ])


class PerformanceTrendSerializer(serializers.Serializer):
    """Serializer for performance trend data"""
    date = serializers.DateField()
    success_rate = serializers.FloatField()
    reviews_completed = serializers.IntegerField()
    study_time_minutes = serializers.IntegerField()
    difficulty_trend = serializers.FloatField()
    engagement_score = serializers.FloatField()