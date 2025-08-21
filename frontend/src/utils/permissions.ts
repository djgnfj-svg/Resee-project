/**
 * Permission utilities for role-based access control
 */
import { User } from '../types';

export const hasPermission = {
  /**
   * Check if user can view basic monitoring data
   */
  viewMonitoring: (user: User | null): boolean => {
    return !!user; // All authenticated users can view basic monitoring
  },

  /**
   * Check if user can manage alert rules (create, edit, delete)
   */
  manageAlerts: (user: User | null): boolean => {
    return !!user?.is_staff; // Only staff can manage alerts
  },

  /**
   * Check if user can view sensitive information (email recipients, slack channels, etc.)
   */
  viewSensitiveData: (user: User | null): boolean => {
    return !!user?.is_staff; // Only staff can see sensitive config
  },

  /**
   * Check if user can resolve alerts
   */
  resolveAlerts: (user: User | null): boolean => {
    return !!user?.is_staff; // Only staff can resolve alerts
  },

  /**
   * Check if user can test notifications
   */
  testNotifications: (user: User | null): boolean => {
    return !!user?.is_staff; // Only staff can test notifications
  },

  /**
   * Check if user can access admin features
   */
  adminAccess: (user: User | null): boolean => {
    return !!user?.is_superuser; // Only superusers can access admin features
  }
};

// PermissionGate is now in components/AccessControl.tsx

/**
 * Get user role display name
 */
export const getUserRole = (user: User | null): string => {
  if (!user) return 'Guest';
  if (user.is_superuser) return 'Super Admin';
  if (user.is_staff) return 'Admin';
  return 'User';
};

/**
 * Check if user has any admin privileges
 */
export const isAdmin = (user: User | null): boolean => {
  return !!(user?.is_staff || user?.is_superuser);
};