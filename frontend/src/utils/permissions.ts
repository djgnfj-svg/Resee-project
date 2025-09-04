/**
 * Permission utilities for role-based access control
 */
import { User } from '../types';

export const hasPermission = {
  /**
   * Check if user can access admin features
   */
  adminAccess: (user: User | null): boolean => {
    return !!user?.is_superuser; // Only superusers can access admin features
  },

  // Note: monitoring and alert permissions removed with monitoring app deletion
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