# Generated migration file for alerts app

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AlertRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of the alert rule', max_length=100)),
                ('metric_name', models.CharField(choices=[('cpu_usage', 'CPU 사용률'), ('memory_usage', '메모리 사용률'), ('disk_usage', '디스크 사용률'), ('api_response_time', 'API 응답시간'), ('api_error_rate', 'API 에러율'), ('api_request_count', 'API 요청수'), ('db_connection_count', 'DB 연결수'), ('db_query_time', 'DB 쿼리시간'), ('slow_query_count', '느린 쿼리수'), ('error_count', '에러 발생수'), ('critical_error_count', '심각한 에러수'), ('ai_cost_daily', 'AI 일일 비용'), ('ai_token_usage', 'AI 토큰 사용량'), ('ai_failure_rate', 'AI 실패율'), ('active_user_count', '활성 사용자수'), ('signup_count', '가입자수'), ('subscription_count', '구독자수'), ('cache_hit_rate', '캐시 적중률'), ('cache_memory_usage', '캐시 메모리 사용량'), ('celery_queue_length', 'Celery 큐 길이'), ('celery_failed_tasks', 'Celery 실패 작업수'), ('redis_memory_usage', 'Redis 메모리 사용량'), ('postgres_connection_count', 'PostgreSQL 연결수'), ('nginx_request_rate', 'Nginx 요청률'), ('network_bytes_sent', '네트워크 송신량')], help_text='Metric to monitor', max_length=50)),
                ('condition', models.CharField(choices=[('gt', '초과 (>)'), ('gte', '이상 (>=)'), ('lt', '미만 (<)'), ('lte', '이하 (<=)'), ('eq', '같음 (=)'), ('neq', '다름 (!=)')], help_text='Condition operator', max_length=10)),
                ('threshold_value', models.FloatField(help_text='Threshold value to trigger alert')),
                ('time_window_minutes', models.IntegerField(default=5, help_text='Time window in minutes to evaluate the metric')),
                ('severity', models.CharField(choices=[('low', '낮음'), ('medium', '보통'), ('high', '높음'), ('critical', '심각')], default='medium', help_text='Alert severity level', max_length=20)),
                ('is_active', models.BooleanField(default=True, help_text='Whether the rule is active')),
                ('slack_enabled', models.BooleanField(default=False, help_text='Send Slack notifications')),
                ('slack_channel', models.CharField(blank=True, help_text='Slack channel to send notifications', max_length=100)),
                ('email_enabled', models.BooleanField(default=True, help_text='Send email notifications')),
                ('email_recipients', models.TextField(blank=True, help_text='Comma-separated email addresses')),
                ('description', models.TextField(blank=True, help_text='Description of what this alert monitors')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'alerts_rule',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AlertHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField(help_text='Alert message')),
                ('metric_value', models.FloatField(help_text='Value that triggered the alert')),
                ('triggered_at', models.DateTimeField(auto_now_add=True)),
                ('is_resolved', models.BooleanField(default=False, help_text='Whether the alert has been resolved')),
                ('resolved_at', models.DateTimeField(blank=True, help_text='When the alert was resolved', null=True)),
                ('resolution_notes', models.TextField(blank=True, help_text='Notes about the resolution')),
                ('slack_sent', models.BooleanField(default=False, help_text='Whether Slack notification was sent')),
                ('email_sent', models.BooleanField(default=False, help_text='Whether email notification was sent')),
                ('notification_success', models.BooleanField(default=True, help_text='Whether notifications were sent successfully')),
                ('notification_error', models.TextField(blank=True, help_text='Error message if notifications failed')),
                ('rule', models.ForeignKey(help_text='Alert rule that triggered this alert', on_delete=django.db.models.deletion.CASCADE, related_name='history', to='alerts.alertrule')),
            ],
            options={
                'db_table': 'alerts_history',
                'ordering': ['-triggered_at'],
            },
        ),
        migrations.AddIndex(
            model_name='alerthistory',
            index=models.Index(fields=['triggered_at'], name='alerts_hist_trigger_8d2c9f_idx'),
        ),
        migrations.AddIndex(
            model_name='alerthistory',
            index=models.Index(fields=['is_resolved'], name='alerts_hist_is_reso_088b8b_idx'),
        ),
        migrations.AddIndex(
            model_name='alerthistory',
            index=models.Index(fields=['rule', 'triggered_at'], name='alerts_hist_rule_id_8e95ad_idx'),
        ),
        migrations.AddIndex(
            model_name='alertrule',
            index=models.Index(fields=['is_active'], name='alerts_rule_is_acti_31d70f_idx'),
        ),
        migrations.AddIndex(
            model_name='alertrule',
            index=models.Index(fields=['metric_name'], name='alerts_rule_metric__6b8a79_idx'),
        ),
        migrations.AddIndex(
            model_name='alertrule',
            index=models.Index(fields=['severity'], name='alerts_rule_severit_f40ec6_idx'),
        ),
    ]