const CACHE_NAME = 'resee-v5';
const API_CACHE_NAME = 'resee-api-v5';

// 캐시할 정적 자원들
// 주의: HTML 파일(/)은 캐싱하지 않음 - 항상 최신 bundle 참조를 위해
const STATIC_ASSETS = [
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png'
];

// API 캐싱 비활성화 - React Query가 캐시 관리를 전담
// Service Worker는 정적 파일(JS, CSS, 이미지)만 캐싱
const API_PATTERNS = [];

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

  // HTML 파일은 항상 네트워크에서 가져오기 (캐싱 방지)
  if (request.destination === 'document' || url.pathname.endsWith('.html')) {
    event.respondWith(
      fetch(request)
        .catch(() => {
          // 오프라인 시 기본 폴백 (캐시에서 가져오기)
          return caches.match('/offline.html').then(cachedResponse => {
            if (cachedResponse) return cachedResponse;
            // offline.html도 없으면 최소한의 HTML 응답
            return new Response(
              '<html><body><h1>Offline</h1><p>인터넷 연결을 확인해주세요.</p></body></html>',
              { headers: { 'Content-Type': 'text/html' } }
            );
          });
        })
    );
    return;
  }

  // 정적 자원 처리 (Cache-first)
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
            // 정적 자원 로딩 실패 시 아무것도 하지 않음
            return new Response('Resource not available', { status: 404 });
          });
      })
  );
});

// API 요청인지 확인
function isApiRequest(url) {
  return API_PATTERNS.some(pattern => pattern.test(url));
}

// 인증이 필요한 API 패턴 확인
function requiresAuth(url) {
  const authRequiredPatterns = [
    /\/api\/contents\//,
    /\/api\/categories\//,
    /\/api\/review\//,
    /\/api\/analytics\//,
    /\/api\/accounts\/profile\//
  ];
  return authRequiredPatterns.some(pattern => pattern.test(url));
}

// API 요청 처리 (인증 API는 Network First, 기타는 Cache First)
async function handleApiRequest(request) {
  const cache = await caches.open(API_CACHE_NAME);
  const needsAuth = requiresAuth(request.url);

  try {
    if (needsAuth) {
      // 인증이 필요한 API: Network First 전략
      const response = await fetch(request);

      // 성공적인 GET 요청만 캐시에 저장
      if (request.method === 'GET' && response.status === 200) {
        cache.put(request, response.clone());
      }

      return response;

    } else {
      // 기타 API: Cache First 전략
      const cachedResponse = await cache.match(request);

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

      if (request.method === 'GET' && response.status === 200) {
        cache.put(request, response.clone());
      }

      return response;
    }

  } catch (error) {
    // 네트워크 오류 시 캐시에서 반환 (GET 요청만)
    if (request.method === 'GET') {
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

// 캐시 무효화 함수
async function invalidateContentCache() {
  try {
    const cache = await caches.open(API_CACHE_NAME);
    const cacheKeys = await cache.keys();

    // 콘텐츠 관련 캐시 삭제
    const contentCacheKeys = cacheKeys.filter(request =>
      request.url.includes('/api/contents/') ||
      request.url.includes('/api/categories/')
    );

    await Promise.all(contentCacheKeys.map(request => cache.delete(request)));
    console.log('[SW] Content cache invalidated');
  } catch (error) {
    console.error('[SW] Failed to invalidate cache:', error);
  }
}

// 메시지 리스너 (콘텐츠 생성 시 캐시 무효화)
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'INVALIDATE_CONTENT_CACHE') {
    invalidateContentCache();
  }
});