from django.contrib import admin

from .models import Payment, PaymentPlan, Subscription, WebhookEvent


@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'tier', 'monthly_price', 'yearly_price', 'is_active', 'created_at']
    list_filter = ['tier', 'is_active']
    search_fields = ['name', 'tier']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'tier', 'description', 'is_active')
        }),
        ('가격 정보', {
            'fields': ('monthly_price', 'yearly_price')
        }),
        ('Stripe 설정', {
            'fields': ('stripe_price_id_monthly', 'stripe_price_id_yearly')
        }),
        ('기능', {
            'fields': ('features',)
        }),
        ('메타데이터', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'amount', 'currency', 'status', 'billing_cycle', 'created_at']
    list_filter = ['status', 'billing_cycle', 'currency', 'created_at']
    search_fields = ['user__email', 'plan__name', 'stripe_payment_intent_id']
    readonly_fields = ['stripe_payment_intent_id', 'created_at', 'paid_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'plan', 'amount', 'currency', 'billing_cycle')
        }),
        ('결제 상태', {
            'fields': ('status', 'failure_reason')
        }),
        ('Stripe 정보', {
            'fields': ('stripe_payment_intent_id', 'stripe_subscription_id')
        }),
        ('일시', {
            'fields': ('created_at', 'paid_at')
        })
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'billing_cycle', 'is_active', 'current_period_end', 'created_at']
    list_filter = ['is_active', 'billing_cycle', 'plan__tier', 'created_at']
    search_fields = ['user__email', 'plan__name', 'stripe_subscription_id']
    readonly_fields = ['stripe_subscription_id', 'stripe_customer_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'plan', 'billing_cycle', 'is_active')
        }),
        ('구독 기간', {
            'fields': ('current_period_start', 'current_period_end', 'trial_end', 'canceled_at')
        }),
        ('Stripe 정보', {
            'fields': ('stripe_subscription_id', 'stripe_customer_id')
        }),
        ('메타데이터', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ['stripe_event_id', 'event_type', 'processed', 'created_at']
    list_filter = ['processed', 'event_type', 'created_at']
    search_fields = ['stripe_event_id', 'event_type']
    readonly_fields = ['stripe_event_id', 'event_type', 'created_at']
    
    fieldsets = (
        ('이벤트 정보', {
            'fields': ('stripe_event_id', 'event_type', 'processed')
        }),
        ('오류 정보', {
            'fields': ('error_message',)
        }),
        ('메타데이터', {
            'fields': ('created_at',)
        })
    )