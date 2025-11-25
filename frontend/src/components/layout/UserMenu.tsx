import React, { useState } from 'react';
import { Link } from 'react-router-dom';

interface UserMenuProps {
  user: {
    email: string;
    username?: string;
  } | null;
  onLogout: () => void;
}

const UserMenu: React.FC<UserMenuProps> = ({ user, onLogout }) => {
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  if (!user) return null;

  return (
    <div className="hidden sm:block relative">
      <button
        onClick={() => setUserMenuOpen(!userMenuOpen)}
        className="flex items-center space-x-2 text-sm text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded-lg"
        aria-expanded={userMenuOpen}
        aria-haspopup="true"
        aria-label="사용자 메뉴"
      >
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold" aria-hidden="true">
          {user.email[0].toUpperCase()}
        </div>
        <span className="hidden md:block text-gray-900 dark:text-gray-100">
          안녕하세요, {user.username || user.email.split('@')[0]}님
        </span>
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>

      {userMenuOpen && (
        <div className="absolute right-0 mt-2 w-48 card card-elevated z-50" role="menu" aria-orientation="vertical">
          <Link
            to="/profile"
            onClick={() => setUserMenuOpen(false)}
            className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
            role="menuitem"
          >
            프로필 관리
          </Link>
          <Link
            to="/settings"
            onClick={() => setUserMenuOpen(false)}
            className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
            role="menuitem"
          >
            설정
          </Link>
          <Link
            to="/subscription"
            onClick={() => setUserMenuOpen(false)}
            className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
            role="menuitem"
          >
            구독 관리
          </Link>
          <button
            onClick={() => {
              onLogout();
              setUserMenuOpen(false);
            }}
            className="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-b-md"
            role="menuitem"
          >
            로그아웃
          </button>
        </div>
      )}
    </div>
  );
};

export default React.memo(UserMenu);
