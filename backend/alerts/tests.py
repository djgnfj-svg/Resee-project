"""
Test cases for alerts application
"""
import json
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import AlertRule, AlertHistory
from .services.alert_engine import AlertEngine
from .services.metric_collector import MetricCollector

User = get_user_model()


class AlertRuleModelTest(TestCase):
    """Test AlertRule model"""
    
    def test_create_alert_rule(self):
        rule = AlertRule.objects.create(
            name="High CPU Usage",
            metric_name="cpu_usage",
            condition="gt",
            threshold_value=80.0,
            time_window_minutes=5
        )
        self.assertEqual(rule.name, "High CPU Usage")
        self.assertTrue(rule.is_active)
        self.assertEqual(rule.severity, "medium")


class AlertHistoryModelTest(TestCase):
    """Test AlertHistory model"""
    
    def setUp(self):
        self.rule = AlertRule.objects.create(
            name="Test Rule",
            metric_name="cpu_usage",
            condition="gt",
            threshold_value=80.0
        )
    
    def test_create_alert_history(self):
        history = AlertHistory.objects.create(
            rule=self.rule,
            message="CPU usage is high",
            metric_value=85.5
        )
        self.assertEqual(history.rule, self.rule)
        self.assertFalse(history.is_resolved)
        self.assertTrue(history.notification_success)


class MetricCollectorTest(TestCase):
    """Test MetricCollector service"""
    
    def setUp(self):
        self.collector = MetricCollector()
    
    @patch('alerts.services.metric_collector.SystemHealth.objects')
    def test_get_system_metric(self, mock_health):
        mock_health.filter.return_value.aggregate.return_value = {'avg_value': 75.5}
        
        value = self.collector._get_system_metric('cpu_usage_percent', 
                                                  timezone.now() - timedelta(minutes=5),
                                                  timezone.now())
        self.assertEqual(value, 75.5)
    
    def test_unknown_metric(self):
        value = self.collector.get_metric_value('unknown_metric', 5)
        self.assertEqual(value, 0.0)


class AlertEngineTest(TestCase):
    """Test AlertEngine service"""
    
    def setUp(self):
        self.engine = AlertEngine()
        self.rule = AlertRule.objects.create(
            name="CPU Test",
            metric_name="cpu_usage",
            condition="gt",
            threshold_value=80.0
        )
    
    def test_evaluate_condition_greater_than(self):
        result = self.engine._evaluate_condition(85.0, "gt", 80.0)
        self.assertTrue(result)
        
        result = self.engine._evaluate_condition(75.0, "gt", 80.0)
        self.assertFalse(result)
    
    def test_evaluate_condition_less_than(self):
        result = self.engine._evaluate_condition(75.0, "lt", 80.0)
        self.assertTrue(result)
        
        result = self.engine._evaluate_condition(85.0, "lt", 80.0)
        self.assertFalse(result)
    
    @patch('alerts.services.alert_engine.MetricCollector')
    def test_check_rule(self, mock_collector_class):
        mock_collector = MagicMock()
        mock_collector_class.return_value = mock_collector
        mock_collector.get_metric_value.return_value = 85.0
        
        with patch.object(self.engine, '_send_notifications') as mock_send:
            mock_send.return_value = (True, True, None)
            
            result = self.engine.check_rule(self.rule)
            self.assertTrue(result)
            
            # Check that alert history was created
            history = AlertHistory.objects.filter(rule=self.rule).first()
            self.assertIsNotNone(history)
            self.assertEqual(history.metric_value, 85.0)


class AlertAPITest(APITestCase):
    """Test Alert API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        self.rule = AlertRule.objects.create(
            name="API Test Rule",
            metric_name="cpu_usage",
            condition="gt",
            threshold_value=80.0
        )
    
    def test_list_alert_rules(self):
        url = reverse('alerts:rule-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_alert_rule(self):
        url = reverse('alerts:rule-list')
        data = {
            'name': 'Memory Alert',
            'metric_name': 'memory_usage',
            'condition': 'gte',
            'threshold_value': 90.0,
            'time_window_minutes': 10,
            'severity': 'high',
            'email_enabled': True,
            'email_recipients': 'admin@test.com',
            'description': 'Monitor memory usage'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AlertRule.objects.count(), 2)
    
    def test_update_alert_rule(self):
        url = reverse('alerts:rule-detail', kwargs={'pk': self.rule.pk})
        data = {
            'name': 'Updated Rule',
            'threshold_value': 85.0
        }
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.rule.refresh_from_db()
        self.assertEqual(self.rule.name, 'Updated Rule')
        self.assertEqual(self.rule.threshold_value, 85.0)
    
    def test_delete_alert_rule(self):
        url = reverse('alerts:rule-detail', kwargs={'pk': self.rule.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(AlertRule.objects.count(), 0)
    
    def test_get_alert_statistics(self):
        # Create some test history
        AlertHistory.objects.create(
            rule=self.rule,
            message="Test alert",
            metric_value=85.0
        )
        
        url = reverse('alerts:alert-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('total_alerts_24h', data)
        self.assertIn('unresolved_alerts', data)
        self.assertIn('active_rules', data)
    
    def test_resolve_alert(self):
        history = AlertHistory.objects.create(
            rule=self.rule,
            message="Test alert",
            metric_value=85.0
        )
        
        url = reverse('alerts:alert-resolve', kwargs={'pk': history.pk})
        data = {'resolution_notes': 'Fixed by restarting service'}
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        history.refresh_from_db()
        self.assertTrue(history.is_resolved)
        self.assertIsNotNone(history.resolved_at)
        self.assertEqual(history.resolution_notes, 'Fixed by restarting service')


class AlertNotificationTest(TestCase):
    """Test alert notification functionality"""
    
    def setUp(self):
        self.rule = AlertRule.objects.create(
            name="Notification Test",
            metric_name="cpu_usage",
            condition="gt",
            threshold_value=80.0,
            slack_enabled=True,
            slack_channel="#alerts",
            email_enabled=True,
            email_recipients="admin@test.com"
        )
        self.engine = AlertEngine()
    
    @patch('alerts.services.slack_notifier.SlackNotifier.send_alert')
    @patch('alerts.services.email_notifier.EmailNotifier.send_alert')
    def test_send_notifications(self, mock_email, mock_slack):
        mock_slack.return_value = True
        mock_email.return_value = True
        
        slack_sent, email_sent, error = self.engine._send_notifications(
            self.rule, "Test message", 85.0
        )
        
        self.assertTrue(slack_sent)
        self.assertTrue(email_sent)
        self.assertIsNone(error)
        
        mock_slack.assert_called_once()
        mock_email.assert_called_once()
    
    @patch('alerts.services.slack_notifier.SlackNotifier.send_alert')
    def test_slack_notification_failure(self, mock_slack):
        mock_slack.side_effect = Exception("Slack error")
        
        slack_sent, email_sent, error = self.engine._send_notifications(
            self.rule, "Test message", 85.0
        )
        
        self.assertFalse(slack_sent)
        self.assertFalse(email_sent)
        self.assertIn("Slack error", error)


class AlertTaskTest(TestCase):
    """Test alert Celery tasks"""
    
    def setUp(self):
        self.rule = AlertRule.objects.create(
            name="Task Test",
            metric_name="cpu_usage",
            condition="gt",
            threshold_value=80.0
        )
    
    @patch('alerts.tasks.AlertEngine')
    def test_check_alert_rules_task(self, mock_engine_class):
        from .tasks import check_alert_rules
        
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        mock_engine.check_all_rules.return_value = 1
        
        result = check_alert_rules()
        
        self.assertEqual(result, "Checked 1 alert rules")
        mock_engine.check_all_rules.assert_called_once()
    
    def test_cleanup_old_alert_history_task(self):
        from .tasks import cleanup_old_alert_history
        
        # Create old and new history records
        old_date = timezone.now() - timedelta(days=35)
        AlertHistory.objects.create(
            rule=self.rule,
            message="Old alert",
            metric_value=85.0,
            triggered_at=old_date
        )
        
        AlertHistory.objects.create(
            rule=self.rule,
            message="New alert",
            metric_value=85.0
        )
        
        # Mock the triggered_at field for the old record
        AlertHistory.objects.filter(message="Old alert").update(
            triggered_at=old_date
        )
        
        result = cleanup_old_alert_history()
        
        # Check that only the new record remains
        remaining = AlertHistory.objects.count()
        self.assertEqual(remaining, 1)
        self.assertEqual(AlertHistory.objects.first().message, "New alert")