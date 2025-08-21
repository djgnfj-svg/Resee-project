"""
Custom permissions for alerts and monitoring system
"""
from rest_framework import permissions


class MonitoringPermission(permissions.BasePermission):
    """
    Custom permission for monitoring system:
    - Authenticated users can view basic monitoring data
    - Only staff/admins can create/modify alert rules
    - Only staff/admins can access sensitive information
    """
    
    def has_permission(self, request, view):
        # Allow authenticated users to view basic monitoring data
        if request.method in permissions.READONLY_METHODS:
            return request.user and request.user.is_authenticated
        
        # Only staff can create/modify
        return request.user and request.user.is_staff


class AlertRulePermission(permissions.BasePermission):
    """
    Alert rule permissions:
    - Authenticated users can view alert rules (limited info)
    - Only staff can create/modify/delete alert rules
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Read-only access for authenticated users
        if request.method in permissions.READONLY_METHODS:
            return True
        
        # Write access only for staff
        return request.user.is_staff


class AlertHistoryPermission(permissions.BasePermission):
    """
    Alert history permissions:
    - Authenticated users can view alert history (limited info)
    - Only staff can resolve alerts or see detailed information
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Basic read access for authenticated users
        if request.method == 'GET':
            return True
        
        # Staff only for modifications
        return request.user.is_staff


class AdminOnlyPermission(permissions.BasePermission):
    """
    Admin-only access for sensitive operations
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


def get_monitoring_permissions():
    """
    Get appropriate permissions based on user role
    """
    return [MonitoringPermission]


def get_alert_rule_permissions():
    """
    Get appropriate permissions for alert rules
    """
    return [AlertRulePermission]


def get_admin_only_permissions():
    """
    Get admin-only permissions for sensitive operations
    """
    return [AdminOnlyPermission]