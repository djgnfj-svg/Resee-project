"""
Alert engine for evaluating rules and triggering notifications
"""
import logging
from datetime import timedelta
from typing import List, Dict, Any
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q

from ..models import AlertRule, AlertHistory
from .metric_collector import MetricCollector
from .slack_notifier import SlackNotifier
from .email_notifier import EmailNotifier

logger = logging.getLogger(__name__)


class AlertEngine:
    """
    Main alert engine for evaluating rules and sending notifications
    """
    
    def __init__(self):
        self.metric_collector = MetricCollector()
        self.slack_notifier = SlackNotifier()
        self.email_notifier = EmailNotifier()
    
    def check_all_rules(self) -> Dict[str, Any]:
        """
        Check all active alert rules and trigger alerts if conditions are met
        
        Returns:
            Dictionary with check results and statistics
        """
        logger.info("Starting alert rule evaluation")
        
        results = {
            'timestamp': timezone.now(),
            'rules_checked': 0,
            'alerts_triggered': 0,
            'alerts_sent': 0,
            'errors': []
        }
        
        try:
            # Get active alert rules
            active_rules = self._get_active_rules()
            results['rules_checked'] = len(active_rules)
            
            for rule in active_rules:
                try:
                    if self._should_check_rule(rule):
                        alert_triggered = self._check_rule(rule)
                        if alert_triggered:
                            results['alerts_triggered'] += 1
                            if alert_triggered.notification_success:
                                results['alerts_sent'] += 1
                                
                except Exception as e:
                    error_msg = f"Error checking rule {rule.name}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            logger.info(
                f"Alert check completed: {results['rules_checked']} rules checked, "
                f"{results['alerts_triggered']} alerts triggered, "
                f"{results['alerts_sent']} alerts sent successfully"
            )
            
        except Exception as e:
            error_msg = f"Critical error in alert engine: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results
    
    def check_specific_rule(self, rule_id: int) -> Dict[str, Any]:
        """
        Check a specific alert rule manually
        
        Args:
            rule_id: ID of the alert rule to check
            
        Returns:
            Dictionary with check results
        """
        try:
            rule = AlertRule.objects.get(id=rule_id, is_active=True)
            
            result = {
                'rule_name': rule.name,
                'timestamp': timezone.now(),
                'alert_triggered': False,
                'metric_value': None,
                'threshold_value': rule.threshold_value,
                'condition': rule.get_condition_display(),
                'error': None
            }
            
            # Get current metric value
            metric_value = self.metric_collector.get_metric_value(
                rule.metric_name, 
                rule.time_window_minutes
            )
            result['metric_value'] = metric_value
            
            # Check condition
            if self._evaluate_condition(rule, metric_value):
                # Force trigger even if in cooldown for manual checks
                alert_history = self._trigger_alert(rule, metric_value, force=True)
                result['alert_triggered'] = True
                result['alert_id'] = alert_history.id if alert_history else None
            
            return result
            
        except AlertRule.DoesNotExist:
            return {
                'error': f'Alert rule with ID {rule_id} not found or inactive',
                'timestamp': timezone.now()
            }
        except Exception as e:
            logger.error(f"Error checking rule {rule_id}: {str(e)}")
            return {
                'error': str(e),
                'timestamp': timezone.now()
            }
    
    def _get_active_rules(self) -> List[AlertRule]:
        """Get all active alert rules with caching"""
        cache_key = 'active_alert_rules'
        rules = cache.get(cache_key)
        
        if rules is None:
            rules = list(AlertRule.objects.filter(is_active=True).select_related('created_by'))
            cache.set(cache_key, rules, 300)  # 5 minute cache
        
        return rules
    
    def _should_check_rule(self, rule: AlertRule) -> bool:
        """
        Determine if a rule should be checked based on cooldown and rate limiting
        
        Args:
            rule: AlertRule instance
            
        Returns:
            True if rule should be checked
        """
        # Check if rule is in cooldown period
        if rule.is_in_cooldown():
            logger.debug(f"Rule {rule.name} is in cooldown period")
            return False
        
        # Check hourly rate limit
        recent_count = rule.get_recent_alert_count()
        if recent_count >= rule.max_alerts_per_hour:
            logger.warning(
                f"Rule {rule.name} has reached hourly limit: {recent_count}/{rule.max_alerts_per_hour}"
            )
            return False
        
        return True
    
    def _check_rule(self, rule: AlertRule) -> AlertHistory:
        """
        Check a single alert rule and trigger if conditions are met
        
        Args:
            rule: AlertRule instance
            
        Returns:
            AlertHistory instance if alert was triggered, None otherwise
        """
        try:
            # Get current metric value
            metric_value = self.metric_collector.get_metric_value(
                rule.metric_name,
                rule.time_window_minutes
            )
            
            logger.debug(
                f"Rule {rule.name}: metric_value={metric_value}, "
                f"condition={rule.condition}, threshold={rule.threshold_value}"
            )
            
            # Evaluate condition
            if self._evaluate_condition(rule, metric_value):
                logger.info(f"Alert triggered for rule: {rule.name}")
                return self._trigger_alert(rule, metric_value)
                
        except Exception as e:
            logger.error(f"Error checking rule {rule.name}: {str(e)}")
        
        return None
    
    def _evaluate_condition(self, rule: AlertRule, metric_value: float) -> bool:
        """
        Evaluate if the condition is met
        
        Args:
            rule: AlertRule instance  
            metric_value: Current metric value
            
        Returns:
            True if condition is met
        """
        threshold = rule.threshold_value
        condition = rule.condition
        
        if condition == 'gt':
            return metric_value > threshold
        elif condition == 'gte':
            return metric_value >= threshold
        elif condition == 'lt':
            return metric_value < threshold
        elif condition == 'lte':
            return metric_value <= threshold
        elif condition == 'eq':
            return abs(metric_value - threshold) < 0.01  # Float equality with tolerance
        elif condition == 'ne':
            return abs(metric_value - threshold) >= 0.01
        else:
            logger.error(f"Unknown condition operator: {condition}")
            return False
    
    def _trigger_alert(self, rule: AlertRule, metric_value: float, force: bool = False) -> AlertHistory:
        """
        Trigger an alert and send notifications
        
        Args:
            rule: AlertRule instance
            metric_value: Metric value that triggered the alert
            force: Force trigger even if in cooldown (for manual checks)
            
        Returns:
            AlertHistory instance
        """
        # Create alert message
        message = self._build_alert_message(rule, metric_value)
        
        # Create alert history record
        alert_history = AlertHistory.objects.create(
            rule=rule,
            metric_value=metric_value,
            message=message,
            context_data={
                'force_triggered': force,
                'metric_name': rule.metric_name,
                'condition': rule.condition,
                'threshold_value': rule.threshold_value,
                'time_window_minutes': rule.time_window_minutes
            }
        )
        
        # Send notifications
        self._send_notifications(rule, alert_history, message)
        
        return alert_history
    
    def _build_alert_message(self, rule: AlertRule, metric_value: float) -> str:
        """
        Build human-readable alert message
        
        Args:
            rule: AlertRule instance
            metric_value: Current metric value
            
        Returns:
            Formatted alert message
        """
        severity_emoji = {
            'low': '🟡',
            'medium': '🟠', 
            'high': '🔴',
            'critical': '💥'
        }
        
        emoji = severity_emoji.get(rule.severity, '⚠️')
        
        message = f"{emoji} **{rule.get_severity_display().upper()} ALERT: {rule.name}**\n\n"
        message += f"**Metric:** {rule.get_metric_name_display()}\n"
        message += f"**Current Value:** {metric_value:.2f}\n"
        message += f"**Threshold:** {rule.get_condition_display()} {rule.threshold_value}\n"
        message += f"**Time Window:** {rule.time_window_minutes} minutes\n"
        message += f"**Time:** {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        
        if rule.description:
            message += f"**Description:** {rule.description}\n"
        
        return message
    
    def _send_notifications(self, rule: AlertRule, alert_history: AlertHistory, message: str):
        """
        Send notifications via configured channels
        
        Args:
            rule: AlertRule instance
            alert_history: AlertHistory instance
            message: Alert message
        """
        # Send Slack notification
        if rule.slack_enabled:
            try:
                slack_result = self.slack_notifier.send_alert(
                    channel=rule.slack_channel or '#alerts',
                    message=message,
                    severity=rule.severity,
                    rule_name=rule.name
                )
                
                alert_history.slack_sent = slack_result.get('success', False)
                alert_history.slack_response = slack_result
                
                if slack_result.get('success'):
                    logger.info(f"Slack notification sent for rule: {rule.name}")
                else:
                    logger.error(f"Failed to send Slack notification: {slack_result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Error sending Slack notification: {str(e)}")
                alert_history.slack_response = {'error': str(e)}
        
        # Send email notification
        if rule.email_enabled and rule.email_recipients:
            try:
                email_result = self.email_notifier.send_alert(
                    recipients=rule.email_recipients,
                    subject=f"[{rule.get_severity_display().upper()}] {rule.name}",
                    message=message,
                    rule=rule
                )
                
                alert_history.email_sent = email_result.get('success', False)
                alert_history.email_response = email_result
                
                if email_result.get('success'):
                    logger.info(f"Email notification sent for rule: {rule.name}")
                else:
                    logger.error(f"Failed to send email notification: {email_result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Error sending email notification: {str(e)}")
                alert_history.email_response = {'error': str(e)}
        
        # Save notification results
        alert_history.save(update_fields=['slack_sent', 'slack_response', 'email_sent', 'email_response'])