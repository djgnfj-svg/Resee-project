import React, { useState, useEffect } from 'react';
import { 
  WifiIcon, 
  SignalSlashIcon,
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline';

interface NetworkStatusProps {
  className?: string;
  showLabel?: boolean;
}

const NetworkStatus: React.FC<NetworkStatusProps> = ({ 
  className = '',
  showLabel = true 
}) => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [showOfflineMessage, setShowOfflineMessage] = useState(false);

  useEffect(() => {
    const handleNetworkChange = (event: CustomEvent<{ isOnline: boolean }>) => {
      const { isOnline: newStatus } = event.detail;
      setIsOnline(newStatus);
      
      // 오프라인이 되었을 때 잠시 메시지 표시
      if (!newStatus) {
        setShowOfflineMessage(true);
        setTimeout(() => setShowOfflineMessage(false), 5000);
      }
    };

    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    // 커스텀 네트워크 상태 이벤트 리스너
    window.addEventListener('networkstatus', handleNetworkChange as EventListener);
    
    // 브라우저 기본 이벤트 리스너 (fallback)
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('networkstatus', handleNetworkChange as EventListener);
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // 온라인 상태에서는 아무것도 표시하지 않음 (옵션)
  if (isOnline && !showOfflineMessage) {
    return null;
  }

  return (
    <>
      {/* 상태 표시기 */}
      <div className={`inline-flex items-center ${className}`}>
        {isOnline ? (
          <WifiIcon className="w-5 h-5 text-green-500" />
        ) : (
          <SignalSlashIcon className="w-5 h-5 text-red-500" />
        )}
        
        {showLabel && (
          <span className={`ml-2 text-sm font-medium ${
            isOnline ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
          }`}>
            {isOnline ? '온라인' : '오프라인'}
          </span>
        )}
      </div>

      {/* 오프라인 알림 배너 */}
      {showOfflineMessage && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-yellow-50 dark:bg-yellow-900 border-b border-yellow-200 dark:border-yellow-700 px-4 py-3">
          <div className="flex items-center justify-center max-w-4xl mx-auto">
            <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-2 flex-shrink-0" />
            <p className="text-sm text-yellow-800 dark:text-yellow-200">
              인터넷 연결이 끊어졌습니다. 일부 기능은 제한될 수 있습니다.
            </p>
          </div>
        </div>
      )}

      {/* 오프라인 모드 스타일 */}
      {!isOnline && (
        <style>
          {`
            body.offline {
              filter: grayscale(0.3);
            }
            body.offline::before {
              content: '';
              position: fixed;
              top: 0;
              left: 0;
              right: 0;
              bottom: 0;
              background: rgba(0, 0, 0, 0.1);
              pointer-events: none;
              z-index: 1;
            }
          `}
        </style>
      )}
    </>
  );
};

export default NetworkStatus;