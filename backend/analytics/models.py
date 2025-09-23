"""
Business Intelligence models for advanced analytics
"""
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

from resee.models import BaseUserModel, BaseModel

User = get_user_model()


class LearningPattern(BaseModel):
    """
    Track user learning patterns and behaviors
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_patterns')
    date = models.DateField(db_index=True)
    
    # Daily activity metrics
    contents_created = models.IntegerField(default=0, help_text="Contents created today")
    reviews_completed = models.IntegerField(default=0, help_text="Reviews completed today")
    ai_questions_generated = models.IntegerField(default=0, help_text="AI questions generated today")
    session_duration_minutes = models.IntegerField(default=0, help_text="Total session time in minutes")
    
    # Learning efficiency
    success_rate = models.FloatField(
        default=0.0, 
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Daily success rate percentage"
    )
    average_review_time_seconds = models.IntegerField(
        default=0,
        help_text="Average time spent per review in seconds"
    )
    
    # Engagement patterns
    peak_activity_hour = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        help_text="Hour of day with most activity (0-23)"
    )
    login_count = models.IntegerField(default=0, help_text="Number of logins today")
    
    # Streak tracking
    consecutive_days = models.IntegerField(default=0, help_text="Current learning streak")
    
    class Meta:
        db_table = 'bi_learning_pattern'
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date', 'success_rate']),
            models.Index(fields=['consecutive_days']),
        ]
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.email} - {self.date}"




class SubscriptionAnalytics(BaseModel):
    """
    Track subscription behavior and conversion metrics
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscription_analytics')
    
    # Subscription history
    subscription_tier = models.CharField(
        max_length=20,
        choices=[
            ('FREE', 'Free'),
            ('BASIC', 'Basic'),
            ('PRO', 'Pro'),
        ],
        default='FREE'
    )
    tier_start_date = models.DateTimeField()
    tier_end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Usage during subscription period
    total_content_created = models.IntegerField(default=0)
    total_reviews_completed = models.IntegerField(default=0)
    total_ai_questions_used = models.IntegerField(default=0)
    total_session_time_hours = models.FloatField(default=0.0)
    
    # Engagement metrics
    days_active = models.IntegerField(default=0, help_text="Number of days user was active")
    average_daily_reviews = models.FloatField(default=0.0)
    feature_adoption_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentage of features used (0-100)"
    )
    
    # Conversion metrics
    upgrade_probability = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="ML-calculated upgrade probability (0-100)"
    )
    churn_risk_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Risk of subscription cancellation (0-100)"
    )

    class Meta:
        db_table = 'bi_subscription_analytics'
        indexes = [
            models.Index(fields=['user', 'tier_start_date']),
            models.Index(fields=['subscription_tier', 'is_active']),
            models.Index(fields=['upgrade_probability']),
            models.Index(fields=['churn_risk_score']),
        ]
        ordering = ['-tier_start_date']
    
    def __str__(self):
        return f"{self.user.email} - {self.subscription_tier} ({self.tier_start_date.date()})"


class SystemUsageMetrics(BaseModel):
    """
    Track system-wide usage metrics for business insights
    """
    date = models.DateField(unique=True, db_index=True)
    
    # User metrics
    total_users = models.IntegerField(default=0)
    active_users_daily = models.IntegerField(default=0)
    new_users = models.IntegerField(default=0)
    churned_users = models.IntegerField(default=0)
    
    # Subscription metrics
    free_users = models.IntegerField(default=0)
    basic_users = models.IntegerField(default=0)
    pro_users = models.IntegerField(default=0)
    subscription_revenue_usd = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00
    )
    
    # Content metrics
    total_content_created = models.IntegerField(default=0)
    total_reviews_completed = models.IntegerField(default=0)
    average_success_rate = models.FloatField(default=0.0)
    
    # AI usage metrics
    ai_questions_generated = models.IntegerField(default=0)
    ai_cost_usd = models.DecimalField(
        max_digits=8, 
        decimal_places=4, 
        default=0.0000
    )
    ai_tokens_used = models.BigIntegerField(default=0)
    
    # System performance
    average_api_response_time_ms = models.IntegerField(default=0)
    error_rate_percentage = models.FloatField(default=0.0)
    uptime_percentage = models.FloatField(default=100.0)

    class Meta:
        db_table = 'bi_system_usage_metrics'
        ordering = ['-date']
    
    def __str__(self):
        return f"System Metrics - {self.date}"