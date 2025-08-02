from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Subscription


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('is_email_verified', 'weekly_goal')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('weekly_goal',)}),
    )
    list_display = ('email', 'username', 'is_email_verified', 'weekly_goal', 'is_active', 'date_joined')
    list_filter = UserAdmin.list_filter + ('is_email_verified',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'tier', 'max_interval_days', 'is_active', 'start_date', 'end_date')
    list_filter = ('tier', 'is_active', 'start_date')
    search_fields = ('user__email', 'user__username')
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