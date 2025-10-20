# 대시보드 API

## 핵심 개념

**관리자 모니터링 대시보드 API**로 시스템 상태를 실시간으로 확인할 수 있습니다.
헬스 체크, 디스크 용량, 로그 정보를 한 번의 API 호출로 가져옵니다.

## 주요 기능

- **통합 모니터링 데이터**:
  - 시스템 헬스 상태
  - 데이터베이스 연결 상태
  - 디스크 사용량
  - 로그 파일 통계
- **성능 메트릭**:
  - API 응답 시간 측정
  - 타임스탬프 제공
- **환경 정보**:
  - development/production 구분
  - DEBUG 모드 여부

## 동작 흐름

```
1. GET /api/accounts/dashboard-data/ 호출
   ↓
2. 데이터베이스 연결 확인 (SELECT 1)
   ↓
3. 디스크 사용량 계산
   ↓
4. 로그 파일 크기 집계
   ↓
5. 통합 응답 반환 (JSON)
```

## API

- `GET /api/accounts/dashboard-data/` - 통합 대시보드 데이터

## 응답 예시

```json
{
  "health": {
    "status": "healthy",
    "timestamp": 1729411200,
    "database": "healthy",
    "disk_usage_percent": 65.32,
    "disk_free_gb": 120.5
  },
  "logs": {
    "total_files": 8,
    "total_size_mb": 12.45
  },
  "environment": "production",
  "response_time_ms": 15.23
}
```

## 상태 값

**헬스 상태**:
- `healthy`: 모든 시스템 정상
- `degraded`: 일부 시스템 문제 (예: DB 연결 실패)
- `unhealthy`: 심각한 문제 발생

**데이터베이스 상태**:
- `healthy`: 연결 정상
- `unhealthy`: 연결 실패

## 관련 파일

- `backend/accounts/health/monitoring_views.py` - 대시보드 API

## 권한

- **개발 환경**: 인증 불필요 (AllowAny)
- **프로덕션**: 관리자(is_staff) 권한 필요

```python
if not settings.DEBUG and not request.user.is_staff:
    return Response({'error': 'Permission denied'}, status=403)
```

## 디스크 사용량 계산

```python
import shutil

disk_usage = shutil.disk_usage('/')
usage_percent = ((disk_usage.total - disk_usage.free) / disk_usage.total) * 100
free_gb = disk_usage.free / (1024**3)
```

## 로그 파일 집계

```python
import os
import glob

log_dir = os.path.join(settings.BASE_DIR, 'logs')
log_files = []
for ext in ['*.log', '*.log.*']:
    log_files.extend(glob.glob(os.path.join(log_dir, ext)))

total_size = sum(os.path.getsize(f) for f in log_files)
total_size_mb = total_size / (1024 * 1024)
```

## 사용 예시

**프론트엔드에서 호출**:
```typescript
import { api } from '@/utils/api';

interface DashboardData {
  health: {
    status: string;
    timestamp: number;
    database: string;
    disk_usage_percent: number;
    disk_free_gb: number;
  };
  logs: {
    total_files: number;
    total_size_mb: number;
  };
  environment: string;
  response_time_ms: number;
}

async function fetchDashboardData(): Promise<DashboardData> {
  const response = await api.get('/accounts/dashboard-data/');
  return response.data;
}

// React Query 사용
const { data } = useQuery('dashboardData', fetchDashboardData, {
  refetchInterval: 30000  // 30초마다 갱신
});
```

## 모니터링 대시보드 활용

1. **실시간 모니터링**: 30초 간격으로 자동 갱신
2. **알림 트리거**: 디스크 사용량 80% 초과 시 알림
3. **로그 크기 관리**: 로그 파일이 너무 커지면 로테이션
4. **헬스 체크**: DB 연결 실패 시 즉시 감지

## 확장 가능성

다음 메트릭을 추가할 수 있습니다:
- Redis 연결 상태
- Celery 큐 길이
- 활성 사용자 수
- API 요청 통계
- 메모리 사용량
- CPU 사용률
