"""
Admin interface for analytics models
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import (
    LearningPattern, 
    ContentEffectiveness, 
    SubscriptionAnalytics, 
    SystemUsageMetrics
)


@admin.register(LearningPattern)
class LearningPatternAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'date', 'reviews_completed', 'success_rate', 
        'consecutive_days', 'session_duration_minutes'
    ]
    list_filter = ['date', 'success_rate', 'consecutive_days']
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
                'ai_questions_generated', 'session_duration_minutes'
            )
        }),
        ('학습 효율성', {
            'fields': (
                'success_rate', 'average_review_time_seconds', 
                'consecutive_days'
            )
        }),
        ('참여도', {
            'fields': ('peak_activity_hour', 'login_count')
        }),
        ('메타데이터', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ContentEffectiveness)
class ContentEffectivenessAdmin(admin.ModelAdmin):
    list_display = [
        'content', 'success_rate_display', 'total_reviews', 
        'time_to_master_days', 'abandonment_risk_score'
    ]
    list_filter = [
        'average_difficulty_rating', 'abandonment_risk_score',
        'content__category', 'content__content_type'
    ]
    search_fields = ['content__title', 'content__category__name']
    readonly_fields = ['success_rate', 'created_at', 'updated_at']
    
    def success_rate_display(self, obj):
        rate = obj.success_rate
        if rate >= 80:
            color = 'green'
        elif rate >= 60:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>', 
            color, rate
        )
    success_rate_display.short_description = '성공률'


@admin.register(SubscriptionAnalytics)
class SubscriptionAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'subscription_tier', 'tier_start_date', 
        'is_active', 'upgrade_probability', 'churn_risk_score'
    ]
    list_filter = [
        'subscription_tier', 'is_active', 'tier_start_date',
        'upgrade_probability', 'churn_risk_score'
    ]
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'tier_start_date'
    
    fieldsets = (
        ('구독 정보', {
            'fields': (
                'user', 'subscription_tier', 'tier_start_date', 
                'tier_end_date', 'is_active'
            )
        }),
        ('사용량 메트릭', {
            'fields': (
                'total_content_created', 'total_reviews_completed',
                'total_ai_questions_used', 'total_session_time_hours'
            )
        }),
        ('참여도', {
            'fields': (
                'days_active', 'average_daily_reviews', 
                'feature_adoption_score'
            )
        }),
        ('예측 메트릭', {
            'fields': ('upgrade_probability', 'churn_risk_score')
        }),
        ('메타데이터', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SystemUsageMetrics)
class SystemUsageMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'total_users', 'active_users_daily', 
        'subscription_revenue_usd', 'average_success_rate',
        'error_rate_percentage'
    ]
    list_filter = ['date']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('date',)
        }),
        ('사용자 메트릭', {
            'fields': (
                'total_users', 'active_users_daily', 
                'new_users', 'churned_users'
            )
        }),
        ('구독 메트릭', {
            'fields': (
                'free_users', 'basic_users', 'pro_users',
                'subscription_revenue_usd'
            )
        }),
        ('콘텐츠 메트릭', {
            'fields': (
                'total_content_created', 'total_reviews_completed',
                'average_success_rate'
            )
        }),
        ('AI 사용량', {
            'fields': (
                'ai_questions_generated', 'ai_cost_usd', 'ai_tokens_used'
            )
        }),
        ('시스템 성능', {
            'fields': (
                'average_api_response_time_ms', 'error_rate_percentage',
                'uptime_percentage'
            )
        }),
        ('메타데이터', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )