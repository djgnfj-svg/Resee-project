"""
API views for alert system
"""
import logging
from datetime import timedelta
from typing import Dict, Any

from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncHour
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.cache import cache

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import AlertRule, AlertHistory
from .serializers import (
    AlertRuleSerializer, AlertRuleCreateSerializer, AlertHistorySerializer,
    AlertHistoryResolveSerializer, AlertStatisticsSerializer,
    TestNotificationSerializer, ManualTriggerSerializer
)
from .services import AlertEngine, SlackNotifier, EmailNotifier
from .tasks import check_specific_alert_rule, test_alert_notifications
from .permissions import (
    MonitoringPermission, AlertRulePermission, AlertHistoryPermission, AdminOnlyPermission
)

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class AlertRuleListCreateView(generics.ListCreateAPIView):
    """
    List all alert rules or create a new one
    """
    queryset = AlertRule.objects.all().select_related('created_by')
    serializer_class = AlertRuleSerializer
    permission_classes = [AlertRulePermission]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AlertRuleCreateSerializer
        return AlertRuleSerializer
    
    def get_queryset(self):
        queryset = AlertRule.objects.all().select_related('created_by')
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by alert type
        alert_type = self.request.query_params.get('alert_type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # Filter by metric name
        metric_name = self.request.query_params.get('metric_name')
        if metric_name:
            queryset = queryset.filter(metric_name=metric_name)
        
        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.order_by('-created_at')

    @swagger_auto_schema(
        operation_summary="List alert rules",
        operation_description="Get a paginated list of all alert rules with filtering options",
        manual_parameters=[
            openapi.Parameter('is_active', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description='Filter by active status'),
            openapi.Parameter('alert_type', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Filter by alert type'),
            openapi.Parameter('severity', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Filter by severity'),
            openapi.Parameter('metric_name', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Filter by metric name'),
            openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Search by rule name'),
        ],
        tags=['Alerts - Rules']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create alert rule",
        operation_description="Create a new alert rule",
        tags=['Alerts - Rules']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AlertRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a specific alert rule
    """
    queryset = AlertRule.objects.all().select_related('created_by')
    serializer_class = AlertRuleSerializer
    permission_classes = [AlertRulePermission]

    @swagger_auto_schema(
        operation_summary="Get alert rule",
        operation_description="Retrieve details of a specific alert rule",
        tags=['Alerts - Rules']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update alert rule",
        operation_description="Update an existing alert rule",
        tags=['Alerts - Rules']
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update alert rule",
        operation_description="Partially update an existing alert rule",
        tags=['Alerts - Rules']
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete alert rule",
        operation_description="Delete an alert rule",
        tags=['Alerts - Rules']
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class AlertHistoryListView(generics.ListAPIView):
    """
    List alert history with filtering
    """
    serializer_class = AlertHistorySerializer
    permission_classes = [AlertHistoryPermission]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = AlertHistory.objects.all().select_related('rule', 'resolved_by')
        
        # Filter by rule
        rule_id = self.request.query_params.get('rule')
        if rule_id:
            queryset = queryset.filter(rule_id=rule_id)
        
        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(rule__severity=severity)
        
        # Filter by resolved status
        resolved = self.request.query_params.get('resolved')
        if resolved is not None:
            if resolved.lower() == 'true':
                queryset = queryset.filter(resolved_at__isnull=False)
            else:
                queryset = queryset.filter(resolved_at__isnull=True)
        
        # Filter by time range
        hours = self.request.query_params.get('hours')
        if hours:
            try:
                hours_int = int(hours)
                since = timezone.now() - timedelta(hours=hours_int)
                queryset = queryset.filter(triggered_at__gte=since)
            except ValueError:
                pass
        
        return queryset.order_by('-triggered_at')

    @swagger_auto_schema(
        operation_summary="List alert history",
        operation_description="Get a paginated list of alert history with filtering options",
        manual_parameters=[
            openapi.Parameter('rule', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Filter by rule ID'),
            openapi.Parameter('severity', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Filter by severity'),
            openapi.Parameter('resolved', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description='Filter by resolved status'),
            openapi.Parameter('hours', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Filter by hours ago'),
        ],
        tags=['Alerts - History']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AlertHistoryDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific alert
    """
    queryset = AlertHistory.objects.all().select_related('rule', 'resolved_by')
    serializer_class = AlertHistorySerializer
    permission_classes = [AlertRulePermission]

    @swagger_auto_schema(
        operation_summary="Get alert history details",
        operation_description="Retrieve details of a specific alert",
        tags=['Alerts - History']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@swagger_auto_schema(
    method='post',
    operation_summary="Resolve alert",
    operation_description="Mark an alert as resolved with optional resolution notes",
    request_body=AlertHistoryResolveSerializer,
    responses={
        200: AlertHistorySerializer,
        404: "Alert not found",
        400: "Invalid input"
    },
    tags=['Alerts - History']
)
@api_view(['POST'])
@permission_classes([AdminOnlyPermission])
def resolve_alert(request, pk):
    """
    Resolve a specific alert
    """
    try:
        alert = get_object_or_404(AlertHistory, pk=pk)
        
        if alert.is_resolved:
            return Response(
                {'detail': 'Alert is already resolved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = AlertHistoryResolveSerializer(
            alert, 
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            updated_alert = serializer.save()
            result_serializer = AlertHistorySerializer(updated_alert)
            
            logger.info(f"Alert {pk} resolved by {request.user.email}")
            
            return Response(result_serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error resolving alert {pk}: {str(e)}")
        return Response(
            {'detail': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Get alert statistics",
    operation_description="Get comprehensive alert statistics and metrics",
    responses={200: AlertStatisticsSerializer},
    tags=['Alerts - Analytics']
)
@api_view(['GET'])
@permission_classes([AdminOnlyPermission])
def alert_statistics(request):
    """
    Get alert statistics and metrics
    """
    try:
        # Check cache first
        cache_key = 'alert_statistics'
        stats = cache.get(cache_key)
        
        if stats is None:
            stats = _calculate_alert_statistics()
            cache.set(cache_key, stats, 300)  # 5 minute cache
        
        serializer = AlertStatisticsSerializer(stats)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting alert statistics: {str(e)}")
        return Response(
            {'detail': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_summary="Test Slack notification",
    operation_description="Send a test message to Slack to verify integration",
    request_body=TestNotificationSerializer,
    responses={
        200: openapi.Response(description="Test message sent successfully"),
        400: "Invalid configuration or input",
        500: "Failed to send test message"
    },
    tags=['Alerts - Testing']
)
@api_view(['POST'])
@permission_classes([AdminOnlyPermission])
def test_slack_notification(request):
    """
    Test Slack notification integration
    """
    try:
        serializer = TestNotificationSerializer(data=request.data)
        
        if serializer.is_valid():
            channel = serializer.validated_data.get('custom_channel') or '#alerts'
            
            slack_notifier = SlackNotifier()
            
            if not slack_notifier.is_configured:
                return Response(
                    {'detail': 'Slack integration is not configured'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = slack_notifier.send_test_message(channel)
            
            if result['success']:
                logger.info(f"Slack test message sent successfully to {channel}")
                return Response(result, status=status.HTTP_200_OK)
            else:
                logger.error(f"Failed to send Slack test message: {result.get('error')}")
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error testing Slack notification: {str(e)}")
        return Response(
            {'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_summary="Test email notification",
    operation_description="Send a test email to verify email integration",
    request_body=TestNotificationSerializer,
    responses={
        200: openapi.Response(description="Test email sent successfully"),
        400: "Invalid configuration or input",
        500: "Failed to send test email"
    },
    tags=['Alerts - Testing']
)
@api_view(['POST'])
@permission_classes([AdminOnlyPermission])
def test_email_notification(request):
    """
    Test email notification integration
    """
    try:
        serializer = TestNotificationSerializer(data=request.data)
        
        if serializer.is_valid():
            recipients = serializer.validated_data.get('custom_recipients')
            
            email_notifier = EmailNotifier()
            
            if not email_notifier.is_configured:
                return Response(
                    {'detail': 'Email integration is not configured'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = email_notifier.send_test_email(recipients)
            
            if result['success']:
                logger.info(f"Test email sent successfully to {len(recipients or [])} recipients")
                return Response(result, status=status.HTTP_200_OK)
            else:
                logger.error(f"Failed to send test email: {result.get('error')}")
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error testing email notification: {str(e)}")
        return Response(
            {'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_summary="Manual trigger check",
    operation_description="Manually trigger alert rule checks",
    request_body=ManualTriggerSerializer,
    responses={
        200: openapi.Response(description="Alert check triggered successfully"),
        400: "Invalid input",
        500: "Failed to trigger alert check"
    },
    tags=['Alerts - Management']
)
@api_view(['POST'])
@permission_classes([AdminOnlyPermission])
def manual_trigger_check(request):
    """
    Manually trigger alert rule checks
    """
    try:
        serializer = ManualTriggerSerializer(data=request.data)
        
        if serializer.is_valid():
            rule_ids = serializer.validated_data.get('rule_ids', [])
            force = serializer.validated_data.get('force', False)
            
            if rule_ids:
                # Check specific rules
                results = []
                for rule_id in rule_ids:
                    try:
                        # Use Celery task for async processing
                        task = check_specific_alert_rule.delay(rule_id)
                        results.append({
                            'rule_id': rule_id,
                            'task_id': task.id,
                            'status': 'queued'
                        })
                    except Exception as e:
                        results.append({
                            'rule_id': rule_id,
                            'error': str(e),
                            'status': 'error'
                        })
                
                logger.info(f"Manual alert check triggered for {len(rule_ids)} rules")
                
                return Response({
                    'detail': f'Alert check triggered for {len(rule_ids)} rules',
                    'results': results
                }, status=status.HTTP_200_OK)
            
            else:
                # Check all rules using the main alert engine
                engine = AlertEngine()
                results = engine.check_all_rules()
                
                logger.info("Manual alert check triggered for all rules")
                
                return Response({
                    'detail': 'Alert check triggered for all rules',
                    'results': results
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error in manual trigger check: {str(e)}")
        return Response(
            {'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _calculate_alert_statistics() -> Dict[str, Any]:
    """
    Calculate comprehensive alert statistics
    """
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_week = now - timedelta(days=7)
    last_month = now - timedelta(days=30)
    
    # Rule statistics
    total_rules = AlertRule.objects.count()
    active_rules = AlertRule.objects.filter(is_active=True).count()
    inactive_rules = total_rules - active_rules
    
    # Alert count statistics
    total_alerts_24h = AlertHistory.objects.filter(triggered_at__gte=last_24h).count()
    total_alerts_week = AlertHistory.objects.filter(triggered_at__gte=last_week).count()
    total_alerts_month = AlertHistory.objects.filter(triggered_at__gte=last_month).count()
    
    # Severity breakdown for last 24h
    severity_counts = AlertHistory.objects.filter(
        triggered_at__gte=last_24h
    ).values('rule__severity').annotate(count=Count('id'))
    
    severity_dict = {item['rule__severity']: item['count'] for item in severity_counts}
    critical_alerts_24h = severity_dict.get('critical', 0)
    high_alerts_24h = severity_dict.get('high', 0)
    medium_alerts_24h = severity_dict.get('medium', 0)
    low_alerts_24h = severity_dict.get('low', 0)
    
    # Resolution statistics
    unresolved_alerts = AlertHistory.objects.filter(resolved_at__isnull=True).count()
    resolved_alerts_24h = AlertHistory.objects.filter(
        triggered_at__gte=last_24h,
        resolved_at__isnull=False
    ).count()
    
    # Notification success rate
    alerts_24h = AlertHistory.objects.filter(triggered_at__gte=last_24h)
    if alerts_24h.exists():
        successful_notifications = alerts_24h.filter(
            Q(slack_sent=True) | Q(email_sent=True)
        ).count()
        notification_success_rate_24h = (successful_notifications / total_alerts_24h) * 100
    else:
        notification_success_rate_24h = 0.0
    
    # Most triggered rule and metric
    most_triggered_rule_data = AlertHistory.objects.filter(
        triggered_at__gte=last_week
    ).values('rule__name').annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    most_triggered_rule = most_triggered_rule_data['rule__name'] if most_triggered_rule_data else 'None'
    
    most_triggered_metric_data = AlertHistory.objects.filter(
        triggered_at__gte=last_week
    ).values('rule__metric_name').annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    most_triggered_metric = most_triggered_metric_data['rule__metric_name'] if most_triggered_metric_data else 'None'
    
    # Hourly breakdown for last 24h
    hourly_data = AlertHistory.objects.filter(
        triggered_at__gte=last_24h
    ).annotate(
        hour=TruncHour('triggered_at')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour')
    
    alerts_by_hour = [
        {
            'hour': item['hour'].strftime('%H:00'),
            'count': item['count']
        } for item in hourly_data
    ]
    
    # Type breakdown
    type_counts = AlertHistory.objects.filter(
        triggered_at__gte=last_24h
    ).values('rule__alert_type').annotate(count=Count('id'))
    
    alerts_by_type = {item['rule__alert_type']: item['count'] for item in type_counts}
    
    return {
        'total_rules': total_rules,
        'active_rules': active_rules,
        'inactive_rules': inactive_rules,
        'total_alerts_24h': total_alerts_24h,
        'total_alerts_week': total_alerts_week,
        'total_alerts_month': total_alerts_month,
        'critical_alerts_24h': critical_alerts_24h,
        'high_alerts_24h': high_alerts_24h,
        'medium_alerts_24h': medium_alerts_24h,
        'low_alerts_24h': low_alerts_24h,
        'unresolved_alerts': unresolved_alerts,
        'resolved_alerts_24h': resolved_alerts_24h,
        'notification_success_rate_24h': round(notification_success_rate_24h, 2),
        'most_triggered_rule': most_triggered_rule,
        'most_triggered_metric': most_triggered_metric,
        'alerts_by_hour': alerts_by_hour,
        'alerts_by_severity': severity_dict,
        'alerts_by_type': alerts_by_type,
    }