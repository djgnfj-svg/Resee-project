import React, { useState, useEffect } from 'react';
import { isInstallAvailable, promptInstall } from '../utils/sw-registration';
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';

interface PWAInstallButtonProps {
  className?: string;
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
}

const PWAInstallButton: React.FC<PWAInstallButtonProps> = ({
  className = '',
  variant = 'primary',
  size = 'md'
}) => {
  const [canInstall, setCanInstall] = useState(false);
  const [isInstalling, setIsInstalling] = useState(false);

  useEffect(() => {
    // 초기 상태 체크
    setCanInstall(isInstallAvailable());

    // beforeinstallprompt 이벤트 리스너
    const handleInstallPrompt = () => {
      setCanInstall(true);
    };

    // appinstalled 이벤트 리스너
    const handleAppInstalled = () => {
      setCanInstall(false);
      setIsInstalling(false);
    };

    window.addEventListener('beforeinstallprompt', handleInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const handleInstallClick = async () => {
    if (!canInstall || isInstalling) return;

    setIsInstalling(true);
    try {
      const installed = await promptInstall();
      if (installed) {
        setCanInstall(false);
      }
    } catch (error) {
      console.error('[PWA] Install failed:', error);
    } finally {
      setIsInstalling(false);
    }
  };

  // 설치 불가능한 상태면 렌더링하지 않음
  if (!canInstall) return null;

  const getVariantClasses = () => {
    switch (variant) {
      case 'primary':
        return 'bg-primary-600 hover:bg-primary-700 text-white border-transparent';
      case 'secondary':
        return 'bg-white hover:bg-gray-50 text-gray-900 border-gray-300 dark:bg-gray-800 dark:hover:bg-gray-700 dark:text-gray-100 dark:border-gray-600';
      case 'ghost':
        return 'bg-transparent hover:bg-gray-100 text-gray-700 border-transparent dark:hover:bg-gray-800 dark:text-gray-300';
      default:
        return 'bg-primary-600 hover:bg-primary-700 text-white border-transparent';
    }
  };

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'px-3 py-1.5 text-sm';
      case 'md':
        return 'px-4 py-2 text-sm';
      case 'lg':
        return 'px-6 py-3 text-base';
      default:
        return 'px-4 py-2 text-sm';
    }
  };

  return (
    <button
      onClick={handleInstallClick}
      disabled={isInstalling}
      className={`
        inline-flex items-center justify-center
        font-medium rounded-md border
        transition-colors duration-200
        disabled:opacity-50 disabled:cursor-not-allowed
        focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500
        ${getVariantClasses()}
        ${getSizeClasses()}
        ${className}
      `}
      title="앱을 기기에 설치하기"
    >
      <ArrowDownTrayIcon className={`${size === 'sm' ? 'w-4 h-4' : 'w-5 h-5'} ${size !== 'sm' ? 'mr-2' : ''}`} />
      {size !== 'sm' && (
        <span>{isInstalling ? '설치 중...' : '앱 설치'}</span>
      )}
    </button>
  );
};

export default PWAInstallButton;