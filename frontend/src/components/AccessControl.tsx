import React from 'react';
import { LockClosedIcon } from '@heroicons/react/24/outline';
import { User } from '../types';
import { getUserRole } from '../utils/permissions';

interface AccessControlNoticeProps {
  user: User | null;
  requiredRole?: 'admin' | 'staff';
  children?: React.ReactNode;
}

export const AccessControlNotice: React.FC<AccessControlNoticeProps> = ({ 
  user, 
  requiredRole = 'admin',
  children 
}) => {
  return (
    <div className="rounded-md bg-yellow-50 dark:bg-yellow-900/20 p-4">
      <div className="flex">
        <div className="flex-shrink-0">
          <LockClosedIcon className="h-5 w-5 text-yellow-400" aria-hidden="true" />
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
            접근 권한 제한
          </h3>
          <div className="mt-2 text-sm text-yellow-700 dark:text-yellow-300">
            <p>
              이 기능은 {requiredRole === 'admin' ? '관리자' : '스태프'} 권한이 필요합니다.
              현재 권한: <strong>{getUserRole(user)}</strong>
            </p>
            {children && (
              <div className="mt-2">
                {children}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

interface PermissionGateProps {
  user: User | null;
  permission: 'viewMonitoring' | 'manageAlerts' | 'viewSensitiveData' | 'adminAccess';
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export const PermissionGate: React.FC<PermissionGateProps> = ({ 
  user, 
  permission, 
  fallback, 
  children 
}) => {
  let hasAccess = false;
  
  switch (permission) {
    case 'viewMonitoring':
      hasAccess = !!user;
      break;
    case 'manageAlerts':
      hasAccess = !!user?.is_staff;
      break;
    case 'viewSensitiveData':
      hasAccess = !!user?.is_staff;
      break;
    case 'adminAccess':
      hasAccess = !!user?.is_superuser;
      break;
  }
  
  if (hasAccess) {
    return <>{children}</>;
  }
  
  if (fallback) {
    return <>{fallback}</>;
  }
  
  return (
    <AccessControlNotice user={user} requiredRole={permission === 'adminAccess' ? 'admin' : 'staff'} />
  );
};