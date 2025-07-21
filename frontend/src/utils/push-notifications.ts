// 푸시 알림 관리

export interface NotificationPermission {
  permission: 'granted' | 'denied' | 'default';
  subscription: PushSubscription | null;
}

export interface NotificationConfig {
  title: string;
  body: string;
  icon?: string;
  badge?: string;
  tag?: string;
  data?: any;
  actions?: NotificationAction[];
  requireInteraction?: boolean;
}

export interface ReviewNotificationData {
  type: 'review_reminder';
  reviewCount: number;
  url: string;
}

// 알림 권한 요청
export async function requestNotificationPermission(): Promise<NotificationPermission> {
  if (!('Notification' in window)) {
    throw new Error('이 브라우저는 알림을 지원하지 않습니다.');
  }

  if (!('serviceWorker' in navigator)) {
    throw new Error('이 브라우저는 Service Worker를 지원하지 않습니다.');
  }

  const permission = await Notification.requestPermission();
  let subscription: PushSubscription | null = null;

  if (permission === 'granted') {
    try {
      const registration = await navigator.serviceWorker.ready;
      subscription = await registration.pushManager.getSubscription();

      if (!subscription) {
        // VAPID 키는 백엔드에서 제공되어야 함
        const vapidKey = process.env.REACT_APP_VAPID_PUBLIC_KEY;
        if (vapidKey) {
          subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlB64ToUint8Array(vapidKey),
          });
        }
      }
    } catch (error) {
      console.error('[Push] Subscription failed:', error);
    }
  }

  return { permission, subscription };
}

// 현재 알림 상태 확인
export async function getNotificationStatus(): Promise<NotificationPermission> {
  const permission = Notification.permission;
  let subscription: PushSubscription | null = null;

  if (permission === 'granted' && 'serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.ready;
      subscription = await registration.pushManager.getSubscription();
    } catch (error) {
      console.error('[Push] Failed to get subscription:', error);
    }
  }

  return { permission, subscription };
}

// 로컬 알림 표시 (즉시)
export function showLocalNotification(config: NotificationConfig): Notification | null {
  if (Notification.permission !== 'granted') {
    return null;
  }

  const notification = new Notification(config.title, {
    body: config.body,
    icon: config.icon || '/icons/icon-192x192.png',
    badge: config.badge || '/icons/icon-72x72.png',
    tag: config.tag,
    data: config.data,
    requireInteraction: config.requireInteraction,
  });

  // 클릭 이벤트 처리
  notification.onclick = () => {
    window.focus();
    notification.close();
    
    // 특정 페이지로 이동
    if (config.data?.url) {
      window.location.href = config.data.url;
    }
  };

  return notification;
}

// 복습 알림 표시
export function showReviewNotification(reviewCount: number): Notification | null {
  return showLocalNotification({
    title: '📚 복습 시간입니다!',
    body: `${reviewCount}개의 콘텐츠가 복습을 기다리고 있습니다.`,
    tag: 'review_reminder',
    data: {
      type: 'review_reminder',
      reviewCount,
      url: '/review'
    },
    requireInteraction: true,
    actions: [
      {
        action: 'review',
        title: '복습 시작',
        icon: '/icons/shortcut-review.png'
      },
      {
        action: 'later',
        title: '나중에',
        icon: '/icons/close.png'
      }
    ]
  });
}

// 푸시 구독을 서버에 저장
export async function subscribeToServerPush(subscription: PushSubscription): Promise<boolean> {
  try {
    const response = await fetch('/api/notifications/subscribe/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({
        subscription: subscription.toJSON(),
        user_agent: navigator.userAgent,
        endpoint: subscription.endpoint
      })
    });

    if (!response.ok) {
      throw new Error(`Server subscription failed: ${response.status}`);
    }

    console.log('[Push] Successfully subscribed to server');
    return true;
  } catch (error) {
    console.error('[Push] Failed to subscribe to server:', error);
    return false;
  }
}

// 푸시 구독 해제
export async function unsubscribeFromPush(): Promise<boolean> {
  try {
    if (!('serviceWorker' in navigator)) {
      return false;
    }

    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();

    if (subscription) {
      // 서버에서 구독 해제
      await fetch('/api/notifications/unsubscribe/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          endpoint: subscription.endpoint
        })
      });

      // 브라우저에서 구독 해제
      await subscription.unsubscribe();
      console.log('[Push] Successfully unsubscribed');
      return true;
    }

    return false;
  } catch (error) {
    console.error('[Push] Failed to unsubscribe:', error);
    return false;
  }
}

// 알림 설정 관리
export interface NotificationSettings {
  enabled: boolean;
  reviewReminders: boolean;
  dailyGoalReminders: boolean;
  streakReminders: boolean;
  quietHours: {
    enabled: boolean;
    start: string; // "22:00"
    end: string;   // "08:00"
  };
}

export function getNotificationSettings(): NotificationSettings {
  const saved = localStorage.getItem('notification_settings');
  if (saved) {
    try {
      return JSON.parse(saved);
    } catch (error) {
      console.error('[Push] Failed to parse notification settings:', error);
    }
  }

  // 기본 설정
  return {
    enabled: true,
    reviewReminders: true,
    dailyGoalReminders: true,
    streakReminders: true,
    quietHours: {
      enabled: true,
      start: '22:00',
      end: '08:00'
    }
  };
}

export function saveNotificationSettings(settings: NotificationSettings): void {
  localStorage.setItem('notification_settings', JSON.stringify(settings));
}

// 조용한 시간 확인
export function isQuietHours(settings?: NotificationSettings): boolean {
  const config = settings || getNotificationSettings();
  
  if (!config.quietHours.enabled) {
    return false;
  }

  const now = new Date();
  const currentTime = now.getHours() * 60 + now.getMinutes();
  
  const [startHour, startMin] = config.quietHours.start.split(':').map(Number);
  const [endHour, endMin] = config.quietHours.end.split(':').map(Number);
  
  const startTime = startHour * 60 + startMin;
  const endTime = endHour * 60 + endMin;

  if (startTime <= endTime) {
    return currentTime >= startTime && currentTime < endTime;
  } else {
    // 자정을 넘는 경우 (예: 22:00 ~ 08:00)
    return currentTime >= startTime || currentTime < endTime;
  }
}

// 유틸리티 함수들
function urlB64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  
  return outputArray;
}

// 브라우저 지원 여부 확인
export function isNotificationSupported(): boolean {
  return 'Notification' in window && 'serviceWorker' in navigator && 'PushManager' in window;
}

// Note: Test notification function removed for production