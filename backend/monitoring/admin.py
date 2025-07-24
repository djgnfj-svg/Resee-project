"""
Django admin interface for monitoring models
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Avg, Count, Sum
from .models import (
    APIMetrics, DatabaseMetrics, AIMetrics, ErrorLog, 
    SystemHealth, UserActivity
)


@admin.register(APIMetrics)
class APIMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'endpoint', 'method', 'status_code', 'response_time_ms', 
        'query_count', 'user', 'timestamp'
    ]
    list_filter = [
        'method', 'status_code', 'date', 'endpoint'
    ]
    search_fields = ['endpoint', 'user__email', 'ip_address']
    readonly_fields = ['request_id', 'timestamp', 'date', 'hour']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Request Info', {
            'fields': ('endpoint', 'method', 'status_code', 'user')
        }),
        ('Performance', {
            'fields': ('response_time_ms', 'query_count', 'response_size_bytes')
        }),
        ('Cache', {
            'fields': ('cache_hits', 'cache_misses')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'request_id')
        }),
        ('Timestamps', {
            'fields': ('timestamp', 'date', 'hour')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def changelist_view(self, request, extra_context=None):
        # Add summary statistics to the changelist
        qs = self.get_queryset(request)
        
        summary = {
            'total_requests': qs.count(),
            'avg_response_time': qs.aggregate(avg=Avg('response_time_ms'))['avg'] or 0,
            'slow_requests': qs.filter(response_time_ms__gt=1000).count(),
            'error_requests': qs.filter(status_code__gte=400).count(),
        }
        
        extra_context = extra_context or {}
        extra_context['summary'] = summary
        
        return super().changelist_view(request, extra_context)


@admin.register(DatabaseMetrics)
class DatabaseMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'table_name', 'operation_type', 'execution_time_ms', 
        'rows_affected', 'is_slow_query', 'endpoint', 'timestamp'
    ]
    list_filter = [
        'operation_type', 'table_name', 'is_slow_query', 'date'
    ]
    search_fields = ['table_name', 'endpoint', 'query_hash']
    readonly_fields = ['query_hash', 'timestamp', 'date']
    date_hierarchy = 'date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(AIMetrics)
class AIMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'service_provider', 'model_name', 'operation_type',
        'tokens_used', 'cost_usd', 'processing_time_ms', 'success', 'timestamp'
    ]
    list_filter = [
        'service_provider', 'operation_type', 'success', 'date', 'subscription_tier'
    ]
    search_fields = ['user__email', 'model_name', 'operation_type']
    readonly_fields = ['timestamp', 'date']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('User & Service', {
            'fields': ('user', 'service_provider', 'model_name', 'subscription_tier')
        }),
        ('Operation', {
            'fields': ('operation_type', 'content_id', 'success')
        }),
        ('Metrics', {
            'fields': ('tokens_used', 'cost_usd', 'processing_time_ms', 'quality_score')
        }),
        ('Timestamps', {
            'fields': ('timestamp', 'date')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def changelist_view(self, request, extra_context=None):
        qs = self.get_queryset(request)
        
        summary = {
            'total_operations': qs.count(),
            'total_tokens': qs.aggregate(total=Sum('tokens_used'))['total'] or 0,
            'total_cost': qs.aggregate(total=Sum('cost_usd'))['total'] or 0,
            'success_rate': (qs.filter(success=True).count() / qs.count() * 100) if qs.count() > 0 else 0,
        }
        
        extra_context = extra_context or {}
        extra_context['summary'] = summary
        
        return super().changelist_view(request, extra_context)


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = [
        'level', 'exception_type', 'short_message', 'endpoint', 
        'occurrences', 'resolved', 'last_seen'
    ]
    list_filter = [
        'level', 'exception_type', 'resolved', 'date', 'endpoint'
    ]
    search_fields = ['message', 'exception_type', 'endpoint', 'user__email']
    readonly_fields = ['first_seen', 'last_seen', 'timestamp', 'date']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Error Info', {
            'fields': ('level', 'exception_type', 'message', 'resolved')
        }),
        ('Context', {
            'fields': ('endpoint', 'method', 'user')
        }),
        ('Request Details', {
            'fields': ('ip_address', 'user_agent', 'request_data')
        }),
        ('Occurrence Tracking', {
            'fields': ('occurrences', 'first_seen', 'last_seen')
        }),
        ('Debug Info', {
            'fields': ('traceback',),
            'classes': ('collapse',)
        }),
    )
    
    def short_message(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    short_message.short_description = 'Message'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    actions = ['mark_resolved', 'mark_unresolved']
    
    def mark_resolved(self, request, queryset):
        updated = queryset.update(resolved=True)
        self.message_user(request, f"{updated} errors marked as resolved.")
    mark_resolved.short_description = "Mark selected errors as resolved"
    
    def mark_unresolved(self, request, queryset):
        updated = queryset.update(resolved=False)
        self.message_user(request, f"{updated} errors marked as unresolved.")
    mark_unresolved.short_description = "Mark selected errors as unresolved"


@admin.register(SystemHealth)
class SystemHealthAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'cpu_usage_percent', 'memory_usage_percent', 
        'api_requests_per_minute', 'api_error_rate_percent',
        'health_status'
    ]
    list_filter = ['date', 'redis_status', 'postgres_status']
    readonly_fields = ['timestamp', 'date']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('System Resources', {
            'fields': ('cpu_usage_percent', 'memory_usage_percent', 'disk_usage_percent')
        }),
        ('Database', {
            'fields': ('db_connection_count', 'db_query_avg_time_ms', 'postgres_status')
        }),
        ('Cache', {
            'fields': ('cache_hit_rate_percent', 'cache_memory_usage_mb', 'redis_status')
        }),
        ('Services', {
            'fields': ('celery_workers_active',)
        }),
        ('API Performance', {
            'fields': ('api_requests_per_minute', 'api_error_rate_percent', 'api_avg_response_time_ms')
        }),
        ('Timestamps', {
            'fields': ('timestamp', 'date')
        }),
    )
    
    def health_status(self, obj):
        """Display overall health status with color coding"""
        if not obj.redis_status or not obj.postgres_status:
            return format_html('<span style="color: red;">Critical</span>')
        elif obj.cpu_usage_percent > 80 or obj.memory_usage_percent > 80:
            return format_html('<span style="color: orange;">Warning</span>')
        elif obj.api_error_rate_percent > 5:
            return format_html('<span style="color: orange;">Warning</span>')
        else:
            return format_html('<span style="color: green;">Healthy</span>')
    health_status.short_description = 'Status'


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'date', 'api_requests_count', 'content_created_count',
        'reviews_completed_count', 'ai_questions_generated_count', 'device_type'
    ]
    list_filter = ['date', 'device_type']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = ['first_activity', 'last_activity']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('User & Date', {
            'fields': ('user', 'date', 'device_type')
        }),
        ('Activity Counts', {
            'fields': (
                'api_requests_count', 'content_created_count', 
                'reviews_completed_count', 'ai_questions_generated_count'
            )
        }),
        ('Session Info', {
            'fields': ('session_duration_minutes', 'unique_endpoints_accessed')
        }),
        ('Device Info', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Timestamps', {
            'fields': ('first_activity', 'last_activity')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def changelist_view(self, request, extra_context=None):
        qs = self.get_queryset(request)
        
        # Calculate summary for the last 7 days
        week_ago = timezone.now().date() - timezone.timedelta(days=7)
        recent_activity = qs.filter(date__gte=week_ago)
        
        summary = {
            'total_users': qs.values('user').distinct().count(),
            'active_users_7d': recent_activity.values('user').distinct().count(),
            'avg_api_requests': recent_activity.aggregate(avg=Avg('api_requests_count'))['avg'] or 0,
            'total_content_created': recent_activity.aggregate(total=Sum('content_created_count'))['total'] or 0,
        }
        
        extra_context = extra_context or {}
        extra_context['summary'] = summary
        
        return super().changelist_view(request, extra_context)


# Custom admin site title
admin.site.site_header = "Resee Monitoring Admin"
admin.site.site_title = "Monitoring"
admin.site.index_title = "System Monitoring Dashboard"