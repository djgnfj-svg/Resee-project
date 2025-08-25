"""
Serializers for monitoring and alert system
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .alert_models import AlertRule, AlertHistory

User = get_user_model()


class AlertRuleSerializer(serializers.ModelSerializer):
    """
    Serializer for AlertRule model
    """
    condition_display = serializers.CharField(source='get_condition_display_verbose', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    metric_name_display = serializers.CharField(source='get_metric_name_display', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    is_in_cooldown = serializers.BooleanField(read_only=True)
    recent_alert_count = serializers.IntegerField(source='get_recent_alert_count', read_only=True)
    
    class Meta:
        model = AlertRule
        fields = [
            'id', 'name', 'description', 'alert_type', 'alert_type_display',
            'severity', 'severity_display', 'metric_name', 'metric_name_display',
            'condition', 'threshold_value', 'condition_display', 'time_window_minutes',
            'slack_enabled', 'slack_channel', 'email_enabled', 'email_recipients',
            'cooldown_minutes', 'max_alerts_per_hour', 'is_active',
            'created_at', 'updated_at', 'created_by', 'created_by_username',
            'is_in_cooldown', 'recent_alert_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def validate_email_recipients(self, value):
        """Validate email recipients format"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Email recipients must be a list")
        
        for email in value:
            if not isinstance(email, str) or '@' not in email:
                raise serializers.ValidationError(f"Invalid email format: {email}")
        
        return value


class AlertRuleCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new AlertRule
    """
    class Meta:
        model = AlertRule
        fields = [
            'name', 'description', 'alert_type', 'severity', 'metric_name',
            'condition', 'threshold_value', 'time_window_minutes',
            'slack_enabled', 'slack_channel', 'email_enabled', 'email_recipients',
            'cooldown_minutes', 'max_alerts_per_hour', 'is_active'
        ]
    
    def validate_threshold_value(self, value):
        """Validate threshold value based on metric type"""
        if value < 0:
            raise serializers.ValidationError("Threshold value cannot be negative")
        return value


class AlertHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for AlertHistory model
    """
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    rule_severity = serializers.CharField(source='rule.severity', read_only=True)
    rule_severity_display = serializers.CharField(source='rule.get_severity_display', read_only=True)
    resolved_by_username = serializers.CharField(source='resolved_by.username', read_only=True)
    is_resolved = serializers.BooleanField(read_only=True)
    notification_success = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = AlertHistory
        fields = [
            'id', 'rule', 'rule_name', 'rule_severity', 'rule_severity_display',
            'triggered_at', 'metric_value', 'message', 'context_data',
            'slack_sent', 'slack_response', 'email_sent', 'email_response',
            'resolved_at', 'resolved_by', 'resolved_by_username', 'resolution_notes',
            'is_resolved', 'notification_success'
        ]
        read_only_fields = [
            'id', 'triggered_at', 'slack_sent', 'slack_response', 
            'email_sent', 'email_response'
        ]


class AlertHistoryResolveSerializer(serializers.Serializer):
    """
    Serializer for resolving alerts
    """
    resolution_notes = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    
    def validate_resolution_notes(self, value):
        """Validate resolution notes"""
        if len(value.strip()) == 0:
            return "Alert resolved by user"
        return value.strip()


class AlertStatisticsSerializer(serializers.Serializer):
    """
    Serializer for alert statistics
    """
    total_alerts = serializers.IntegerField()
    resolved_alerts = serializers.IntegerField()
    unresolved_alerts = serializers.IntegerField()
    alerts_by_severity = serializers.DictField()
    alerts_by_type = serializers.DictField()
    recent_alerts = AlertHistorySerializer(many=True, read_only=True)
    
    # Time-based statistics
    alerts_last_24h = serializers.IntegerField()
    alerts_last_week = serializers.IntegerField()
    alerts_last_month = serializers.IntegerField()
    
    # Performance metrics
    avg_resolution_time = serializers.FloatField()
    notification_success_rate = serializers.FloatField()


class TestNotificationSerializer(serializers.Serializer):
    """
    Serializer for testing notification channels
    """
    CHANNEL_CHOICES = [
        ('slack', 'Slack'),
        ('email', 'Email'),
        ('both', 'Both Slack and Email')
    ]
    
    channel = serializers.ChoiceField(choices=CHANNEL_CHOICES, default='both')
    test_message = serializers.CharField(
        max_length=500,
        default="This is a test notification from Resee Alert System",
        required=False
    )
    email_recipients = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        allow_empty=True
    )
    slack_channel = serializers.CharField(
        max_length=50,
        default='#alerts',
        required=False
    )


class ManualTriggerSerializer(serializers.Serializer):
    """
    Serializer for manually triggering alerts
    """
    rule_id = serializers.IntegerField()
    test_metric_value = serializers.FloatField()
    custom_message = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True
    )
    
    def validate_rule_id(self, value):
        """Validate that the rule exists and is active"""
        try:
            rule = AlertRule.objects.get(id=value)
            if not rule.is_active:
                raise serializers.ValidationError("Cannot trigger inactive alert rule")
            return value
        except AlertRule.DoesNotExist:
            raise serializers.ValidationError("Alert rule not found")
    
    def validate_test_metric_value(self, value):
        """Validate test metric value"""
        if value < 0:
            raise serializers.ValidationError("Test metric value cannot be negative")
        return value