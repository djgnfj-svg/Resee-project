# 🚨 Alert System Documentation

## Overview
The Resee Alert System provides comprehensive monitoring and alerting capabilities for the platform. It monitors system metrics, API performance, database health, and business metrics, sending notifications via Slack and email when thresholds are exceeded.

## Features

### 📊 Monitoring Capabilities
- **System Metrics**: CPU, Memory, Disk usage
- **API Performance**: Response time, error rate, request count
- **Database Health**: Connection count, query time, slow queries
- **Error Tracking**: Error count, critical errors
- **AI Services**: Cost tracking, token usage, failure rate
- **Business Metrics**: Active users, signups, subscriptions
- **Cache & Services**: Redis, Celery, cache hit rates

### 🔔 Alert Features
- **Flexible Conditions**: >, >=, <, <=, =, !=
- **Time Windows**: Configurable monitoring periods (1-60 minutes)
- **Severity Levels**: Low, Medium, High, Critical
- **Multiple Notifications**: Slack webhooks, Email alerts
- **Alert Resolution**: Manual resolution with notes
- **Alert History**: Complete audit trail

### 📈 Dashboard & UI
- **Real-time Dashboard**: System status cards and performance charts
- **Alert Management**: Create, edit, delete alert rules
- **Error Log Viewer**: Searchable error logs with bulk actions
- **Statistics View**: Alert frequency, success rates, trends

## Architecture

### Backend Components

```
backend/alerts/
├── models.py              # AlertRule, AlertHistory models
├── serializers.py         # DRF serializers for API
├── views.py               # REST API views
├── urls.py                # URL routing
├── admin.py               # Django admin interface
├── tasks.py               # Celery periodic tasks
├── services/
│   ├── metric_collector.py    # Collect metrics from monitoring
│   ├── alert_engine.py        # Evaluate rules and trigger alerts
│   ├── slack_notifier.py      # Slack webhook integration
│   └── email_notifier.py      # Email notification service
├── migrations/
└── tests.py               # Comprehensive test suite
```

### Frontend Components

```
frontend/src/
├── pages/MonitoringDashboard.tsx  # Main dashboard page
├── components/monitoring/
│   ├── SystemStatusCard.tsx       # Status display cards
│   ├── PerformanceChart.tsx       # Chart components
│   ├── ErrorLogTable.tsx          # Error log interface
│   └── AlertPanel.tsx             # Alert management panel
├── hooks/monitoring/
│   └── useMonitoring.ts           # React Query hooks
└── types/monitoring.ts            # TypeScript definitions
```

## Configuration

### Environment Variables

```bash
# Alert System Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_DEFAULT_CHANNEL=#alerts
SLACK_BOT_NAME=Resee Alert Bot
ALERT_SUMMARY_RECIPIENTS=admin@resee.com,ops@resee.com

# Email Configuration (for production)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=alerts@resee.com
EMAIL_HOST_PASSWORD=your_password
DEFAULT_FROM_EMAIL=alerts@resee.com
```

### Celery Tasks Schedule

```python
CELERY_BEAT_SCHEDULE = {
    'check-alert-rules': {
        'task': 'alerts.tasks.check_alert_rules',
        'schedule': crontab(minute='*'),  # Every minute
    },
    'send-daily-alert-summary': {
        'task': 'alerts.tasks.send_daily_alert_summary',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    'cleanup-old-alert-history': {
        'task': 'alerts.tasks.cleanup_old_alert_history',
        'schedule': crontab(hour=4, minute=0),  # Daily at 4 AM
    },
    'update-alert-metrics-cache': {
        'task': 'alerts.tasks.update_alert_metrics_cache',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}
```

## API Endpoints

### Alert Rules
- `GET /api/alerts/rules/` - List alert rules
- `POST /api/alerts/rules/` - Create alert rule
- `GET /api/alerts/rules/{id}/` - Get alert rule details
- `PUT /api/alerts/rules/{id}/` - Update alert rule
- `DELETE /api/alerts/rules/{id}/` - Delete alert rule

### Alert History
- `GET /api/alerts/history/` - List alert history
- `POST /api/alerts/history/{id}/resolve/` - Resolve alert
- `GET /api/alerts/stats/` - Alert statistics

### Testing Endpoints
- `POST /api/alerts/test/slack/` - Test Slack integration
- `POST /api/alerts/test/email/` - Test email notifications
- `POST /api/alerts/trigger/` - Manually trigger alert

## Usage Examples

### Creating Alert Rules

#### High CPU Usage Alert
```json
{
  "name": "High CPU Usage",
  "metric_name": "cpu_usage",
  "condition": "gt",
  "threshold_value": 80.0,
  "time_window_minutes": 5,
  "severity": "high",
  "slack_enabled": true,
  "slack_channel": "#system-alerts",
  "email_enabled": true,
  "email_recipients": "ops@resee.com",
  "description": "Alert when CPU usage exceeds 80% for 5 minutes"
}
```

#### API Error Rate Alert
```json
{
  "name": "High API Error Rate",
  "metric_name": "api_error_rate",
  "condition": "gte",
  "threshold_value": 5.0,
  "time_window_minutes": 10,
  "severity": "critical",
  "slack_enabled": true,
  "email_enabled": true,
  "email_recipients": "dev@resee.com,ops@resee.com"
}
```

#### AI Cost Monitoring
```json
{
  "name": "Daily AI Cost Limit",
  "metric_name": "ai_cost_daily",
  "condition": "gt",
  "threshold_value": 100.0,
  "time_window_minutes": 60,
  "severity": "medium",
  "email_enabled": true,
  "email_recipients": "finance@resee.com"
}
```

## Setup Instructions

### 1. Database Migration
```bash
# Create and run migrations
docker-compose exec backend python manage.py makemigrations alerts
docker-compose exec backend python manage.py migrate alerts
```

### 2. Configure Environment
```bash
# Add to .env file
SLACK_WEBHOOK_URL=your_slack_webhook_url
ALERT_SUMMARY_RECIPIENTS=your@email.com
```

### 3. Create Initial Alert Rules
```bash
# Access Django admin
docker-compose exec backend python manage.py createsuperuser

# Or use the API to create rules programmatically
```

### 4. Test Integration
```bash
# Test Slack notification
curl -X POST http://localhost:8000/api/alerts/test/slack/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "Test alert from Resee"}'

# Test email notification
curl -X POST http://localhost:8000/api/alerts/test/email/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"recipient": "test@example.com", "message": "Test alert"}'
```

## Best Practices

### Alert Rule Design
1. **Start with High-Level Metrics**: Begin with system-critical metrics
2. **Use Appropriate Time Windows**: Balance responsiveness vs noise
3. **Set Realistic Thresholds**: Based on historical performance data
4. **Layer Severity Levels**: Multiple alerts for different threshold levels

### Notification Strategy
1. **Route by Severity**: Critical alerts to on-call, low alerts to email
2. **Use Different Channels**: System alerts to #ops, business alerts to #product
3. **Avoid Alert Fatigue**: Don't over-alert on normal fluctuations
4. **Include Context**: Provide enough information for quick resolution

### Maintenance
1. **Regular Review**: Audit and adjust thresholds quarterly
2. **Clean Up History**: Automatic cleanup of old alert records
3. **Monitor the Monitor**: Alert on alert system failures
4. **Document Playbooks**: Link alerts to resolution procedures

## Troubleshooting

### Common Issues

#### Alerts Not Firing
- Check rule is active: `AlertRule.objects.filter(is_active=True)`
- Verify metric data exists: Check monitoring models have recent data
- Test metric collection: Use Django shell to test `MetricCollector`
- Check Celery workers: `docker-compose exec celery celery inspect active`

#### Notifications Not Sending
- Test Slack webhook URL manually
- Check email configuration in Django settings
- Review notification error logs in AlertHistory
- Verify network connectivity from backend container

#### Performance Issues
- Check alert rule count and complexity
- Review metric collection cache settings
- Monitor Celery task queue length
- Consider reducing check frequency for non-critical alerts

### Debug Commands
```bash
# Check active Celery tasks
docker-compose exec celery celery -A resee inspect active

# Test metric collector directly
docker-compose exec backend python manage.py shell
>>> from alerts.services.metric_collector import MetricCollector
>>> collector = MetricCollector()
>>> collector.get_metric_value('cpu_usage', 5)

# View recent alert history
docker-compose exec backend python manage.py shell
>>> from alerts.models import AlertHistory
>>> AlertHistory.objects.order_by('-triggered_at')[:10]
```

## Security Considerations

1. **Webhook URLs**: Keep Slack webhook URLs secure and rotate regularly
2. **Email Recipients**: Validate email addresses to prevent spam
3. **API Access**: Ensure alert management requires proper authentication
4. **Data Sensitivity**: Don't include sensitive data in alert messages
5. **Rate Limiting**: Implement rate limits on alert generation

## Monitoring the Alert System

The alert system itself should be monitored:

```json
{
  "name": "Alert System Health",
  "metric_name": "celery_failed_tasks",
  "condition": "gt",
  "threshold_value": 5,
  "time_window_minutes": 15,
  "severity": "critical"
}
```

## Future Enhancements

1. **Integration Expansion**: PagerDuty, Microsoft Teams, Discord
2. **Smart Alerting**: Machine learning for dynamic thresholds
3. **Alert Clustering**: Group related alerts to reduce noise
4. **Mobile Push**: Mobile app push notifications
5. **Webhook Integration**: Generic webhook support for custom integrations

## Support

For issues or questions about the alert system:
1. Check the troubleshooting section above
2. Review application logs in the monitoring dashboard
3. Test individual components using the debug commands
4. Create an issue in the project repository with detailed logs