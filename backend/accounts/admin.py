from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Subscription


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('timezone', 'notification_enabled', 'is_email_verified')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('timezone', 'notification_enabled')}),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_email_verified', 'is_active', 'date_joined')
    list_filter = UserAdmin.list_filter + ('is_email_verified',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'tier', 'max_interval_days', 'is_active', 'start_date', 'end_date')
    list_filter = ('tier', 'is_active', 'start_date')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'tier', 'max_interval_days')
        }),
        ('Subscription Period', {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )