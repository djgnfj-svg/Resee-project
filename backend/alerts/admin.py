from django.contrib import admin
from .models import AlertRule, AlertHistory


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'alert_type', 'severity', 'metric_name', 
        'condition', 'threshold_value', 'is_active', 'created_at'
    ]
    list_filter = ['alert_type', 'severity', 'is_active', 'created_at']
    search_fields = ['name', 'metric_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'alert_type', 'severity', 'description', 'is_active')
        }),
        ('조건 설정', {
            'fields': ('metric_name', 'condition', 'threshold_value', 'time_window_minutes')
        }),
        ('알림 설정', {
            'fields': ('slack_enabled', 'slack_channel', 'email_enabled', 'email_recipients')
        }),
        ('중복 방지', {
            'fields': ('cooldown_minutes', 'max_alerts_per_hour')
        }),
        ('시간 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AlertHistory)
class AlertHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'rule', 'triggered_at', 'metric_value', 'slack_sent', 
        'email_sent', 'resolved_at', 'resolved_by'
    ]
    list_filter = ['rule__alert_type', 'rule__severity', 'slack_sent', 'email_sent', 'triggered_at']
    search_fields = ['rule__name', 'message']
    readonly_fields = ['triggered_at']
    date_hierarchy = 'triggered_at'
    
    fieldsets = (
        ('알림 정보', {
            'fields': ('rule', 'triggered_at', 'metric_value', 'message')
        }),
        ('발송 상태', {
            'fields': ('slack_sent', 'slack_response', 'email_sent', 'email_response')
        }),
        ('해결 상태', {
            'fields': ('resolved_at', 'resolved_by')
        }),
    )
    
    actions = ['mark_as_resolved']
    
    def mark_as_resolved(self, request, queryset):
        """선택된 알림들을 해결됨으로 표시"""
        from django.utils import timezone
        
        updated_count = 0
        for alert in queryset:
            if not alert.resolved_at:
                alert.resolved_at = timezone.now()
                alert.resolved_by = request.user
                alert.save()
                updated_count += 1
        
        self.message_user(
            request,
            f'{updated_count}개의 알림이 해결됨으로 표시되었습니다.'
        )
    
    mark_as_resolved.short_description = "선택된 알림을 해결됨으로 표시"