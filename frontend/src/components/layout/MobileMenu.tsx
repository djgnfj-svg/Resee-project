import React from 'react';
import { Link, useLocation } from 'react-router-dom';

interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
  user: {
    email: string;
    username?: string;
  } | null;
  onLogout: () => void;
}

const MobileMenu: React.FC<MobileMenuProps> = ({ isOpen, onClose, user, onLogout }) => {
  const location = useLocation();

  const navigation = [
    { name: '대시보드', href: '/dashboard', current: location.pathname === '/dashboard' },
    { name: '콘텐츠', href: '/content', current: location.pathname === '/content' },
    { name: '복습', href: '/review', current: location.pathname === '/review' },
    { name: '주간시험', href: '/exams', current: location.pathname === '/exams' },
  ];

  if (!isOpen || !user) return null;

  return (
    <div className="sm:hidden">
      <div className="px-2 pt-2 pb-3 space-y-1 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        {navigation.map((item) => (
          <Link
            key={item.name}
            to={item.href}
            onClick={onClose}
            className={`block px-3 py-2 rounded-md text-base font-medium transition-colors ${
              item.current
                ? 'bg-primary-50 dark:bg-primary-900/20 border-primary-500 text-primary-700 dark:text-primary-300'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            {item.name}
          </Link>
        ))}

        {/* Mobile user menu items */}
        <div className="pt-4 pb-3 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center px-3 py-2">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold">
              {user.email[0].toUpperCase()}
            </div>
            <div className="ml-3">
              <div className="text-base font-medium text-gray-800 dark:text-gray-200">{user.username || user.email.split('@')[0]}</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">사용자</div>
            </div>
          </div>
          <div className="mt-3 space-y-1">
            <Link
              to="/profile"
              onClick={onClose}
              className="block px-3 py-2 rounded-md text-base font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              프로필 관리
            </Link>
            <Link
              to="/settings"
              onClick={onClose}
              className="block px-3 py-2 rounded-md text-base font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              설정
            </Link>
            <button
              onClick={() => {
                onLogout();
                onClose();
              }}
              className="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              로그아웃
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default React.memo(MobileMenu);
