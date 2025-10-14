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
import { logger } from './utils/logger';

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
      logger.log('[PWA] App is ready for offline use');
    },
    onUpdate: () => {
      logger.log('[PWA] New app version available');
    },
    onOfflineReady: () => {
      logger.log('[PWA] App is ready for offline use');
    },
    onError: (error) => {
      logger.error('[PWA] Service Worker error:', error);
    }
  });

  // 설치 프롬프트 설정
  setupInstallPrompt({
    onInstallAvailable: () => {
      logger.log('[PWA] Install option is available');
    },
    onInstallSuccess: () => {
      logger.log('[PWA] App installed successfully');
    }
  });

  // 네트워크 상태 추적
  setupNetworkStatusTracking();
  
  // 앱 업데이트 관리
  setupAppUpdateManagement();
}