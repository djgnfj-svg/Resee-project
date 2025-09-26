const CACHE_NAME = 'resee-v2';
const API_CACHE_NAME = 'resee-api-v2';

// 캐시할 정적 자원들
const STATIC_ASSETS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png'
];

// 캐시할 API 엔드포인트 패턴
const API_PATTERNS = [
  /^https?:\/\/[^\/]+\/api\/content\/contents\//,
  /^https?:\/\/[^\/]+\/api\/review\/today/,
  /^https?:\/\/[^\/]+\/api\/analytics\/dashboard/,
];

// Service Worker 설치
self.addEventListener('install', event => {
  console.log('[SW] Installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .catch(err => {
        console.error('[SW] Failed to cache static assets:', err);
      })
  );
  
  // 새 Service Worker가 즉시 활성화되도록 강제
  self.skipWaiting();
});

// Service Worker 활성화
self.addEventListener('activate', event => {
  console.log('[SW] Activating...');
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames
          .filter(cacheName => cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME)
          .map(cacheName => {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          })
      );
    })
  );
  
  // 즉시 모든 탭을 제어하도록 설정
  self.clients.claim();
});

// Fetch 이벤트 처리
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // API 요청 처리
  if (isApiRequest(request.url)) {
    event.respondWith(handleApiRequest(request));
    return;
  }
  
  // 정적 자원 처리
  event.respondWith(
    caches.match(request)
      .then(response => {
        // 캐시에 있으면 반환
        if (response) {
          return response;
        }
        
        // 네트워크에서 가져오기
        return fetch(request)
          .then(response => {
            // 유효한 응답이 아니면 그대로 반환
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // 응답을 복제하여 캐시에 저장
            const responseToCache = response.clone();
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(request, responseToCache);
              });
            
            return response;
          })
          .catch(() => {
            // 오프라인일 때 기본 페이지 반환
            if (request.destination === 'document') {
              return caches.match('/');
            }
          });
      })
  );
});

// API 요청인지 확인
function isApiRequest(url) {
  return API_PATTERNS.some(pattern => pattern.test(url));
}

// API 요청 처리 (Cache First 전략)
async function handleApiRequest(request) {
  try {
    // 먼저 캐시에서 찾기
    const cache = await caches.open(API_CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    // GET 요청이고 캐시에 있으면 반환
    if (request.method === 'GET' && cachedResponse) {
      // 백그라운드에서 업데이트
      fetch(request)
        .then(response => {
          if (response.status === 200) {
            cache.put(request, response.clone());
          }
        })
        .catch(() => {/* 백그라운드 업데이트 실패 무시 */});
      
      return cachedResponse;
    }
    
    // 네트워크에서 가져오기
    const response = await fetch(request);
    
    // GET 요청의 성공 응답은 캐시에 저장
    if (request.method === 'GET' && response.status === 200) {
      cache.put(request, response.clone());
    }
    
    return response;
    
  } catch (error) {
    // 네트워크 오류 시 캐시에서 반환
    if (request.method === 'GET') {
      const cache = await caches.open(API_CACHE_NAME);
      const cachedResponse = await cache.match(request);
      if (cachedResponse) {
        return cachedResponse;
      }
    }
    
    // 오프라인 에러 응답
    return new Response(
      JSON.stringify({
        error: 'Network unavailable',
        message: '네트워크 연결을 확인해 주세요.',
        offline: true
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

// 백그라운드 동기화 (Future enhancement)
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync') {
    event.waitUntil(syncPendingData());
  }
});

// 푸시 알림 처리 (Future enhancement)
self.addEventListener('push', event => {
  if (!event.data) return;
  
  const data = event.data.json();
  
  const options = {
    body: data.body,
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    vibrate: [200, 100, 200],
    data: {
      url: data.url || '/'
    },
    actions: [
      {
        action: 'open',
        title: '학습 시작',
        icon: '/icons/shortcut-review.png'
      },
      {
        action: 'close',
        title: '나중에',
        icon: '/icons/close.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// 알림 클릭 처리
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  if (event.action === 'open') {
    event.waitUntil(
      clients.openWindow(event.notification.data.url)
    );
  }
});

// 미래 개선사항: 백그라운드 동기화 함수
async function syncPendingData() {
  // 오프라인 상태에서 생성된 데이터를 서버와 동기화
  console.log('[SW] Background sync triggered');
}