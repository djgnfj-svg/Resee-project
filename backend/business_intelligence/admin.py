"""
Django admin interface for Business Intelligence app
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg, Count
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import LearningPattern, ContentEffectiveness, SubscriptionAnalytics, SystemUsageMetrics


@admin.register(LearningPattern)
class LearningPatternAdmin(admin.ModelAdmin):
    list_display = [
        'user_email', 'date', 'reviews_completed', 'success_rate', 
        'session_duration_display', 'consecutive_days', 'activity_level'
    ]
    list_filter = [
        'date', 'success_rate', 'consecutive_days',
        ('user', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-date', '-consecutive_days']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = '사용자'
    
    def session_duration_display(self, obj):
        hours = obj.session_duration_minutes // 60
        minutes = obj.session_duration_minutes % 60
        if hours > 0:
            return f"{hours}시간 {minutes}분"
        return f"{minutes}분"
    session_duration_display.short_description = '학습 시간'
    
    def activity_level(self, obj):
        if obj.reviews_completed >= 20:
            color = 'green'
            level = '높음'
        elif obj.reviews_completed >= 10:
            color = 'orange'
            level = '보통'
        else:
            color = 'red'
            level = '낮음'
        
        return format_html(
            '<span style="color: {};">{}</span>',
            color, level
        )
    activity_level.short_description = '활동 수준'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'date')
        }),
        ('일일 활동', {
            'fields': (
                'contents_created', 'reviews_completed', 'ai_questions_generated',
                'session_duration_minutes', 'login_count'
            )
        }),
        ('학습 성과', {
            'fields': (
                'success_rate', 'average_review_time_seconds', 'consecutive_days'
            )
        }),
        ('패턴 분석', {
            'fields': ('peak_activity_hour',)
        }),
        ('메타데이터', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ContentEffectiveness)
class ContentEffectivenessAdmin(admin.ModelAdmin):
    list_display = [
        'content_title', 'content_category', 'success_rate_display', 
        'total_reviews', 'difficulty_display', 'mastery_status'
    ]
    list_filter = [
        'average_difficulty_rating', 'abandonment_risk_score',
        ('content__category', admin.RelatedOnlyFieldListFilter),
        ('content__content_type', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = ['content__title', 'content__user__email']
    readonly_fields = ['created_at', 'updated_at', 'success_rate']
    ordering = ['-total_reviews', '-success_rate']
    
    def content_title(self, obj):
        return obj.content.title
    content_title.short_description = '콘텐츠'
    
    def content_category(self, obj):
        return obj.content.category.name if obj.content.category else '-'
    content_category.short_description = '카테고리'
    
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
    
    def difficulty_display(self, obj):
        rating = obj.average_difficulty_rating
        stars = '★' * int(rating) + '☆' * (5 - int(rating))
        return f"{stars} ({rating:.1f})"
    difficulty_display.short_description = '난이도'
    
    def mastery_status(self, obj):
        if obj.time_to_master_days:
            if obj.time_to_master_days <= 7:
                return format_html('<span style="color: green;">빠름 ({}일)</span>', obj.time_to_master_days)
            elif obj.time_to_master_days <= 21:
                return format_html('<span style="color: orange;">보통 ({}일)</span>', obj.time_to_master_days)
            else:
                return format_html('<span style="color: red;">느림 ({}일)</span>', obj.time_to_master_days)
        return '측정중'
    mastery_status.short_description = '마스터 속도'


@admin.register(SubscriptionAnalytics)
class SubscriptionAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'user_email', 'subscription_tier', 'tier_duration', 
        'feature_adoption_display', 'churn_risk_display', 'is_active'
    ]
    list_filter = [
        'subscription_tier', 'is_active', 
        'tier_start_date', 'churn_risk_score'
    ]
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-tier_start_date', '-churn_risk_score']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = '사용자'
    
    def tier_duration(self, obj):
        from django.utils import timezone
        if obj.tier_end_date:
            duration = (obj.tier_end_date - obj.tier_start_date).days
        else:
            duration = (timezone.now() - obj.tier_start_date).days
        return f"{duration}일"
    tier_duration.short_description = '구독 기간'
    
    def feature_adoption_display(self, obj):
        score = obj.feature_adoption_score
        if score >= 80:
            color = 'green'
            level = '높음'
        elif score >= 50:
            color = 'orange'
            level = '보통'
        else:
            color = 'red'
            level = '낮음'
        
        return format_html(
            '<span style="color: {};">{} ({:.1f}%)</span>',
            color, level, score
        )
    feature_adoption_display.short_description = '기능 활용도'
    
    def churn_risk_display(self, obj):
        risk = obj.churn_risk_score
        if risk >= 70:
            color = 'red'
            level = '높음'
        elif risk >= 40:
            color = 'orange'
            level = '보통'
        else:
            color = 'green'
            level = '낮음'
        
        return format_html(
            '<span style="color: {};">{} ({:.1f}%)</span>',
            color, level, risk
        )
    churn_risk_display.short_description = '이탈 위험'


@admin.register(SystemUsageMetrics)
class SystemUsageMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'active_users_daily', 'subscription_revenue_display',
        'ai_cost_display', 'system_health_display'
    ]
    list_filter = ['date']
    ordering = ['-date']
    readonly_fields = ['created_at', 'updated_at']
    
    def subscription_revenue_display(self, obj):
        return f"${obj.subscription_revenue_usd:,.2f}"
    subscription_revenue_display.short_description = '구독 매출'
    
    def ai_cost_display(self, obj):
        return f"${obj.ai_cost_usd:,.4f}"
    ai_cost_display.short_description = 'AI 비용'
    
    def system_health_display(self, obj):
        uptime = obj.uptime_percentage
        error_rate = obj.error_rate_percentage
        
        if uptime >= 99.9 and error_rate <= 1:
            color = 'green'
            status = '우수'
        elif uptime >= 99.5 and error_rate <= 2:
            color = 'orange'
            status = '양호'
        else:
            color = 'red'
            status = '주의'
        
        return format_html(
            '<span style="color: {};">{} (가동률: {:.2f}%)</span>',
            color, status, uptime
        )
    system_health_display.short_description = '시스템 상태'
    
    fieldsets = (
        ('날짜', {
            'fields': ('date',)
        }),
        ('사용자 메트릭', {
            'fields': (
                'total_users', 'active_users_daily', 'new_users', 'churned_users'
            )
        }),
        ('구독 메트릭', {
            'fields': (
                'free_users', 'basic_users', 'pro_users', 'subscription_revenue_usd'
            )
        }),
        ('콘텐츠 메트릭', {
            'fields': (
                'total_content_created', 'total_reviews_completed', 'average_success_rate'
            )
        }),
        ('AI 사용량', {
            'fields': (
                'ai_questions_generated', 'ai_cost_usd', 'ai_tokens_used'
            )
        }),
        ('시스템 성능', {
            'fields': (
                'average_api_response_time_ms', 'error_rate_percentage', 'uptime_percentage'
            )
        }),
        ('메타데이터', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def changelist_view(self, request, extra_context=None):
        # Add summary statistics to the changelist
        response = super().changelist_view(request, extra_context=extra_context)
        
        try:
            qs = response.context_data['cl'].queryset
            summary_stats = qs.aggregate(
                avg_daily_users=Avg('active_users_daily'),
                total_revenue=models.Sum('subscription_revenue_usd'),
                avg_uptime=Avg('uptime_percentage')
            )
            
            response.context_data['summary'] = {
                'avg_daily_users': summary_stats['avg_daily_users'] or 0,
                'total_revenue': summary_stats['total_revenue'] or 0,
                'avg_uptime': summary_stats['avg_uptime'] or 0,
            }
        except (AttributeError, KeyError):
            pass
        
        return response