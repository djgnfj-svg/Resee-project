# ROADMAP: v0.7 → v1.0

## 현재 상태: v0.9 (88% 완성)

**최종 업데이트**: 2025-10-15 (Toss Payments 풀스택 구현 완료)

### ✅ 완성된 기능 (88%)

#### 핵심 학습 시스템
- [x] Ebbinghaus 간격 반복 알고리즘
- [x] 콘텐츠 CRUD (생성, 수정, 삭제, 보관)
- [x] 복습 시스템 및 히스토리 추적
- [x] ReviewSchedule 자동 생성 (시그널)
- [x] 성과 분석 (30일 성공률)
- [x] AI 생성 주간 테스트

#### 사용자 관리
- [x] JWT 인증 (access + refresh 토큰)
- [x] 이메일 인증 시스템
- [x] 회원가입/로그인
- [x] 비밀번호 재설정
- [x] 프로필 관리

#### 구독 시스템
- [x] 구독 티어 (FREE/BASIC/PRO)
- [x] 티어별 복습 간격
- [x] 권한 데코레이터
- [x] Subscription 모델 (확장됨)
- [x] SubscriptionPage UI (가격, 티어 선택)
- [x] PaymentHistoryPage UI
- [x] 구독 업그레이드/다운그레이드 로직
- [x] BillingSchedule 서비스 (자동 갱신)
- [x] PaymentHistory 추적
- [x] 환불 계산 로직
- [x] 비밀번호 보호된 구독 변경
- [x] **NEW**: Toss Payments 백엔드 API (checkout, confirm, webhook)
- [x] **NEW**: Toss Payments 프론트엔드 (CheckoutPage, Success/Fail pages)
- [⚠️] **부족**: 실제 Toss 테스트 계정 연동 및 샌드박스 테스트

#### AI 기능
- [x] 콘텐츠 검증 (Claude API)
- [x] 답변 평가 및 점수
- [x] 문제 자동 생성
- [x] 잘못된 답변 감지

#### 이메일 시스템
- [x] 이메일 인증
- [x] 일일 복습 알림 (Celery)
- [x] 알림 설정
- [x] Celery + Redis 백그라운드 작업

#### 인프라
- [x] Docker Compose (dev + prod)
- [x] Nginx 리버스 프록시
- [x] PostgreSQL 데이터베이스
- [x] React + TypeScript 프론트엔드
- [x] Django REST API 백엔드
- [x] GDPR 준수

#### 운영 인프라
- [x] 구조화된 로깅 (RotatingFileHandler, 10MB, 5 backups)
- [x] 분리된 로그 (django, celery, security)
- [x] Rate limiting (100/hr anon, 1000/hr user, 5/min login)
- [x] 보안 헤더 (XSS, HSTS, X-Frame-Options, Content-Type-Nosniff)
- [x] CORS 설정
- [x] Session/CSRF 쿠키 보안
- [x] CI/CD 파이프라인 (GitHub Actions)
- [x] Health check 엔드포인트

#### 데이터베이스 최적화
- [x] ReviewSchedule 인덱스 (3개: user+date+active, date, user+active)
- [x] ReviewHistory 인덱스 (4개)
- [x] Content 인덱스 (3개: author+created, category+created)
- [x] 캐싱 시스템 (locmem, 5000 max entries)

#### 테스트 & 품질
- [x] 95.7% 테스트 커버리지 (88/92 테스트 통과)
- [x] 린팅 설정 (ESLint, Black)
- [x] TypeScript 타입 안전성
- [x] React 성능 최적화 (25개 useMemo/useCallback/React.memo)

### ⚠️ 부분 완성 (2%)

- [⚠️] **결제 시스템**: 코드 완성, Toss 테스트 계정 연동 필요
- [⚠️] **모니터링**: Health check 있음, Sentry 연동 필요
- [⚠️] **로깅**: 구조화된 로깅 있음, JSON 포맷터 필요
- [⚠️] **백업**: 수동 백업 가능, 자동화 필요
- [⚠️] **프론트엔드 최적화**: 일부 최적화 완료, 코드 스플리팅 필요

### ❌ 미완성 (10%)

- [ ] 실제 결제 게이트웨이 연동 (Toss/Stripe webhook)
- [ ] Sentry 에러 추적 설정
- [ ] python-json-logger 설치
- [ ] 자동 백업 시스템
- [ ] React.lazy 코드 스플리팅
- [ ] E2E 테스트
- [ ] Prometheus + Grafana 메트릭

---

## v1.0 목표: 프로덕션 런칭 준비 완료

**목표**: 결제 및 운영 인프라를 갖춘 완전한 SaaS 서비스

**필수 구성 요소**:
1. **결제 시스템**: BASIC/PRO 유료 구독 결제 (실제 게이트웨이 연동)
2. **운영 인프라**: 모니터링(Sentry), 백업 자동화
3. **프로덕션 강화**: 최종 최적화 및 안정성

---

## 실행 계획 (총 3-4주)

### Phase 1: 결제 시스템 완성 (1-2주)

#### 목표
시뮬레이션된 결제를 실제 Toss Payments로 연동.

#### 현재 상태
- ✅ Payment UI 완성 (SubscriptionPage, PaymentHistoryPage)
- ✅ 백엔드 로직 완성 (upgrade/downgrade/cancel/refund)
- ✅ BillingSchedule 서비스
- ✅ PaymentHistory 추적
- ❌ 실제 Toss Payments 연동
- ❌ Webhook 처리

#### 1.1 Toss Payments 연동

**백엔드 작업**
- [x] Toss Payments 설정 추가 (settings/base.py)
- [x] TossPaymentsService 클래스 생성 (httpx 기반 REST API)
- [x] 결제 시작 API 구현 (/api/accounts/payment/checkout/)
- [x] Toss 웹훅 처리 구현 (/api/accounts/payment/webhook/)
- [x] PaymentHistory 모델에 gateway_payment_id, gateway_order_id 추가
- [x] 결제 확인 API 구현 (/api/accounts/payment/confirm/)
- [x] 결제 성공 시 구독 활성화 로직
- [x] 결제 실패 처리 로직
- [ ] 샌드박스 모드 테스트

**프론트엔드 작업**
- [x] @tosspayments/payment-widget-sdk 설치
- [x] CheckoutPage Toss 위젯 통합
- [x] PaymentSuccessPage 구현 (결제 확인 API 호출)
- [x] PaymentFailPage 구현 (에러 처리)
- [x] SubscriptionPage에서 Checkout으로 리다이렉트
- [x] 라우팅 추가 (/payment/checkout, /payment/success, /payment/fail)

#### 1.2 테스트 & 검증
- [ ] Toss 샌드박스 테스트
- [ ] 웹훅 처리 검증
- [ ] 업그레이드/다운그레이드 시나리오
- [ ] 결제 실패 처리
- [ ] 환불 테스트

---

### Phase 2: 운영 인프라 완성 (1-2주)

#### 목표
프로덕션급 모니터링 및 백업 시스템 완성.

#### 2.1 모니터링 강화

**Sentry (에러 추적)**
- [ ] sentry-sdk 설치 (requirements.txt)
- [ ] Django 연동 (settings/production.py)
- [ ] React 연동 (frontend)
- [ ] 에러 그룹핑 설정
- [ ] Slack 알림 연동
- [ ] 커스텀 에러 핸들러

**작업 목록**:
- [ ] Sentry 계정 생성
- [ ] DSN 설정
- [ ] 샘플 에러 테스트
- [ ] 에러 대시보드 확인

#### 2.2 로깅 개선

**현재 상태**:
- ✅ 구조화된 로깅 (verbose/simple/file formatters)
- ✅ RotatingFileHandler (10MB, 5 backups)
- ✅ 분리된 로그 (django, celery, security)
- ❌ JSON 포맷터

**작업 목록**:
- [ ] python-json-logger 설치
- [ ] JSON 포맷터 추가
- [ ] 요청 ID 추적 (선택)
- [ ] 로그 분석 쿼리 작성

#### 2.3 자동 백업

**데이터베이스 백업**
- 매일 새벽 3시 자동 백업
- 최근 30일 보관
- S3/Object Storage 업로드 (선택)

**작업 목록**:
- [ ] 백업 스크립트 작성
- [ ] Cron job 설정
- [ ] S3 설정 (선택)
- [ ] 복구 절차 테스트
- [ ] 백업 검증

#### 2.4 알림 시스템

**Slack 알림 트리거**:
- 서버 다운
- 에러율 > 5%
- API 응답 > 2초 (p95)
- DB 연결 실패
- Celery 큐 > 100
- 결제 실패 > 10건/시간

**작업 목록**:
- [ ] Slack 웹훅 설정
- [ ] 알림 함수 구현
- [ ] 임계값 설정
- [ ] 이슈 대응 매뉴얼

---

### Phase 3: 최적화 & 안정성 (1주)

#### 3.1 프론트엔드 최적화

**현재 상태**:
- ✅ 일부 React 성능 최적화 (25개 useMemo/useCallback/React.memo)
- ❌ React.lazy 코드 스플리팅
- ❌ 번들 크기 최적화

**작업 목록**:
- [ ] React.lazy로 주요 페이지 lazy loading
- [ ] 번들 분석 (webpack-bundle-analyzer)
- [ ] Tree shaking 확인
- [ ] 이미지 최적화
- [ ] Lighthouse 측정 (> 90)

#### 3.2 부하 테스트

**시나리오**:
- 100명 동시 복습
- 50명 동시 대시보드
- 10명 동시 결제

**수용 기준**:
- API < 200ms (p95)
- 500명 동시 지원
- 에러 없음

**작업 목록**:
- [ ] 테스트 스크립트 작성
- [ ] 베이스라인 실행
- [ ] 병목 식별
- [ ] 최적화 적용
- [ ] 재테스트

#### 3.3 보안 감사

**체크리스트**:
- [ ] OWASP ZAP 스캔
- [ ] git-secrets 확인
- [x] HTTPS 강제 (CloudFlare)
- [ ] SQL Injection 테스트
- [ ] XSS 테스트
- [x] CSRF 확인
- [x] 인증 테스트
- [x] Rate limiting 테스트

---

### Phase 4: 최종 검증 (1주)

#### 4.1 E2E 테스트

**주요 플로우**:
- [ ] 회원가입 → 인증 → 로그인
- [ ] 콘텐츠 생성 → 복습
- [ ] FREE → BASIC (결제)
- [ ] BASIC → PRO
- [ ] 구독 취소
- [ ] 이메일 알림
- [ ] 주간 테스트

#### 4.2 성능 벤치마킹

**메트릭**:
- [ ] Lighthouse > 90
- [ ] API < 200ms (p95)
- [ ] DB 쿼리 < 50ms (p95)
- [ ] 번들 < 300 kB
- [ ] TTI < 2초

#### 4.3 사용자 수용 테스트

**테스트 그룹**: 10-20명

**피드백**:
- 결제 플로우
- 복습 경험
- 성능 체감
- 버그

**작업 목록**:
- [ ] 베타 테스터 모집
- [ ] 테스트 계정 제공
- [ ] 피드백 수집
- [ ] 이슈 수정
- [ ] 반복 개선

#### 4.4 문서화

**필수 문서**:
- [ ] 사용자 가이드
- [ ] API 문서
- [ ] 배포 가이드
- [ ] 트러블슈팅
- [ ] 보안 모범 사례

#### 4.5 런칭 체크리스트

**런칭 전**:
- [ ] 모든 테스트 통과
- [ ] 결제 시스템 검증 (실제 Toss 연동)
- [ ] Sentry 모니터링 설정
- [ ] 알림 테스트
- [ ] 백업 검증
- [x] HTTPS 활성화
- [x] Rate limiting
- [ ] 에러 추적 (Sentry)
- [ ] 성능 충족
- [ ] 문서화

**런칭 당일**:
- [ ] 배포
- [ ] 에러 모니터링
- [ ] 성능 모니터링
- [ ] 플로우 테스트
- [ ] 공지

**런칭 후**:
- [ ] 24시간 모니터링
- [ ] 피드백 수집
- [ ] 긴급 수정

---

## 타임라인 (총 3-4주)

**예상 일정**:
- Phase 1 (결제 완성): 1-2주
- Phase 2 (운영 완성): 1-2주
- Phase 3 (최적화): 1주 (Phase 2와 병렬)
- Phase 4 (검증): 1주

---

## 성공 지표

### 기술
- 99.9% 가동률
- < 200ms API (p95)
- < 0.1% 에러율
- 95%+ 테스트 커버리지

### 비즈니스
- 첫 달 10명 유료
- 3개월 100명 유료
- < 5% 이탈률
- 70%+ FREE→BASIC 전환

### 사용자
- 80%+ 복습 완료율
- 60%+ 30일 유지율
- 4.5+ 앱 평점

---

## 위험 관리

### 결제 리스크
- **위험**: 게이트웨이 다운
- **완화**: 재시도, 큐잉

### 성능 리스크
- **위험**: DB 병목
- **완화**: 캐싱, Read Replica

### 보안 리스크
- **위험**: 데이터 유출
- **완화**: 토큰만 사용

### 런칭 리스크
- **위험**: 중요 버그
- **완화**: Blue-green, 롤백

---

## 결론

**현재**: v0.8 (78% 완성)
**강점**: 핵심 기능 완성, 운영 인프라 대부분 구축됨
**부족**: 실제 결제 연동, Sentry 모니터링, 자동 백업
**목표**: 3-4주 내 v1.0
**다음**: Phase 1 (Toss Payments 연동) 시작

---

## 실제 완성도 분석

### 기대 이상으로 완성된 항목
- ✅ 구독 시스템 백엔드 (upgrade/downgrade/refund 로직)
- ✅ 결제 UI (SubscriptionPage, PaymentHistoryPage)
- ✅ BillingSchedule 서비스
- ✅ 데이터베이스 최적화 (인덱스 전략)
- ✅ 캐싱 시스템
- ✅ 보안 설정 (rate limiting, headers, CORS)
- ✅ 구조화된 로깅
- ✅ CI/CD 파이프라인

### 예상보다 덜 필요한 항목
- Prometheus + Grafana (소규모 서비스에는 Sentry + 기본 로깅으로 충분)
- 복잡한 캐싱 전략 (현재 locmem으로 충분)
- Read Replica (초기에는 단일 DB로 충분)

### 실제 필요한 작업 (v1.0)
1. **Toss Payments 연동** (가장 중요)
2. **Sentry 설정** (10분 작업)
3. **python-json-logger 추가** (5분 작업)
4. **자동 백업 설정** (1시간 작업)
5. **React.lazy 코드 스플리팅** (2-3시간 작업)
6. **E2E 테스트** (품질 보장)

**실제 v1.0까지 소요 시간**: 2-3주 (기존 예상 6-8주보다 짧음)
