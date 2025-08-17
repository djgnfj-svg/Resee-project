from django.contrib import admin

from .models import (CookieConsent, DataDeletionRequest, DataExportRequest,
                     LegalDocument, UserConsent)


@admin.register(LegalDocument)
class LegalDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'version', 'effective_date', 'is_active', 'updated_at']
    list_filter = ['document_type', 'is_active', 'effective_date']
    search_fields = ['title', 'document_type', 'version']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('title', 'document_type', 'version', 'effective_date', 'is_active')
        }),
        ('내용', {
            'fields': ('content',)
        }),
        ('메타데이터', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(UserConsent)
class UserConsentAdmin(admin.ModelAdmin):
    list_display = ['user', 'consent_type', 'document_version', 'is_consented', 'consented_at']
    list_filter = ['consent_type', 'is_consented', 'document_version', 'consented_at']
    search_fields = ['user__email', 'consent_type']
    readonly_fields = ['consented_at', 'ip_address', 'user_agent']
    
    fieldsets = (
        ('동의 정보', {
            'fields': ('user', 'consent_type', 'document_version', 'is_consented')
        }),
        ('기술적 정보', {
            'fields': ('ip_address', 'user_agent', 'consented_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(DataDeletionRequest)
class DataDeletionRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'requested_at', 'processed_by', 'processed_at']
    list_filter = ['status', 'requested_at', 'processed_at']
    search_fields = ['user__email', 'reason']
    readonly_fields = ['requested_at']
    
    fieldsets = (
        ('요청 정보', {
            'fields': ('user', 'reason', 'status', 'requested_at')
        }),
        ('처리 정보', {
            'fields': ('processed_by', 'processed_at', 'admin_notes')
        })
    )
    
    actions = ['approve_deletion', 'reject_deletion']
    
    def approve_deletion(self, request, queryset):
        """삭제 요청 승인"""
        for deletion_request in queryset:
            if deletion_request.status == 'pending':
                deletion_request.status = 'in_progress'
                deletion_request.processed_by = request.user
                deletion_request.save()
        
        self.message_user(request, f"{queryset.count()}개의 삭제 요청이 승인되었습니다.")
    
    approve_deletion.short_description = "선택된 삭제 요청 승인"
    
    def reject_deletion(self, request, queryset):
        """삭제 요청 거부"""
        for deletion_request in queryset:
            if deletion_request.status == 'pending':
                deletion_request.status = 'rejected'
                deletion_request.processed_by = request.user
                deletion_request.save()
        
        self.message_user(request, f"{queryset.count()}개의 삭제 요청이 거부되었습니다.")
    
    reject_deletion.short_description = "선택된 삭제 요청 거부"


@admin.register(DataExportRequest)
class DataExportRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'requested_at', 'processed_at', 'expires_at']
    list_filter = ['status', 'requested_at', 'processed_at']
    search_fields = ['user__email']
    readonly_fields = ['requested_at', 'processed_at', 'downloaded_at', 'file_path']
    
    fieldsets = (
        ('요청 정보', {
            'fields': ('user', 'status', 'requested_at')
        }),
        ('처리 정보', {
            'fields': ('file_path', 'expires_at', 'processed_at', 'downloaded_at')
        })
    )


@admin.register(CookieConsent)
class CookieConsentAdmin(admin.ModelAdmin):
    list_display = ['get_identifier', 'essential_cookies', 'analytics_cookies', 'marketing_cookies', 'functional_cookies', 'consented_at']
    list_filter = ['essential_cookies', 'analytics_cookies', 'marketing_cookies', 'functional_cookies', 'consented_at']
    search_fields = ['user__email', 'session_id']
    readonly_fields = ['consented_at', 'ip_address', 'user_agent']
    
    def get_identifier(self, obj):
        if obj.user:
            return obj.user.email
        return f"Session: {obj.session_id[:10]}..."
    get_identifier.short_description = '사용자/세션'
    
    fieldsets = (
        ('식별 정보', {
            'fields': ('user', 'session_id')
        }),
        ('쿠키 동의', {
            'fields': ('essential_cookies', 'analytics_cookies', 'marketing_cookies', 'functional_cookies')
        }),
        ('기술적 정보', {
            'fields': ('ip_address', 'user_agent', 'consented_at'),
            'classes': ('collapse',)
        })
    )