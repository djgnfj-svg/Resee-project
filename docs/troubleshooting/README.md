# 트러블슈팅 가이드

> Resee 프로젝트에서 발생했던 실제 문제와 해결 과정

## 이 문서에 대하여

이 트러블슈팅 가이드는 **신입 백엔드 개발자**를 위해 작성되었습니다.

실제 프로젝트에서 발생했던 문제들을 다루며, 각 문서는 다음과 같은 구조로 되어 있습니다:

```
1. 문제 상황 (에러 메시지, 증상)
2. 원인 분석 (왜 발생했나?)
3. 해결 방법 (단계별 코드)
4. 테스트 및 검증
5. 배운 점 정리
```

---

## 난이도별 가이드

### 초급

**Django/Python 기본 개념 이해**

- [02. 데이터베이스 NULL 제약 조건 에러](./02-데이터베이스-null-제약조건.md)
  - `blank=True` vs `null=True` 차이
  - IntegrityError 해결
  - 마이그레이션 생성 및 적용

### 중급

**성능 최적화와 인프라 관리**

- [01. N+1 쿼리 최적화](./01-n+1-쿼리-최적화.md)
  - `select_related()` vs `prefetch_related()` 사용법
  - Mixin 패턴으로 코드 재사용
  - 쿼리 개수 301개 → 3개 (99% 감소)

- [04. Celery 시작 순서 문제](./04-celery-시작-순서.md)
  - Docker Compose `depends_on` vs `condition: service_healthy`
  - Healthcheck 설정 및 활용
  - Entrypoint 스크립트로 초기화 순서 제어

### 고급

**보안과 고급 최적화**

- [03. 이메일 인증 토큰 보안 취약점](./03-이메일-토큰-보안.md)
  - SHA-256 해싱으로 토큰 보호
  - Timing attack 방어 (Constant-time 비교)
  - `secrets` 모듈로 안전한 토큰 생성

---

## 카테고리별 가이드

### 성능 최적화

1. **[N+1 쿼리 최적화](./01-n+1-쿼리-최적화.md)** (중급)
   - **문제**: API 응답 시간 500ms, 301개 쿼리 실행
   - **해결**: `select_related()` + Mixin 패턴
   - **결과**: 응답 시간 50ms (90% 개선), 3개 쿼리 (99% 감소)
   - **적용**: ReviewSchedule, ReviewHistory, Content ViewSet

### 데이터베이스

2. **[NULL 제약 조건 에러](./02-데이터베이스-null-제약조건.md)** (초급)
   - **문제**: `IntegrityError: NOT NULL constraint failed`
   - **해결**: `null=True` 추가 및 마이그레이션
   - **핵심**: `blank=True` (Form) vs `null=True` (DB) 차이
   - **모델**: ReviewHistory

### 보안

3. **[이메일 토큰 보안](./03-이메일-토큰-보안.md)** (고급)
   - **문제**: 평문 토큰 저장으로 인한 계정 탈취 위험
   - **해결**: SHA-256 해싱 + Constant-time 비교
   - **추가**: Timing attack 방어, 만료 시간, 일회용 토큰
   - **모델**: User (email_verification_token)

### 인프라/DevOps

4. **[Celery 시작 순서](./04-celery-시작-순서.md)** (중급)
   - **문제**: Celery가 마이그레이션 전에 시작되어 테이블 없음 에러
   - **해결**: `condition: service_healthy` + Healthcheck
   - **추가**: Entrypoint 스크립트, 백그라운드 워커 모니터링
   - **파일**: docker-compose.yml

---

## 우선순위: 어떤 순서로 읽을까요?

### 신입 백엔드 개발자라면

**1단계: 필수 (면접 단골 질문)**

1. [N+1 쿼리 최적화](./01-n+1-쿼리-최적화.md) - 가장 중요
   - 실무에서 가장 흔한 성능 문제
   - 면접에서 자주 물어보는 주제
   - 측정 가능한 성과 (99% 쿼리 감소)

**2단계: 추천 (보안 감각 어필)**

2. [이메일 토큰 보안](./03-이메일-토큰-보안.md)
   - 보안 의식 보여주기
   - 실제 해킹 시나리오 이해
   - 암호학 기초 (해시, Constant-time 비교)

**3단계: 기본 (Django 이해도)**

3. [데이터베이스 NULL 제약 조건](./02-데이터베이스-null-제약조건.md)
   - Django ORM 기본 개념
   - 마이그레이션 실습
   - 빠르게 읽을 수 있음 (5분)

**4단계: 선택 (인프라 경험)**

4. [Celery 시작 순서](./04-celery-시작-순서.md)
   - Docker/Celery 경험 어필
   - 실무 배포 경험

---

## 트러블슈팅 통계

### 문제 유형 분석

| 카테고리 | 문서 수 | 평균 난이도 | 예상 학습 시간 |
|----------|---------|-------------|----------------|
| 성능 최적화 | 1 | 중급 | 10분 |
| 데이터베이스 | 1 | 초급 | 5분 |
| 보안 | 1 | 고급 | 15분 |
| 인프라 | 1 | 중급 | 8분 |
| **전체** | **4** | **중급** | **38분** |

### 성능 개선 효과

| 문제 | Before | After | 개선율 |
|------|--------|-------|--------|
| N+1 쿼리 | 301개 쿼리 | 3개 쿼리 | 99% 감소 |
| API 응답 | 500ms | 50ms | 90% 개선 |
| Celery 이메일 | 3001개 쿼리 | 4개 쿼리 | 99.9% 감소 |

---

## 실습 가이드

### 환경 설정

```bash
# 프로젝트 클론
git clone https://github.com/your-repo/Resee-project.git
cd Resee-project

# Docker 환경 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f backend
```

### N+1 쿼리 직접 확인해보기

```bash
# Django Shell 접속
docker-compose exec backend python manage.py shell_plus

# 쿼리 개수 확인
from django.db import connection
from review.models import ReviewSchedule

# Before: N+1 쿼리
initial = len(connection.queries)
schedules = ReviewSchedule.objects.filter(user_id=1)[:10]
for s in schedules:
    print(s.content.title)
print(f"쿼리 개수: {len(connection.queries) - initial}")

# After: 최적화
connection.queries.clear()
initial = len(connection.queries)
schedules = ReviewSchedule.objects.filter(user_id=1).select_related(
    'content', 'content__category', 'user'
)[:10]
for s in schedules:
    print(s.content.title)
print(f"쿼리 개수: {len(connection.queries) - initial}")
```

### 테스트 실행

```bash
# 전체 테스트
docker-compose exec backend python -m pytest

# 보안 테스트만
docker-compose exec backend python -m pytest backend/accounts/tests/test_security.py

# Coverage 확인
docker-compose exec backend python -m pytest --cov=. --cov-report=html
```

---

## 각 문서의 구성

### 공통 섹션

1. **개요**
   - 문제 발견 시점
   - 해결 완료 시점
   - 주요 성과

2. **문제 발견**
   - 실제 에러 메시지
   - 발생 증상

3. **원인 분석**
   - 왜 발생했는지 상세 설명
   - 근본 원인 파악

4. **해결 과정**
   - 단계별 코드와 설명
   - 파일 위치 명시

5. **배운 점**
   - 핵심 개념 요약
   - 체크리스트

6. **참고 자료**
   - 공식 문서 링크
   - 실제 커밋 정보

---

## 학습 팁

### 효과적으로 읽는 방법

1. **문제 상황부터 읽기**
   - 에러 메시지가 익숙한가?
   - 비슷한 경험이 있었나?

2. **코드 직접 실행해보기**
   - Before 코드 실행 → 문제 재현
   - After 코드 실행 → 해결 확인

3. **자신의 프로젝트에 적용하기**
   - 비슷한 패턴 찾기
   - 예방적 수정하기

### 면접 대비

각 문서의 **"배운 점"** 섹션에는 면접에서 답변할 핵심 내용이 정리되어 있습니다.

**예상 질문**:

- "N+1 쿼리 문제를 해결한 경험이 있나요?"
  → [01. N+1 쿼리 최적화](./01-n+1-쿼리-최적화.md) 읽기

- "보안 취약점을 발견하고 해결한 경험이 있나요?"
  → [03. 이메일 토큰 보안](./03-이메일-토큰-보안.md) 읽기

- "Docker 환경에서 서비스 간 의존성을 어떻게 관리하나요?"
  → [04. Celery 시작 순서](./04-celery-시작-순서.md) 읽기

---

## 관련 문서

- [CLAUDE.md](../../CLAUDE.md) - 전체 프로젝트 가이드
- [README.md](../../README.md) - 프로젝트 소개
- [실제 코드 위치](../../backend/) - Backend 소스코드

---

## 피드백

문서 개선 제안이나 질문이 있다면:

1. GitHub Issue 생성
2. Pull Request 작성
3. Discussion 참여

---

## 업데이트 이력

- **2025-10-20**: 초기 버전 작성 (4개 문서)
  - N+1 쿼리 최적화
  - Database NULL 제약 조건
  - 이메일 토큰 보안
  - Celery 시작 순서

---

**Happy Debugging!**
