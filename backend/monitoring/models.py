"""
Models for system monitoring and performance tracking
"""
import json

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

User = get_user_model()


class APIMetrics(models.Model):
    """
    Track API performance metrics
    """
    endpoint = models.CharField(max_length=200, help_text="API endpoint path")
    method = models.CharField(max_length=10, help_text="HTTP method")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Performance metrics
    response_time_ms = models.IntegerField(help_text="Response time in milliseconds")
    query_count = models.IntegerField(default=0, help_text="Number of database queries")
    cache_hits = models.IntegerField(default=0, help_text="Number of cache hits")
    cache_misses = models.IntegerField(default=0, help_text="Number of cache misses")
    
    # Response data
    status_code = models.IntegerField(help_text="HTTP status code")
    response_size_bytes = models.IntegerField(default=0, help_text="Response size in bytes")
    
    # Metadata
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    request_id = models.UUIDField(null=True, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True, db_index=True)
    hour = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(23)])
    
    class Meta:
        db_table = 'monitoring_api_metrics'
        indexes = [
            models.Index(fields=['endpoint', 'date']),
            models.Index(fields=['status_code', 'date']),
            models.Index(fields=['response_time_ms', 'date']),
            models.Index(fields=['user', 'date']),
        ]
        
    def save(self, *args, **kwargs):
        if not self.hour:
            self.hour = timezone.now().hour
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.response_time_ms}ms"


class DatabaseMetrics(models.Model):
    """
    Track database performance metrics
    """
    table_name = models.CharField(max_length=100, help_text="Database table name")
    operation_type = models.CharField(
        max_length=20,
        choices=[
            ('SELECT', 'Select'),
            ('INSERT', 'Insert'),
            ('UPDATE', 'Update'),
            ('DELETE', 'Delete'),
            ('COUNT', 'Count'),
        ]
    )
    
    # Performance metrics
    execution_time_ms = models.FloatField(help_text="Query execution time in milliseconds")
    rows_affected = models.IntegerField(default=0, help_text="Number of rows affected")
    
    # Query information
    query_hash = models.CharField(max_length=64, help_text="MD5 hash of normalized query")
    is_slow_query = models.BooleanField(default=False, help_text="Query took longer than threshold")
    
    # Context
    endpoint = models.CharField(max_length=200, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'monitoring_database_metrics'
        indexes = [
            models.Index(fields=['table_name', 'date']),
            models.Index(fields=['operation_type', 'date']),
            models.Index(fields=['is_slow_query', 'date']),
            models.Index(fields=['execution_time_ms', 'date']),
        ]
    
    def __str__(self):
        return f"{self.operation_type} {self.table_name} - {self.execution_time_ms}ms"


class AIMetrics(models.Model):
    """
    Track AI service usage and costs
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # AI Service information
    service_provider = models.CharField(
        max_length=50,
        choices=[
            ('anthropic', 'Anthropic Claude'),
            ('openai', 'OpenAI GPT'),
        ],
        default='anthropic'
    )
    model_name = models.CharField(max_length=100, help_text="AI model used")
    
    # Operation details
    operation_type = models.CharField(
        max_length=50,
        choices=[
            ('question_generation', 'Question Generation'),
            ('answer_evaluation', 'Answer Evaluation'),
            ('content_analysis', 'Content Analysis'),
            ('chat', 'AI Chat'),
        ]
    )
    
    # Usage metrics
    tokens_used = models.IntegerField(default=0, help_text="Number of tokens consumed")
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0, help_text="Cost in USD")
    processing_time_ms = models.IntegerField(help_text="Processing time in milliseconds")
    
    # Quality metrics
    success = models.BooleanField(default=True, help_text="Operation completed successfully")
    quality_score = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(10)])
    
    # Context
    content_id = models.IntegerField(null=True, blank=True, help_text="Related content ID")
    subscription_tier = models.CharField(max_length=20, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'monitoring_ai_metrics'
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['operation_type', 'date']),
            models.Index(fields=['service_provider', 'date']),
            models.Index(fields=['success', 'date']),
        ]
    
    def __str__(self):
        return f"{self.operation_type} - {self.model_name} ({self.tokens_used} tokens)"


class ErrorLog(models.Model):
    """
    Track application errors and exceptions
    """
    ERROR_LEVELS = [
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
        ('WARNING', 'Warning'),
    ]
    
    level = models.CharField(max_length=10, choices=ERROR_LEVELS)
    message = models.TextField(help_text="Error message")
    exception_type = models.CharField(max_length=200, help_text="Exception class name")
    traceback = models.TextField(blank=True, help_text="Full traceback")
    
    # Context
    endpoint = models.CharField(max_length=200, blank=True)
    method = models.CharField(max_length=10, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Request details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_data = models.JSONField(default=dict, blank=True, help_text="Sanitized request data")
    
    # Metadata
    resolved = models.BooleanField(default=False, help_text="Error has been resolved")
    occurrences = models.IntegerField(default=1, help_text="Number of times this error occurred")
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'monitoring_error_log'
        indexes = [
            models.Index(fields=['level', 'date']),
            models.Index(fields=['exception_type', 'date']),
            models.Index(fields=['endpoint', 'date']),
            models.Index(fields=['resolved', 'date']),
        ]
    
    def __str__(self):
        return f"{self.level}: {self.exception_type} - {self.message[:50]}"


class SystemHealth(models.Model):
    """
    Track overall system health metrics
    """
    # System metrics
    cpu_usage_percent = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    memory_usage_percent = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    disk_usage_percent = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Database metrics
    db_connection_count = models.IntegerField(help_text="Number of active DB connections")
    db_query_avg_time_ms = models.FloatField(help_text="Average query time in milliseconds")
    
    # Cache metrics
    cache_hit_rate_percent = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    cache_memory_usage_mb = models.FloatField(help_text="Cache memory usage in MB")
    
    # Service status
    celery_workers_active = models.IntegerField(default=0)
    redis_status = models.BooleanField(default=True)
    postgres_status = models.BooleanField(default=True)
    
    # API metrics
    api_requests_per_minute = models.FloatField(default=0)
    api_error_rate_percent = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    api_avg_response_time_ms = models.FloatField(default=0)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'monitoring_system_health'
        indexes = [
            models.Index(fields=['date', 'timestamp']),
        ]
    
    def __str__(self):
        return f"Health check - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class UserActivity(models.Model):
    """
    Track user activity patterns
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Activity metrics
    api_requests_count = models.IntegerField(default=0)
    content_created_count = models.IntegerField(default=0)
    reviews_completed_count = models.IntegerField(default=0)
    ai_questions_generated_count = models.IntegerField(default=0)
    
    # Session information
    session_duration_minutes = models.IntegerField(default=0)
    unique_endpoints_accessed = models.IntegerField(default=0)
    
    # Device/Location info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(
        max_length=20,
        choices=[
            ('desktop', 'Desktop'),
            ('mobile', 'Mobile'),
            ('tablet', 'Tablet'),
            ('unknown', 'Unknown'),
        ],
        default='unknown'
    )
    
    # Timestamps
    date = models.DateField(db_index=True)
    first_activity = models.DateTimeField()
    last_activity = models.DateTimeField()
    
    class Meta:
        db_table = 'monitoring_user_activity'
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['date', 'user']),
            models.Index(fields=['api_requests_count', 'date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} activity - {self.date}"