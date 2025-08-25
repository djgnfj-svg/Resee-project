"""
Permission classes for monitoring and alert system
"""
from rest_framework.permissions import BasePermission


class MonitoringPermission(BasePermission):
    """
    Permission for accessing monitoring endpoints.
    Allows staff users and authenticated users to view monitoring data.
    """
    message = "모니터링 데이터에 접근할 권한이 없습니다."
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            (request.user.is_staff or request.method in ['GET', 'HEAD', 'OPTIONS'])
        )


class AlertRulePermission(BasePermission):
    """
    Permission for managing alert rules.
    Only staff users can create, update, or delete alert rules.
    """
    message = "알림 규칙을 관리할 권한이 없습니다."
    
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_staff


class AlertHistoryPermission(BasePermission):
    """
    Permission for viewing alert history.
    Staff users can view all alerts, regular users can only view their own.
    """
    message = "알림 히스토리를 조회할 권한이 없습니다."
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.created_by == request.user


class AdminOnlyPermission(BasePermission):
    """
    Permission that only allows admin users.
    """
    message = "관리자만 접근할 수 있습니다."
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff