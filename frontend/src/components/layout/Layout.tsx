import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { ThemeToggle } from '../common/ThemeToggle';
import NetworkStatus from '../common/NetworkStatus';
import Footer from './Footer';
import Navigation from './Navigation';
import UserMenu from './UserMenu';
import MobileMenu from './MobileMenu';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout, isAuthenticated } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200 flex flex-col">
      <nav className="bg-white dark:bg-gray-800 shadow dark:shadow-gray-700/20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 justify-between">
            <div className="flex">
              <div className="flex flex-shrink-0 items-center">
                <Link 
                  to="/" 
                  className="text-xl sm:text-2xl font-bold text-primary-600 dark:text-primary-400"
                >
                  Resee
                </Link>
              </div>
              <Navigation isAuthenticated={isAuthenticated} />
            </div>
            <div className="flex items-center space-x-3">
              <NetworkStatus showLabel={false} />
              <ThemeToggle />
              {isAuthenticated && (
                <div className="sm:hidden">
                  <button
                    onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                    className="btn btn-ghost btn-sm touch-target"
                    aria-expanded={mobileMenuOpen}
                    aria-label={mobileMenuOpen ? '메인 메뉴 닫기' : '메인 메뉴 열기'}
                  >
                    <span className="sr-only">{mobileMenuOpen ? '메인 메뉴 닫기' : '메인 메뉴 열기'}</span>
                    {!mobileMenuOpen ? (
                      <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                      </svg>
                    ) : (
                      <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    )}
                  </button>
                </div>
              )}
              {isAuthenticated ? (
                <UserMenu user={user} onLogout={logout} />
              ) : (
                <div className="flex items-center space-x-4">
                  <Link
                    to="/login"
                    className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                  >
                    로그인
                  </Link>
                  <Link
                    to="/register"
                    className="btn btn-primary btn-sm"
                  >
                    회원가입
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        <MobileMenu
          isOpen={mobileMenuOpen}
          onClose={() => setMobileMenuOpen(false)}
          user={user}
          onLogout={logout}
        />
      </nav>

      <main className="flex-1 py-4 sm:py-6">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>

      <Footer />

      {/* Welcome Modal removed - users go directly to dashboard */}
    </div>
  );
};

export default Layout;