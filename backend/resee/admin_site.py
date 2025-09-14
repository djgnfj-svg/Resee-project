"""
Custom Admin Site Configuration for Resee Platform
"""
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import path
from django.utils.translation import gettext_lazy as _

from .admin_dashboard import admin_dashboard_view


class ReseeAdminSite(AdminSite):
    """Custom admin site with enhanced dashboard"""

    site_title = _('Resee Admin')
    site_header = _('Resee Administration')
    index_title = _('Resee Admin Dashboard')
    index_template = 'admin/dashboard.html'

    def get_urls(self):
        """Override to add custom dashboard URLs"""
        urls = super().get_urls()

        custom_urls = [
            path('dashboard/', admin_dashboard_view, name='admin_dashboard'),
        ]

        return custom_urls + urls

    def index(self, request, extra_context=None):
        """Override admin index to redirect to custom dashboard"""
        return admin_dashboard_view(request)

    def each_context(self, request):
        """Override to add custom context"""
        context = super().each_context(request)
        context.update({
            'has_permission': request.user.is_active and request.user.is_staff,
            'available_apps': self.get_app_list(request),
        })
        return context


# Create custom admin site instance
admin_site = ReseeAdminSite(name='admin')

# Import and register basic admin configurations
from accounts.admin import CustomUserAdmin, SubscriptionAdmin
from content.admin import CategoryAdmin, ContentAdmin
from review.admin import ReviewScheduleAdmin, ReviewHistoryAdmin

from accounts.models import User, Subscription
from content.models import Category, Content
from review.models import ReviewSchedule, ReviewHistory

# Register basic models with custom admin site
admin_site.register(User, CustomUserAdmin)
admin_site.register(Subscription, SubscriptionAdmin)
admin_site.register(Category, CategoryAdmin)
admin_site.register(Content, ContentAdmin)
admin_site.register(ReviewSchedule, ReviewScheduleAdmin)
admin_site.register(ReviewHistory, ReviewHistoryAdmin)