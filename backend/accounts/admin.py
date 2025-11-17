from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.db import transaction
from django.utils import timezone
from django.utils.html import format_html

from .models import Subscription, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('is_email_verified', 'weekly_goal')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('weekly_goal',)}),
    )

    list_display = (
        'email', 'username', 'subscription_tier', 'is_email_verified',
        'weekly_goal', 'is_active', 'date_joined'
    )
    list_filter = UserAdmin.list_filter + (
        'is_email_verified',
        'subscription__tier',
        ('date_joined', admin.DateFieldListFilter),
        ('last_login', admin.DateFieldListFilter),
    )
    search_fields = ['email', 'username', 'first_name', 'last_name']
    list_per_page = 50

    # Simple Bulk Actions
    actions = [
        'bulk_verify_email',
        'bulk_send_welcome_email',
        'export_users_csv',
    ]

    def subscription_tier(self, obj):
        """Display current subscription tier with color coding"""
        if hasattr(obj, 'subscription') and obj.subscription:
            tier = obj.subscription.tier
            colors = {
                'free': '#6c757d',
                'basic': '#007bff',
                'pro': '#28a745'
            }
            color = colors.get(tier, '#6c757d')
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color,
                obj.subscription.get_tier_display()
            )
        return format_html('<span style="color: #dc3545;">No Subscription</span>')
    subscription_tier.short_description = 'Subscription'
    subscription_tier.admin_order_field = 'subscription__tier'


    # Bulk Actions Implementation
    def bulk_verify_email(self, request, queryset):
        """Bulk verify user emails"""
        with transaction.atomic():
            updated = queryset.filter(is_email_verified=False).update(
                is_email_verified=True,
                email_verification_token=None,
                email_verification_sent_at=None
            )

        self.message_user(
            request,
            f'Successfully verified {updated} user emails.',
            messages.SUCCESS
        )
    bulk_verify_email.short_description = "Verify selected user emails"

    def bulk_send_welcome_email(self, request, queryset):
        """Send welcome email to selected users with individual error tracking"""
        import logging

        from django.core.mail import send_mail

        logger = logging.getLogger(__name__)
        users = list(queryset.all())

        if len(users) > 100:
            self.message_user(
                request,
                'Cannot send to more than 100 users at once. Please select fewer users.',
                messages.ERROR
            )
            return

        # Send emails individually to track success/failure
        successful_sends = []
        failed_sends = []

        for user in users:
            subject = 'Welcome to Resee - Smart Review Platform'
            message = f'''
Dear {user.first_name or user.email},

Welcome to Resee! We're excited to have you on board.

Get started by creating your first content and begin your learning journey with our spaced repetition system.

If you have any questions, don't hesitate to reach out to our support team.

Best regards,
The Resee Team
            '''.strip()

            try:
                send_mail(
                    subject,
                    message,
                    'noreply@reseeall.com',
                    [user.email],
                    fail_silently=False,
                )
                successful_sends.append(user.email)
                logger.info(f'Welcome email sent successfully to {user.email}')
            except Exception as e:
                failed_sends.append((user.email, str(e)))
                logger.error(f'Failed to send welcome email to {user.email}: {str(e)}')

        # Report results
        if successful_sends:
            self.message_user(
                request,
                f'Successfully sent welcome emails to {len(successful_sends)} users.',
                messages.SUCCESS
            )

        if failed_sends:
            failed_list = ', '.join([email for email, _ in failed_sends[:5]])
            if len(failed_sends) > 5:
                failed_list += f' (and {len(failed_sends) - 5} more)'

            self.message_user(
                request,
                f'Failed to send emails to {len(failed_sends)} users: {failed_list}',
                messages.WARNING
            )

        # Log detailed failure information
        for email, error in failed_sends:
            logger.error(f'Email send failure - User: {email}, Error: {error}')

    bulk_send_welcome_email.short_description = "Send welcome email to selected users"


    def export_users_csv(self, request, queryset):
        """Export selected users to CSV"""
        import csv

        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="users_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Email', 'Username', 'First Name', 'Last Name', 'Date Joined',
            'Last Login', 'Is Active', 'Is Verified', 'Subscription Tier',
            'Weekly Goal'
        ])

        for user in queryset.all():
            subscription_tier = ''
            if hasattr(user, 'subscription'):
                subscription_tier = user.subscription.get_tier_display()

            writer.writerow([
                user.email,
                user.username or '',
                user.first_name or '',
                user.last_name or '',
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if user.date_joined else '',
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
                'Yes' if user.is_active else 'No',
                'Yes' if user.is_email_verified else 'No',
                subscription_tier,
                user.weekly_goal
            ])

        return response
    export_users_csv.short_description = "Export selected users to CSV"



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


