# Generated manually for alert models

from django.db import migrations, models
import django.core.validators
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('monitoring', '0002_auto_20250826_1150'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlertRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Alert rule name', max_length=100)),
                ('description', models.TextField(blank=True, help_text='Description of the alert rule')),
                ('alert_type', models.CharField(choices=[('system_error', 'System Error'), ('performance', 'Performance Issue'), ('security', 'Security Alert'), ('business', 'Business Metric Alert'), ('database', 'Database Issue'), ('ai_usage', 'AI Usage Alert')], max_length=20)),
                ('severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], max_length=10)),
                ('metric_name', models.CharField(choices=[('cpu_usage', 'CPU Usage (%)'), ('memory_usage', 'Memory Usage (%)'), ('disk_usage', 'Disk Usage (%)'), ('api_response_time', 'API Response Time (ms)'), ('api_error_rate', 'API Error Rate (%)'), ('api_request_count', 'API Request Count'), ('db_connection_count', 'Database Connections'), ('db_query_time', 'Database Query Time (ms)'), ('slow_query_count', 'Slow Query Count'), ('error_count', 'Error Count'), ('critical_error_count', 'Critical Error Count'), ('ai_cost_daily', 'Daily AI Cost (USD)'), ('ai_token_usage', 'AI Token Usage'), ('ai_failure_rate', 'AI Failure Rate (%)'), ('active_user_count', 'Active User Count'), ('signup_count', 'Daily Signup Count'), ('subscription_count', 'Daily Subscription Count')], max_length=50)),
                ('condition', models.CharField(choices=[('gt', 'Greater Than (>)'), ('gte', 'Greater Than or Equal (>=)'), ('lt', 'Less Than (<)'), ('lte', 'Less Than or Equal (<=)'), ('eq', 'Equal To (==)'), ('ne', 'Not Equal To (!=)')], max_length=10)),
                ('threshold_value', models.FloatField(help_text='Threshold value to trigger alert')),
                ('time_window_minutes', models.IntegerField(default=5, help_text='Time window in minutes to evaluate the condition', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(1440)])),
                ('slack_enabled', models.BooleanField(default=True)),
                ('slack_channel', models.CharField(blank=True, default='#alerts', max_length=50)),
                ('email_enabled', models.BooleanField(default=True)),
                ('email_recipients', models.JSONField(blank=True, default=list, help_text='List of email addresses to notify')),
                ('cooldown_minutes', models.IntegerField(default=30, help_text='Minimum time between alerts for the same rule', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(1440)])),
                ('max_alerts_per_hour', models.IntegerField(default=10, help_text='Maximum alerts per hour for this rule', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, help_text='User who created this rule', null=True, on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'alerts_alert_rule',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['is_active', 'metric_name'], name='alerts_alert_rule_is_active_metric_idx'),
                    models.Index(fields=['alert_type', 'severity'], name='alerts_alert_rule_alert_type_severity_idx'),
                    models.Index(fields=['created_at'], name='alerts_alert_rule_created_at_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='AlertHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('triggered_at', models.DateTimeField(auto_now_add=True)),
                ('metric_value', models.FloatField(help_text='Metric value that triggered the alert')),
                ('message', models.TextField(help_text='Alert message sent to users')),
                ('context_data', models.JSONField(blank=True, default=dict, help_text='Additional context data for debugging')),
                ('slack_sent', models.BooleanField(default=False)),
                ('slack_response', models.JSONField(blank=True, help_text='Response from Slack API', null=True)),
                ('email_sent', models.BooleanField(default=False)),
                ('email_response', models.JSONField(blank=True, help_text='Response from email service', null=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('resolution_notes', models.TextField(blank=True)),
                ('resolved_by', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='resolved_alerts', to=settings.AUTH_USER_MODEL)),
                ('rule', models.ForeignKey(on_delete=models.CASCADE, to='monitoring.alertrule')),
            ],
            options={
                'db_table': 'alerts_alert_history',
                'ordering': ['-triggered_at'],
                'indexes': [
                    models.Index(fields=['rule', 'triggered_at'], name='alerts_alert_history_rule_triggered_idx'),
                    models.Index(fields=['triggered_at', 'resolved_at'], name='alerts_alert_history_triggered_resolved_idx'),
                    models.Index(fields=['slack_sent', 'email_sent'], name='alerts_alert_history_slack_email_idx'),
                ],
            },
        ),
    ]