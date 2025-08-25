"""
Alert system models for monitoring and notification
"""
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

User = get_user_model()


class AlertRule(models.Model):
    """
    Alert rule configuration for automated monitoring
    """
    
    ALERT_TYPES = [
        ('system_error', 'System Error'),
        ('performance', 'Performance Issue'),
        ('security', 'Security Alert'), 
        ('business', 'Business Metric Alert'),
        ('database', 'Database Issue'),
        ('ai_usage', 'AI Usage Alert'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'), 
        ('critical', 'Critical'),
    ]
    
    CONDITION_OPERATORS = [
        ('gt', 'Greater Than (>)'),
        ('gte', 'Greater Than or Equal (>=)'),
        ('lt', 'Less Than (<)'),
        ('lte', 'Less Than or Equal (<=)'),
        ('eq', 'Equal To (==)'),
        ('ne', 'Not Equal To (!=)'),
    ]
    
    METRIC_CHOICES = [
        # System metrics
        ('cpu_usage', 'CPU Usage (%)'),
        ('memory_usage', 'Memory Usage (%)'),
        ('disk_usage', 'Disk Usage (%)'),
        
        # API metrics  
        ('api_response_time', 'API Response Time (ms)'),
        ('api_error_rate', 'API Error Rate (%)'),
        ('api_request_count', 'API Request Count'),
        
        # Database metrics
        ('db_connection_count', 'Database Connections'),
        ('db_query_time', 'Database Query Time (ms)'),
        ('slow_query_count', 'Slow Query Count'),
        
        # Error metrics
        ('error_count', 'Error Count'),
        ('critical_error_count', 'Critical Error Count'),
        
        # AI metrics
        ('ai_cost_daily', 'Daily AI Cost (USD)'),
        ('ai_token_usage', 'AI Token Usage'),
        ('ai_failure_rate', 'AI Failure Rate (%)'),
        
        # Business metrics
        ('active_user_count', 'Active User Count'),
        ('signup_count', 'Daily Signup Count'),
        ('subscription_count', 'Daily Subscription Count'),
    ]
    
    # Basic information
    name = models.CharField(max_length=100, help_text="Alert rule name")
    description = models.TextField(blank=True, help_text="Description of the alert rule")
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    
    # Condition configuration
    metric_name = models.CharField(max_length=50, choices=METRIC_CHOICES)
    condition = models.CharField(max_length=10, choices=CONDITION_OPERATORS)
    threshold_value = models.FloatField(help_text="Threshold value to trigger alert")
    time_window_minutes = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(1440)],
        help_text="Time window in minutes to evaluate the condition"
    )
    
    # Notification settings
    slack_enabled = models.BooleanField(default=True)
    slack_channel = models.CharField(max_length=50, default='#alerts', blank=True)
    email_enabled = models.BooleanField(default=True) 
    email_recipients = models.JSONField(
        default=list,
        blank=True,
        help_text="List of email addresses to notify"
    )
    
    # Spam prevention
    cooldown_minutes = models.IntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(1440)],
        help_text="Minimum time between alerts for the same rule"
    )
    max_alerts_per_hour = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Maximum alerts per hour for this rule"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who created this rule"
    )
    
    class Meta:
        db_table = 'alerts_alert_rule'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'metric_name']),
            models.Index(fields=['alert_type', 'severity']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_severity_display()})"
    
    def get_condition_display_verbose(self):
        """Get human-readable condition description"""
        return f"{self.get_metric_name_display()} {self.get_condition_display()} {self.threshold_value}"
    
    def is_in_cooldown(self):
        """Check if this rule is still in cooldown period"""
        if not hasattr(self, '_last_alert_time'):
            # Get the most recent alert for this rule
            last_alert = self.alerthistory_set.order_by('-triggered_at').first()
            if not last_alert:
                return False
            self._last_alert_time = last_alert.triggered_at
        
        cooldown_end = self._last_alert_time + timezone.timedelta(minutes=self.cooldown_minutes)
        return timezone.now() < cooldown_end
    
    def get_recent_alert_count(self):
        """Get number of alerts in the last hour"""
        one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
        return self.alerthistory_set.filter(triggered_at__gte=one_hour_ago).count()


class AlertHistory(models.Model):
    """
    History of triggered alerts
    """
    
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE)
    triggered_at = models.DateTimeField(auto_now_add=True)
    
    # Trigger information
    metric_value = models.FloatField(help_text="Metric value that triggered the alert")
    message = models.TextField(help_text="Alert message sent to users")
    context_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context data for debugging"
    )
    
    # Notification status
    slack_sent = models.BooleanField(default=False)
    slack_response = models.JSONField(
        null=True,
        blank=True,
        help_text="Response from Slack API"
    )
    email_sent = models.BooleanField(default=False)
    email_response = models.JSONField(
        null=True, 
        blank=True,
        help_text="Response from email service"
    )
    
    # Resolution tracking
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts'
    )
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'alerts_alert_history'
        ordering = ['-triggered_at']
        indexes = [
            models.Index(fields=['rule', 'triggered_at']),
            models.Index(fields=['triggered_at', 'resolved_at']),
            models.Index(fields=['slack_sent', 'email_sent']),
        ]
    
    def __str__(self):
        return f"{self.rule.name} - {self.triggered_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def is_resolved(self):
        """Check if this alert has been resolved"""
        return self.resolved_at is not None
    
    @property
    def notification_success(self):
        """Check if at least one notification method succeeded"""
        if self.rule.slack_enabled and self.rule.email_enabled:
            return self.slack_sent or self.email_sent
        elif self.rule.slack_enabled:
            return self.slack_sent
        elif self.rule.email_enabled:
            return self.email_sent
        return True  # No notifications configured
    
    def resolve(self, user=None, notes=""):
        """Mark this alert as resolved"""
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.resolution_notes = notes
        self.save(update_fields=['resolved_at', 'resolved_by', 'resolution_notes'])