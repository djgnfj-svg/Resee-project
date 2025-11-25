import React from 'react';
import { Link, useLocation } from 'react-router-dom';

interface NavigationProps {
  isAuthenticated: boolean;
}

const Navigation: React.FC<NavigationProps> = ({ isAuthenticated }) => {
  const location = useLocation();

  const navigation = [
    { name: '대시보드', href: '/dashboard', current: location.pathname === '/dashboard' },
    { name: '콘텐츠', href: '/content', current: location.pathname === '/content' },
    { name: '복습', href: '/review', current: location.pathname === '/review' },
    { name: '주간시험', href: '/exams', current: location.pathname === '/exams' },
  ];

  if (!isAuthenticated) return null;

  return (
    <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
      {navigation.map((item) => (
        <Link
          key={item.name}
          to={item.href}
          aria-current={item.current ? 'page' : undefined}
          aria-label={`${item.name} 페이지로 이동`}
          className={`inline-flex items-center px-1 pt-1 text-sm font-medium transition-colors duration-200 ${
            item.current
              ? 'border-b-2 border-primary-500 text-gray-900 dark:text-gray-100'
              : 'text-gray-500 dark:text-gray-400 hover:border-gray-300 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          {item.name}
        </Link>
      ))}
    </div>
  );
};

export default React.memo(Navigation);
