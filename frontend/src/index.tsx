import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { 
  registerSW, 
  setupInstallPrompt, 
  setupNetworkStatusTracking,
  setupAppUpdateManagement
} from './utils/sw-registration';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// PWA 기능 설정
if (process.env.NODE_ENV === 'production') {
  // Service Worker 등록
  registerSW({
    onSuccess: () => {
      console.log('[PWA] App is ready for offline use');
    },
    onUpdate: () => {
      console.log('[PWA] New app version available');
      // 사용자에게 업데이트 알림 (향후 토스트 메시지로 구현)
    },
    onOfflineReady: () => {
      console.log('[PWA] App is ready for offline use');
    },
    onError: (error) => {
      console.error('[PWA] Service Worker error:', error);
    }
  });

  // 설치 프롬프트 설정
  setupInstallPrompt({
    onInstallAvailable: () => {
      console.log('[PWA] Install option is available');
    },
    onInstallSuccess: () => {
      console.log('[PWA] App installed successfully');
    }
  });

  // 네트워크 상태 추적
  setupNetworkStatusTracking();
  
  // 앱 업데이트 관리
  setupAppUpdateManagement();
}