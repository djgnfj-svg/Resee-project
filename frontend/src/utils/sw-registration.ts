// Service Worker 등록 및 관리

const isLocalhost = Boolean(
  window.location.hostname === 'localhost' ||
  window.location.hostname === '[::1]' ||
  window.location.hostname.match(
    /^127(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}$/
  )
);

export interface SWRegistrationCallbacks {
  onSuccess?: (registration: ServiceWorkerRegistration) => void;
  onUpdate?: (registration: ServiceWorkerRegistration) => void;
  onOfflineReady?: () => void;
  onError?: (error: Error) => void;
}

export function registerSW(config?: SWRegistrationCallbacks) {
  if ('serviceWorker' in navigator) {
    const publicUrl = new URL(process.env.PUBLIC_URL!, window.location.href);
    if (publicUrl.origin !== window.location.origin) {
      return;
    }

    window.addEventListener('load', () => {
      const swUrl = `${process.env.PUBLIC_URL}/sw.js`;

      if (isLocalhost) {
        checkValidServiceWorker(swUrl, config);
        navigator.serviceWorker.ready.then(() => {
          console.log('[SW] App is being served from cache by a service worker');
          config?.onOfflineReady?.();
        });
      } else {
        registerValidSW(swUrl, config);
      }
    });
  }
}

function registerValidSW(swUrl: string, config?: SWRegistrationCallbacks) {
  navigator.serviceWorker
    .register(swUrl)
    .then(registration => {
      console.log('[SW] Registration successful:', registration);
      
      registration.onupdatefound = () => {
        const installingWorker = registration.installing;
        if (installingWorker == null) return;

        installingWorker.onstatechange = () => {
          if (installingWorker.state === 'installed') {
            if (navigator.serviceWorker.controller) {
              console.log('[SW] New content available; please refresh');
              config?.onUpdate?.(registration);
            } else {
              console.log('[SW] Content cached for offline use');
              config?.onSuccess?.(registration);
            }
          }
        };
      };
    })
    .catch(error => {
      console.error('[SW] Registration failed:', error);
      config?.onError?.(new Error('Service Worker registration failed'));
    });
}

function checkValidServiceWorker(swUrl: string, config?: SWRegistrationCallbacks) {
  fetch(swUrl, {
    headers: { 'Service-Worker': 'script' },
  })
    .then(response => {
      const contentType = response.headers.get('content-type');
      if (
        response.status === 404 ||
        (contentType != null && contentType.indexOf('javascript') === -1)
      ) {
        navigator.serviceWorker.ready.then(registration => {
          registration.unregister().then(() => {
            window.location.reload();
          });
        });
      } else {
        registerValidSW(swUrl, config);
      }
    })
    .catch(() => {
      console.log('[SW] No internet connection. App is running in offline mode');
    });
}

export function unregisterSW() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready
      .then(registration => {
        registration.unregister();
      })
      .catch(error => {
        console.error('[SW] Unregistration error:', error);
      });
  }
}

// PWA 설치 프롬프트 관리
let deferredPrompt: BeforeInstallPromptEvent | null = null;

export interface InstallPromptOptions {
  onInstallAvailable?: () => void;
  onInstallSuccess?: () => void;
  onInstallDeclined?: () => void;
  onInstallError?: (error: Error) => void;
}

// PWA 설치 관련 타입 정의
interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed';
    platform: string;
  }>;
  prompt(): Promise<void>;
}

declare global {
  interface WindowEventMap {
    beforeinstallprompt: BeforeInstallPromptEvent;
  }
}

export function setupInstallPrompt(options?: InstallPromptOptions) {
  window.addEventListener('beforeinstallprompt', (e: BeforeInstallPromptEvent) => {
    console.log('[PWA] Install prompt available');
    e.preventDefault();
    deferredPrompt = e;
    options?.onInstallAvailable?.();
  });

  window.addEventListener('appinstalled', () => {
    console.log('[PWA] App installed successfully');
    deferredPrompt = null;
    options?.onInstallSuccess?.();
  });
}

export async function promptInstall(): Promise<boolean> {
  if (!deferredPrompt) {
    console.log('[PWA] Install prompt not available');
    return false;
  }

  try {
    await deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    
    console.log(`[PWA] Install prompt outcome: ${outcome}`);
    deferredPrompt = null;
    
    return outcome === 'accepted';
  } catch (error) {
    console.error('[PWA] Install prompt error:', error);
    return false;
  }
}

export function isInstallAvailable(): boolean {
  return deferredPrompt !== null;
}

// 네트워크 상태 관리
export function setupNetworkStatusTracking() {
  const updateOnlineStatus = () => {
    const isOnline = navigator.onLine;
    document.body.classList.toggle('offline', !isOnline);
    
    // 커스텀 이벤트 발생
    window.dispatchEvent(new CustomEvent('networkstatus', {
      detail: { isOnline }
    }));
  };

  window.addEventListener('online', updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);
  
  // 초기 상태 설정
  updateOnlineStatus();
}

// 앱 업데이트 관리
export function setupAppUpdateManagement() {
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    console.log('[SW] Controller changed - reloading page');
    window.location.reload();
  });
}