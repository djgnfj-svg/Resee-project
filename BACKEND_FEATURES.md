# Resee Backend 기능 정리

## 1. accounts (사용자 관리)

### 1.1 인증 시스템
JWT 토큰 기반 인증 (Access 60분, Refresh 7일), Google OAuth 2.0 소셜 로그인, 이메일 인증 및 재발송 시스템 구현

### 1.2 사용자 관리
회원가입/로그인/로그아웃, 프로필 조회/수정, 비밀번호 변경, 계정 삭제 기능

### 1.3 구독 시스템
티어 관리 (FREE/BASIC/PRO), 업그레이드/다운그레이드, 결제 내역 조회 (Stripe 미연동)

### 1.4 알림 설정 (V0.2)
NotificationPreference 모델, 일일 복습 알림 시간 설정, 이메일 알림 on/off

### 1.5 헬스체크 (V0.3)
기본/상세 헬스체크 API, DB/Redis/Celery/디스크 상태 모니터링, Readiness/Liveness probe

### 1.6 로그 관리 (V0.3)
로그 파일 목록/요약, 최근 에러 조회, 로그 내용 필터링, 로그 분석 및 통계

### 1.7 모니터링 대시보드 (V0.3)
웹 기반 시스템 상태 대시보드, 로그 뷰어 인터페이스, 개발용 대시보드 (인증 불필요)

---

## 2. content (콘텐츠 관리)

### 2.1 콘텐츠 CRUD
생성/조회/수정/삭제, 마크다운 지원, 카테고리 분류, 페이지네이션 (20개/페이지)

### 2.2 카테고리 관리
카테고리 생성/수정/삭제, 사용자별 독립 관리, 카테고리별 콘텐츠 조회

### 2.3 자동 스케줄링
콘텐츠 생성 시 ReviewSchedule 자동 생성 (Signal), 다음날부터 복습 시작

---

## 3. review (복습 시스템)

### 3.1 Ebbinghaus 복습 알고리즘
티어별 복습 간격 (FREE: 3일, BASIC: 90일, PRO: 180일), 성공 시 다음 간격, 실패 시 리셋

### 3.2 복습 관리
오늘의 복습 목록 조회, 복습 완료 처리, ReviewHistory 기록, 카테고리별 통계

### 3.3 백그라운드 태스크 (V0.2)
Celery Beat 스케줄링, 만료된 복습 정리, 일일/저녁/주간 이메일 알림

---

## 4. analytics (분석)

### 4.1 기본 통계
DailyStats 수집 (콘텐츠 생성, 복습 완료, 성공률), 대시보드 데이터 제공

### 4.2 학습 분석
오늘의 복습 수, 전체 콘텐츠 수, 30일 복습 성공률, 카테고리별 성과

---

## 5. weekly_test (주간 시험)

### 5.1 테스트 관리
주간 테스트 생성/시작/완료, 카테고리 선택식 문제 생성, 답안 제출 및 채점

### 5.2 AI 문제 생성
Claude API 연동 (현재 mock), 객관식/주관식/빈칸 문제 생성, 난이도 조절 (추후 구현)

---

## 6. resee (프로젝트 설정)

### 6.1 공통 설정
환경별 설정 분리 (base/development/production), JWT 인증 설정, Celery 백그라운드 작업 설정

### 6.2 인프라
PostgreSQL 데이터베이스, Redis 캐시 (Celery 브로커), Nginx 리버스 프록시

---

## API 엔드포인트 요약

### accounts
- `POST /api/accounts/users/register/` - 회원가입
- `POST /api/auth/token/` - 로그인
- `POST /api/accounts/google-oauth/` - Google OAuth
- `POST /api/accounts/verify-email/` - 이메일 인증
- `GET /api/accounts/profile/` - 프로필 조회
- `GET /api/accounts/subscription/` - 구독 정보
- `GET /api/accounts/notification-preferences/` - 알림 설정
- `GET /api/health/` - 헬스체크
- `GET /api/health/detailed/` - 상세 헬스체크
- `GET /api/accounts/logs/summary/` - 로그 요약
- `GET /api/accounts/monitoring/` - 모니터링 대시보드

### content
- `GET /api/contents/` - 콘텐츠 목록
- `POST /api/contents/` - 콘텐츠 생성
- `GET /api/contents/{id}/` - 콘텐츠 조회
- `PUT /api/contents/{id}/` - 콘텐츠 수정
- `DELETE /api/contents/{id}/` - 콘텐츠 삭제
- `GET /api/categories/` - 카테고리 목록
- `POST /api/categories/` - 카테고리 생성

### review
- `GET /api/review/today/` - 오늘의 복습
- `POST /api/review/complete/` - 복습 완료
- `GET /api/review/stats/category/` - 카테고리별 통계

### analytics
- `GET /api/analytics/dashboard/basic/` - 기본 대시보드

### weekly_test
- `POST /api/weekly-test/tests/` - 테스트 생성
- `POST /api/weekly-test/start/` - 테스트 시작
- `POST /api/weekly-test/submit/` - 답안 제출
- `GET /api/weekly-test/results/{id}/` - 결과 조회

---

## 기술 스택
- **Backend**: Django 4.2, Django REST Framework
- **Database**: PostgreSQL (로컬)
- **Cache**: Redis (Celery 브로커)
- **Task Queue**: Celery + Celery Beat
- **Authentication**: JWT (simplejwt)
- **Infrastructure**: Docker Compose, Nginx
