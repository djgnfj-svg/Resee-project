"""
Celery tasks for alert system
"""
import logging
from datetime import timedelta
from typing import Dict, Any

from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Count, Q

from .models import AlertRule, AlertHistory
from .services import AlertEngine, EmailNotifier

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def check_alert_rules(self):
    """
    Check all active alert rules and trigger notifications
    
    This task runs periodically (every minute) to evaluate all active alert rules
    """
    try:
        logger.info("Starting scheduled alert rule check")
        
        engine = AlertEngine()
        results = engine.check_all_rules()
        
        # Cache results for monitoring dashboard
        cache.set('last_alert_check_results', results, 3600)  # 1 hour cache
        
        logger.info(
            f"Alert check completed successfully: "
            f"{results['rules_checked']} rules checked, "
            f"{results['alerts_triggered']} alerts triggered, "
            f"{results['alerts_sent']} alerts sent"
        )
        
        return results
        
    except Exception as exc:
        logger.error(f"Error in check_alert_rules task: {str(exc)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = (2 ** self.request.retries) * 60  # 60s, 2m, 4m
            logger.info(f"Retrying in {retry_delay} seconds...")
            raise self.retry(countdown=retry_delay)
        
        # After max retries, log final failure
        logger.critical(f"Alert check task failed after {self.max_retries} retries: {str(exc)}")
        raise


@shared_task(bind=True, max_retries=2)
def check_specific_alert_rule(self, rule_id: int):
    """
    Check a specific alert rule (for manual triggering)
    
    Args:
        rule_id: ID of the alert rule to check
    """
    try:
        logger.info(f"Checking specific alert rule: {rule_id}")
        
        engine = AlertEngine()
        result = engine.check_specific_rule(rule_id)
        
        logger.info(f"Specific rule check completed: {result}")
        
        return result
        
    except Exception as exc:
        logger.error(f"Error checking specific rule {rule_id}: {str(exc)}")
        
        if self.request.retries < self.max_retries:
            retry_delay = 30  # 30 seconds
            raise self.retry(countdown=retry_delay)
        
        raise


@shared_task(bind=True, max_retries=2)
def send_daily_alert_summary(self, recipients=None):
    """
    Send daily summary of alert activity
    
    Args:
        recipients: List of email recipients (optional)
    """
    try:
        logger.info("Generating daily alert summary")
        
        # Calculate summary data for the last 24 hours
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=24)
        
        summary_data = _calculate_alert_summary(start_time, end_time)
        
        # Get default recipients if none provided
        if not recipients:
            recipients = _get_default_summary_recipients()
        
        if recipients:
            email_notifier = EmailNotifier()
            result = email_notifier.send_daily_summary(recipients, summary_data)
            
            logger.info(f"Daily summary sent to {len(recipients)} recipients")
            return {
                'success': True,
                'recipients_count': len(recipients),
                'summary_data': summary_data,
                'email_result': result
            }
        else:
            logger.warning("No recipients configured for daily summary")
            return {
                'success': False,
                'error': 'No recipients configured'
            }
            
    except Exception as exc:
        logger.error(f"Error sending daily alert summary: {str(exc)}")
        
        if self.request.retries < self.max_retries:
            retry_delay = 300  # 5 minutes
            raise self.retry(countdown=retry_delay)
        
        raise


@shared_task
def cleanup_old_alert_history(days_to_keep=30):
    """
    Clean up old alert history records
    
    Args:
        days_to_keep: Number of days of history to keep (default: 30)
    """
    try:
        logger.info(f"Starting cleanup of alert history older than {days_to_keep} days")
        
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # Delete old alert history
        deleted_count, deleted_details = AlertHistory.objects.filter(
            triggered_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleanup completed: {deleted_count} alert history records deleted")
        
        return {
            'success': True,
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat(),
            'deleted_details': deleted_details
        }
        
    except Exception as exc:
        logger.error(f"Error in alert history cleanup: {str(exc)}")
        raise


@shared_task(bind=True, max_retries=1)
def test_alert_notifications(self, rule_id: int, test_type: str = 'both'):
    """
    Test alert notifications for a specific rule
    
    Args:
        rule_id: ID of the alert rule to test
        test_type: Type of test ('slack', 'email', or 'both')
    """
    try:
        logger.info(f"Testing alert notifications for rule {rule_id}, type: {test_type}")
        
        # Get the alert rule
        rule = AlertRule.objects.get(id=rule_id)
        
        results = {}
        
        # Test Slack notification
        if test_type in ['slack', 'both'] and rule.slack_enabled:
            from .services import SlackNotifier
            slack_notifier = SlackNotifier()
            
            slack_result = slack_notifier.send_test_message(rule.slack_channel)
            results['slack'] = slack_result
        
        # Test email notification
        if test_type in ['email', 'both'] and rule.email_enabled and rule.email_recipients:
            from .services import EmailNotifier
            email_notifier = EmailNotifier()
            
            email_result = email_notifier.send_test_email(rule.email_recipients)
            results['email'] = email_result
        
        logger.info(f"Test completed for rule {rule_id}: {results}")
        
        return {
            'success': True,
            'rule_name': rule.name,
            'test_type': test_type,
            'results': results
        }
        
    except AlertRule.DoesNotExist:
        error_msg = f"Alert rule {rule_id} not found"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }
    except Exception as exc:
        logger.error(f"Error testing notifications for rule {rule_id}: {str(exc)}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30)
        
        raise


@shared_task
def update_alert_metrics_cache():
    """
    Update cached alert metrics for dashboard
    """
    try:
        logger.debug("Updating alert metrics cache")
        
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_week = now - timedelta(days=7)
        
        # Calculate various metrics
        metrics = {
            'last_updated': now.isoformat(),
            'alerts_last_24h': AlertHistory.objects.filter(triggered_at__gte=last_24h).count(),
            'alerts_last_week': AlertHistory.objects.filter(triggered_at__gte=last_week).count(),
            'critical_alerts_last_24h': AlertHistory.objects.filter(
                triggered_at__gte=last_24h,
                rule__severity='critical'
            ).count(),
            'unresolved_alerts': AlertHistory.objects.filter(resolved_at__isnull=True).count(),
            'active_rules': AlertRule.objects.filter(is_active=True).count(),
            'total_rules': AlertRule.objects.count(),
        }
        
        # Alert breakdown by severity
        severity_breakdown = AlertHistory.objects.filter(
            triggered_at__gte=last_24h
        ).values('rule__severity').annotate(count=Count('id'))
        
        metrics['severity_breakdown'] = {
            item['rule__severity']: item['count'] 
            for item in severity_breakdown
        }
        
        # Alert breakdown by type
        type_breakdown = AlertHistory.objects.filter(
            triggered_at__gte=last_24h
        ).values('rule__alert_type').annotate(count=Count('id'))
        
        metrics['type_breakdown'] = {
            item['rule__alert_type']: item['count'] 
            for item in type_breakdown
        }
        
        # Cache metrics
        cache.set('alert_metrics', metrics, 300)  # 5 minute cache
        
        logger.debug("Alert metrics cache updated successfully")
        
        return metrics
        
    except Exception as exc:
        logger.error(f"Error updating alert metrics cache: {str(exc)}")
        raise


def _calculate_alert_summary(start_time, end_time) -> Dict[str, Any]:
    """
    Calculate alert summary statistics for given time period
    """
    alerts_in_period = AlertHistory.objects.filter(
        triggered_at__gte=start_time,
        triggered_at__lte=end_time
    )
    
    summary = {
        'period_start': start_time.isoformat(),
        'period_end': end_time.isoformat(),
        'total_alerts': alerts_in_period.count(),
        'critical_alerts': alerts_in_period.filter(rule__severity='critical').count(),
        'high_alerts': alerts_in_period.filter(rule__severity='high').count(),
        'medium_alerts': alerts_in_period.filter(rule__severity='medium').count(),
        'low_alerts': alerts_in_period.filter(rule__severity='low').count(),
        'resolved_alerts': alerts_in_period.filter(resolved_at__isnull=False).count(),
        'unresolved_alerts': alerts_in_period.filter(resolved_at__isnull=True).count(),
    }
    
    # Add notification success rates
    total_alerts = summary['total_alerts']
    if total_alerts > 0:
        successful_slack = alerts_in_period.filter(slack_sent=True).count()
        successful_email = alerts_in_period.filter(email_sent=True).count()
        
        summary['slack_success_rate'] = (successful_slack / total_alerts) * 100
        summary['email_success_rate'] = (successful_email / total_alerts) * 100
    else:
        summary['slack_success_rate'] = 0
        summary['email_success_rate'] = 0
    
    # Add system health metrics if available
    from monitoring.models import APIMetrics, SystemHealth
    
    try:
        # Average API response time
        api_metrics = APIMetrics.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        )
        if api_metrics.exists():
            from django.db.models import Avg
            avg_response = api_metrics.aggregate(avg=Avg('response_time_ms'))['avg']
            summary['avg_response_time'] = round(avg_response, 2) if avg_response else None
            
            # Error rate
            total_requests = api_metrics.count()
            error_requests = api_metrics.filter(status_code__gte=400).count()
            summary['error_rate'] = (error_requests / total_requests * 100) if total_requests > 0 else 0
        
        # System uptime (simplified calculation)
        health_checks = SystemHealth.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        )
        if health_checks.exists():
            total_checks = health_checks.count()
            healthy_checks = health_checks.filter(
                postgres_status=True,
                redis_status=True
            ).count()
            summary['uptime'] = f"{(healthy_checks / total_checks * 100):.1f}%" if total_checks > 0 else "N/A"
        
    except Exception as e:
        logger.warning(f"Error calculating system health metrics: {str(e)}")
    
    return summary


def _get_default_summary_recipients():
    """
    Get default recipients for daily summary emails
    """
    from django.conf import settings
    
    # Try to get from settings first
    recipients = getattr(settings, 'ALERT_SUMMARY_RECIPIENTS', [])
    
    # If not configured, use admin emails
    if not recipients:
        admins = getattr(settings, 'ADMINS', [])
        recipients = [email for name, email in admins]
    
    return recipients