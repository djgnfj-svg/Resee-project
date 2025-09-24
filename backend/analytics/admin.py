"""
Simple admin interface for analytics models
"""
from django.contrib import admin

from .models import DailyStats


@admin.register(DailyStats)
class DailyStatsAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'date', 'contents_created', 'reviews_completed',
        'success_rate'
    ]
    list_filter = ['date', 'success_rate']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'

    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'date')
        }),
        ('활동 메트릭', {
            'fields': (
                'contents_created', 'reviews_completed',
                'success_rate'
            )
        }),
        ('메타데이터', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )