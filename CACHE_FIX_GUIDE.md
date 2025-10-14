# 캐시 문제 해결 가이드

**날짜**: 2025-10-14
**문제**: /content 페이지에서 지속적인 캐시 문제 발생
**해결**: Service Worker API 캐싱 제거

---

## 🔍 문제 원인

### 다중 캐시 레이어 충돌

프로젝트는 3개의 독립적인 캐시 레이어를 사용하고 있었습니다:

1. **Nginx** (서버): API 캐싱 방지 ✅
   ```nginx
   location /api/ {
       add_header Cache-Control "no-cache, no-store, must-revalidate";
   }
   ```

2. **Service Worker** (브라우저): API 캐싱 활성화 ❌
   ```javascript
   const API_PATTERNS = [
     /\/api\/content\/contents\//,  // 콘텐츠 API를 캐싱!
   ];
   ```

3. **React Query** (클라이언트): 스마트 캐시 관리 ✅

### 충돌 시나리오

```
1. 사용자가 새 콘텐츠 생성
   ↓
2. React Query가 캐시 무효화
   ↓
3. API 재요청 발생
   ↓
4. Service Worker가 요청 가로챔
   ↓
5. 오래된 캐시 응답 반환 ❌
   ↓
6. 사용자는 새 콘텐츠를 볼 수 없음
```

**핵심 문제**: Service Worker가 "Stale-While-Revalidate" 전략 사용
- 캐시된 응답을 먼저 반환 (빠름)
- 백그라운드에서 새 데이터 fetch (사용자가 못 봄)

---

## ✅ 해결 방법

### Service Worker API 캐싱 제거

**파일**: `frontend/public/sw.js`

**변경 전** (v3):
```javascript
const CACHE_NAME = 'resee-v3';
const API_PATTERNS = [
  /^https?:\/\/[^\/]+\/api\/content\/contents\//,
  /^https?:\/\/[^\/]+\/api\/review\/today/,
  /^https?:\/\/[^\/]+\/api\/analytics\/dashboard/,
];
```

**변경 후** (v4):
```javascript
const CACHE_NAME = 'resee-v4';  // 버전 업그레이드로 기존 캐시 무효화
const API_PATTERNS = [];  // API 캐싱 완전 제거
```

### 새로운 캐시 전략

| 레이어 | 역할 | 캐싱 대상 |
|--------|------|-----------|
| Nginx | 리버스 프록시 | 정적 파일만 (1년) |
| Service Worker | PWA 오프라인 지원 | 정적 파일만 (JS, CSS, 이미지) |
| React Query | 스마트 상태 관리 | API 응답 (메모리, 무효화 가능) |

---

## 🚀 배포 방법

### 1. 프로덕션 빌드

```bash
cd frontend
npm run build
```

### 2. 배포 스크립트 실행

```bash
./deploy.sh
```

### 3. 사용자 측 업데이트

Service Worker v4가 자동으로 배포됩니다:

```javascript
// sw.js의 install 이벤트에서
self.skipWaiting();  // 즉시 새 버전 활성화

// activate 이벤트에서
caches.keys().then(cacheNames => {
  return Promise.all(
    cacheNames
      .filter(cacheName => cacheName !== 'resee-v4')  // v3 캐시 삭제
      .map(cacheName => caches.delete(cacheName))
  );
});
```

---

## 📊 예상 효과

### Before (v3 - 문제 발생)
```
콘텐츠 생성 → React Query 무효화 → API 요청
   ↓
Service Worker 가로챔 → 캐시 반환 (오래된 데이터)
   ↓
새 콘텐츠 안 보임 ❌
```

### After (v4 - 해결됨)
```
콘텐츠 생성 → React Query 무효화 → API 요청
   ↓
Service Worker 통과 → 네트워크 요청
   ↓
최신 데이터 반환 → 새 콘텐츠 즉시 표시 ✅
```

---

## 🧪 테스트 방법

### 로컬 테스트

```bash
# 1. 프로덕션 빌드
cd frontend
npm run build

# 2. 개발 서버 시작
docker-compose up -d

# 3. 브라우저 개발자 도구 확인
# Application → Service Workers → "resee-v4" 확인
```

### 캐시 확인

```javascript
// 브라우저 콘솔에서
caches.keys().then(console.log);  // ['resee-v4'] 만 표시되어야 함

// API 캐시 확인
caches.open('resee-api-v4').then(cache =>
  cache.keys().then(keys => console.log(keys.length))
);  // 0이어야 함 (API 캐싱 안 함)
```

### 기능 테스트

1. ✅ /content 페이지 접속
2. ✅ 새 콘텐츠 생성
3. ✅ 목록에 즉시 표시됨
4. ✅ 새로고침(F5)해도 유지됨
5. ✅ 콘텐츠 수정 즉시 반영
6. ✅ 콘텐츠 삭제 즉시 반영

---

## 🔧 문제 발생 시

### 기존 사용자의 캐시가 남아있는 경우

**증상**: 배포 후에도 여전히 오래된 데이터 표시

**해결**:
1. Hard Refresh: `Ctrl + Shift + R` (Windows/Linux) 또는 `Cmd + Shift + R` (Mac)
2. Service Worker 수동 갱신:
   ```
   개발자 도구 → Application → Service Workers → Unregister
   ```
3. 캐시 완전 삭제:
   ```
   개발자 도구 → Application → Storage → Clear site data
   ```

### skipWaiting()이 작동하지 않는 경우

Service Worker는 사용자가 탭을 닫았다가 다시 열 때 업데이트됩니다.

**강제 업데이트** (선택):
```javascript
// index.tsx에서
registerSW({
  onUpdate: (registration) => {
    if (confirm('새 버전이 있습니다. 지금 업데이트하시겠습니까?')) {
      registration.waiting?.postMessage({ type: 'SKIP_WAITING' });
      window.location.reload();
    }
  }
});
```

---

## 📈 성능 영향

### 변경 전후 비교

| 항목 | v3 (API 캐싱 O) | v4 (API 캐싱 X) |
|------|------------------|------------------|
| 첫 로드 | 빠름 ⚡ | 동일 |
| 데이터 신선도 | 나쁨 ❌ | 좋음 ✅ |
| 오프라인 지원 | 일부 | 정적 파일만 |
| 캐시 무효화 | 불가능 | React Query 제어 |
| 사용자 경험 | 혼란스러움 | 일관성 있음 |

**결론**: 약간의 네트워크 요청 증가 대신 **데이터 일관성 확보**

---

## 📚 관련 문서

- [React Query - Cache Invalidation](https://tanstack.com/query/latest/docs/react/guides/query-invalidation)
- [Service Worker Best Practices](https://web.dev/service-worker-lifecycle/)
- [MDN - Cache API](https://developer.mozilla.org/en-US/docs/Web/API/Cache)

---

## 🎯 향후 개선 방향

### 옵션 1: Network First with Short Cache

API 응답을 짧은 시간(5초)만 캐싱:

```javascript
const API_PATTERNS = [
  { pattern: /\/api\/content\//, ttl: 5000 }  // 5초 캐시
];
```

### 옵션 2: Background Sync

오프라인 시 생성한 콘텐츠를 자동 동기화:

```javascript
self.addEventListener('sync', event => {
  if (event.tag === 'sync-content') {
    event.waitUntil(syncOfflineContent());
  }
});
```

### 옵션 3: React Query Persistent Cache

React Query 캐시를 IndexedDB에 저장:

```javascript
import { persistQueryClient } from '@tanstack/react-query-persist-client';
import { createSyncStoragePersister } from '@tanstack/query-sync-storage-persister';

const persister = createSyncStoragePersister({
  storage: window.localStorage,
});

persistQueryClient({ queryClient, persister });
```

---

**최종 권장사항**: 현재 v4 (API 캐싱 제거) 솔루션으로 충분합니다. 추가 최적화는 실제 성능 지표를 모니터링한 후 결정하세요.
