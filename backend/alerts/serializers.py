"""
Serializers for alert system API
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import AlertRule, AlertHistory

User = get_user_model()


class AlertRuleSerializer(serializers.ModelSerializer):
    """
    Serializer for AlertRule model
    """
    created_by = serializers.StringRelatedField(read_only=True)
    created_by_id = serializers.IntegerField(read_only=True)
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    condition_display_verbose = serializers.CharField(source='get_condition_display_verbose', read_only=True)
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    metric_name_display = serializers.CharField(source='get_metric_name_display', read_only=True)
    is_in_cooldown = serializers.BooleanField(read_only=True)
    recent_alert_count = serializers.IntegerField(source='get_recent_alert_count', read_only=True)
    
    class Meta:
        model = AlertRule
        fields = [
            'id', 'name', 'description', 'alert_type', 'alert_type_display',
            'severity', 'severity_display', 'metric_name', 'metric_name_display',
            'condition', 'condition_display', 'condition_display_verbose',
            'threshold_value', 'time_window_minutes',
            'slack_enabled', 'slack_channel', 'email_enabled', 'email_recipients',
            'cooldown_minutes', 'max_alerts_per_hour', 'is_active',
            'created_at', 'updated_at', 'created_by', 'created_by_id',
            'is_in_cooldown', 'recent_alert_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'created_by_id']
    
    def validate_email_recipients(self, value):
        """Validate email recipients format"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Email recipients must be a list")
        
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        for email in value:
            if not isinstance(email, str):
                raise serializers.ValidationError("All email addresses must be strings")
            try:
                validate_email(email)
            except ValidationError:
                raise serializers.ValidationError(f"Invalid email address: {email}")
        
        return value
    
    def validate_threshold_value(self, value):
        """Validate threshold value"""
        if value < 0:
            raise serializers.ValidationError("Threshold value cannot be negative")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        # Ensure at least one notification method is enabled
        slack_enabled = data.get('slack_enabled', False)
        email_enabled = data.get('email_enabled', False)
        email_recipients = data.get('email_recipients', [])
        
        if not slack_enabled and not (email_enabled and email_recipients):
            raise serializers.ValidationError(
                "At least one notification method must be enabled and properly configured"
            )
        
        # Validate Slack configuration
        if slack_enabled and not data.get('slack_channel'):
            data['slack_channel'] = '#alerts'  # Default channel
        
        return data


class AlertRuleCreateSerializer(AlertRuleSerializer):
    """
    Serializer for creating AlertRule instances
    """
    
    def create(self, validated_data):
        # Set the created_by field to the current user
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AlertHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for AlertHistory model
    """
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    rule_severity = serializers.CharField(source='rule.severity', read_only=True)
    rule_severity_display = serializers.CharField(source='rule.get_severity_display', read_only=True)
    rule_alert_type = serializers.CharField(source='rule.alert_type', read_only=True)
    rule_metric_name = serializers.CharField(source='rule.metric_name', read_only=True)
    resolved_by_email = serializers.CharField(source='resolved_by.email', read_only=True)
    is_resolved = serializers.BooleanField(read_only=True)
    notification_success = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = AlertHistory
        fields = [
            'id', 'rule', 'rule_name', 'rule_severity', 'rule_severity_display',
            'rule_alert_type', 'rule_metric_name', 'triggered_at', 'metric_value',
            'message', 'context_data', 'slack_sent', 'slack_response',
            'email_sent', 'email_response', 'resolved_at', 'resolved_by',
            'resolved_by_email', 'resolution_notes', 'is_resolved',
            'notification_success'
        ]
        read_only_fields = [
            'id', 'triggered_at', 'slack_sent', 'slack_response',
            'email_sent', 'email_response', 'is_resolved', 'notification_success'
        ]


class AlertHistoryResolveSerializer(serializers.Serializer):
    """
    Serializer for resolving alert history
    """
    resolution_notes = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    
    def update(self, instance, validated_data):
        """Resolve the alert"""
        user = self.context['request'].user
        notes = validated_data.get('resolution_notes', '')
        instance.resolve(user=user, notes=notes)
        return instance


class AlertStatisticsSerializer(serializers.Serializer):
    """
    Serializer for alert statistics
    """
    total_rules = serializers.IntegerField()
    active_rules = serializers.IntegerField()
    inactive_rules = serializers.IntegerField()
    
    total_alerts_24h = serializers.IntegerField()
    total_alerts_week = serializers.IntegerField()
    total_alerts_month = serializers.IntegerField()
    
    critical_alerts_24h = serializers.IntegerField()
    high_alerts_24h = serializers.IntegerField()
    medium_alerts_24h = serializers.IntegerField()
    low_alerts_24h = serializers.IntegerField()
    
    unresolved_alerts = serializers.IntegerField()
    resolved_alerts_24h = serializers.IntegerField()
    
    notification_success_rate_24h = serializers.FloatField()
    most_triggered_rule = serializers.CharField()
    most_triggered_metric = serializers.CharField()
    
    alerts_by_hour = serializers.ListField(child=serializers.DictField())
    alerts_by_severity = serializers.DictField()
    alerts_by_type = serializers.DictField()


class TestNotificationSerializer(serializers.Serializer):
    """
    Serializer for testing notifications
    """
    NOTIFICATION_TYPES = [
        ('slack', 'Slack Only'),
        ('email', 'Email Only'),
        ('both', 'Both Slack and Email'),
    ]
    
    notification_type = serializers.ChoiceField(
        choices=NOTIFICATION_TYPES,
        default='both',
        help_text="Type of notification to test"
    )
    custom_channel = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Custom Slack channel for testing (optional)"
    )
    custom_recipients = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        allow_empty=True,
        help_text="Custom email recipients for testing (optional)"
    )


class ManualTriggerSerializer(serializers.Serializer):
    """
    Serializer for manually triggering alert checks
    """
    rule_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="List of specific rule IDs to check (empty = check all)"
    )
    force = serializers.BooleanField(
        default=False,
        help_text="Force trigger even if rules are in cooldown"
    )