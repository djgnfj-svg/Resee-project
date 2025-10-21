# Celery 시작 순서 문제 해결 회고

> 2025년 10월, Docker Compose depends_on의 함정

## 개요

- **문제 발견**: 2025년 10월 (배포 테스트 중)
- **해결 완료**: 2025년 10월 (2시간 소요)
- **원인**: depends_on이 "시작 순서"만 보장하지, "준비 완료"는 보장하지 않음

---

## 문제 발견

`docker-compose up`을 실행했는데 Celery가 계속 에러를 발생시켰다.

```bash
$ docker-compose logs celery

celery_1  | relation "review_reviewschedule" does not exist
celery_1  | django.db.utils.ProgrammingError: ...
```

분명히 마이그레이션은 실행됐는데 테이블이 없다는 에러였다.

문제는 **타이밍**이었다.

---

## 원인 분석

### 초기 docker-compose.yml

```yaml
services:
  backend:
    command: python manage.py runserver
    depends_on:
      - postgres

  celery:
    command: celery -A resee worker
    depends_on:
      - backend  # 이것만으로는 부족
      - redis
```

### 실제로 일어난 일

```
00:00  Postgres 시작
00:01  Backend 시작 (마이그레이션 시작)
00:02  Celery 시작 (테이블 없음) ← 에러 발생
00:03  Backend 마이그레이션 완료
00:04  Backend 서버 시작
```

**depends_on의 함정**:
- "backend 컨테이너가 시작된 후"를 의미
- "backend가 준비 완료된 후"가 아님

Celery가 시작되는 시점에는 마이그레이션이 아직 진행 중이었다.

---

## 해결 과정

### 1단계: Healthcheck 이해하기

Docker Compose의 `healthcheck`는 컨테이너가 **실제로 동작하는지** 확인한다.

```yaml
healthcheck:
  test: ["CMD", "curl", "http://localhost:8000/api/health/"]
  interval: 10s   # 10초마다 확인
  timeout: 5s     # 5초 안에 응답 없으면 실패
  retries: 5      # 5번 실패하면 unhealthy
```

**상태 전이**:
```
starting → healthy (test 통과)
starting → unhealthy (test 5번 실패)
```

### 2단계: Health API 엔드포인트 추가

```python
# backend/accounts/health/health_views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """간단한 헬스체크

    마이그레이션 완료 + 서버 시작 = healthy
    """
    try:
        # DB 연결 확인 (마이그레이션 완료 여부)
        connection.ensure_connection()
        return JsonResponse({'status': 'healthy'})
    except Exception as e:
        return JsonResponse(
            {'status': 'unhealthy', 'error': str(e)},
            status=500
        )
```

### 3단계: Backend에 Healthcheck 추가

```yaml
# docker-compose.yml (수정)
services:
  backend:
    entrypoint: /app/docker-entrypoint.sh
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/"]
      interval: 10s
      timeout: 5s
      retries: 5
    depends_on:
      postgres:
        condition: service_healthy
```

### 4단계: Celery에서 Backend healthy 대기

```yaml
celery:
    command: celery -A resee worker
    healthcheck:
      disable: true  # Celery는 웹 서버 아님
    depends_on:
      backend:
        condition: service_healthy  # healthy 상태까지 대기
      redis:
        condition: service_healthy
```

### 5단계: Entrypoint 스크립트 작성

마이그레이션을 서버 시작 전에 실행하도록 보장.

```bash
#!/bin/bash
# backend/docker-entrypoint.sh

set -e  # 에러 발생 시 즉시 중단

echo "Waiting for database..."
while ! nc -z postgres 5432; do
  sleep 0.1
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8000
```

```bash
chmod +x backend/docker-entrypoint.sh
```

---

## 개선된 시작 순서

### Before
```
00:00  Postgres 시작
00:01  Backend 시작
00:02  Celery 시작 ← 에러! 테이블 없음
00:03  Backend 마이그레이션 완료
```

### After
```
00:00  Postgres 시작
00:01  Postgres healthy
00:02  Backend 시작 → 마이그레이션 실행
00:05  Backend 마이그레이션 완료 → 서버 시작
00:06  Backend healthy
00:07  Celery 시작 (테이블 있음)
```

---

## 배운 점

### 1. depends_on의 3가지 옵션

```yaml
# 1. 기본 (컨테이너 시작만 보장)
depends_on:
  - backend

# 2. service_started (명시적, 1과 같음)
depends_on:
  backend:
    condition: service_started

# 3. service_healthy (추천)
depends_on:
  backend:
    condition: service_healthy
```

실무에서는 무조건 3번 써야 한다.

### 2. Celery는 Healthcheck 비활성화

초기에 이런 실수를 했다:

```yaml
celery:
  healthcheck:
    test: ["CMD", "curl", "http://localhost:8000/api/health/"]
    # Celery는 웹 서버가 아님! 8000 포트 없음
```

에러 로그:
```
curl: (7) Failed to connect to localhost port 8000
```

**교훈**: 백그라운드 워커는 healthcheck 비활성화하거나, 별도 모니터링 방법 사용.

### 3. Entrypoint vs Command

```yaml
# Entrypoint: 초기화 작업 (마이그레이션 등)
entrypoint: /app/docker-entrypoint.sh

# Command: 메인 프로세스 (서버 시작)
# command: python manage.py runserver  # entrypoint에서 처리
```

Entrypoint에서 `exec`로 command 실행하면 PID 1 유지됨.

### 4. Celery 상태 모니터링

```python
# backend/accounts/health/health_views.py
def detailed_health_check(request):
    """Celery 포함 전체 상태 확인"""
    status = {}

    # Celery worker 확인
    try:
        from resee.celery import app
        stats = app.control.inspect().stats()
        status['celery'] = 'healthy' if stats else 'no workers'
    except Exception as e:
        status['celery'] = f'unhealthy: {str(e)}'

    return JsonResponse({'services': status})
```

---

## 체크리스트

Docker Compose 설정 시:

- [ ] 웹/API 서버: healthcheck 설정
- [ ] 백그라운드 워커: healthcheck 비활성화
- [ ] `condition: service_healthy` 사용
- [ ] Entrypoint로 초기화 순서 보장
- [ ] 로그로 시작 순서 검증

---

## 관련 코드

- Docker Compose: `docker-compose.yml`
- Entrypoint: `backend/docker-entrypoint.sh`
- Health API: `backend/accounts/health/health_views.py`
- 커밋: `7772eec`, `24f4d5b`

---

## 참고한 자료

- [Docker Compose: depends_on](https://docs.docker.com/compose/compose-file/compose-file-v3/#depends_on)
- [Docker Compose: healthcheck](https://docs.docker.com/compose/compose-file/compose-file-v3/#healthcheck)

---

## 정리

Docker Compose의 depends_on은 생각보다 단순하다.
컨테이너가 시작됐다고 준비된 것이 아니다.

**Healthcheck를 쓰면**:
- 서비스 시작 순서 보장
- 배포 안정성 향상
- 디버깅 시간 절약

앞으로 Docker 쓸 때는 무조건 healthcheck 먼저 설정할 것이다.

**다음에 적용할 점**:
- 새 서비스 추가 시 healthcheck 먼저 생각
- condition: service_healthy가 기본
- 로그로 시작 순서 확인하는 습관
