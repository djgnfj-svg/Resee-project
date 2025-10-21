# Portfolio - 이력서용 핵심 문서

> 백엔드 신입 개발자 취업을 위한 핵심 구현 및 트러블슈팅 문서

---

## 📋 문서 구성

이 폴더는 **이력서에 직접 링크할 수 있는 블로그 포스트용 문서**입니다.

### 핵심 구현 (4개)

1. **[Django Signals로 복습 스케줄링 자동화](./01-복습-스케줄링-자동화.md)**
   - 에빙하우스 망각곡선 이론 적용
   - Django Signal 기반 ReviewSchedule 자동 생성
   - 구독 등급별 복습 주기 차등 적용

2. **[JWT + Google OAuth 2.0 멀티 프로바이더 인증 시스템](./02-JWT-인증-시스템.md)**
   - JWT 토큰 기반 인증 (access + refresh)
   - Google OAuth 2.0 통합
   - SHA-256 토큰 해싱 및 Timing Attack 방어

3. **[Anthropic Claude API 학습 콘텐츠 검증 시스템](./03-AI-콘텐츠-검증.md)**
   - Claude 3.5 Sonnet으로 콘텐츠 정확성 검증
   - Claude 3 Haiku로 답변 자동 채점
   - AI 기반 복습 문제 자동 생성

4. **[Docker Compose 7개 서비스 통합 및 CI/CD 구축](./04-Docker-CICD.md)**
   - Docker Compose로 7개 서비스 관리
   - GitHub Actions 기반 CI/CD 파이프라인
   - AWS EC2 자동 배포

### 트러블슈팅 (4개)

5. **[N+1 쿼리 최적화 - 301개 → 3개 쿼리로 줄이기](./05-N+1-쿼리-최적화.md)** ⭐⭐⭐
   - 쿼리 99% 감소 (301개 → 3개)
   - 응답 시간 90% 개선 (500ms → 50ms)
   - select_related(), prefetch_related() 활용

6. **[이메일 토큰 보안 강화 - SHA-256 해싱 및 Timing Attack 방어](./06-이메일-토큰-보안.md)** ⭐⭐⭐
   - 평문 토큰 → SHA-256 해싱
   - Constant-time 비교로 Timing Attack 방어
   - 보안 취약점 수정 과정

7. **[Celery 시작 순서 문제 해결](./07-Celery-시작-순서.md)**
   - Docker Compose 의존성 관리
   - Healthcheck 기반 초기화 순서 제어
   - Entrypoint 스크립트 활용

8. **[Gunicorn Worker 최적화 - 동시성 2배 향상](./08-Gunicorn-Worker-최적화.md)**
   - Worker 1개 → 2개 증가
   - 동시성 2배 향상 (2 → 4)
   - Redis Throttling 멀티 워커 호환성 검증

---

## 🎯 이력서 작성 가이드

### 이력서에 들어갈 내용 (제목 + 링크 형식)

```markdown
### **Resee | AI 기반 스마트 복습 자동화 플랫폼**

AI로 최적의 복습 시점을 추천하는 지능형 학습 관리 플랫폼 백엔드 개발

- **GitHub**: https://github.com/djgnfj-svg/Resee-project
- **Link**: https://reseeall.com/
- **Tech**: Django DRF, Celery, PostgreSQL, Redis, Claude API, Docker, AWS

---

### 주요 기능 및 성과

1. **지능형 복습 스케줄링 엔진 설계**
   - Django Signals를 활용한 자동 복습 스케줄 생성 및 구독 등급별 차등 적용
   - [자세히 보기 →](블로그링크/01-복습-스케줄링-자동화)

2. **JWT + Google OAuth 2.0 멀티 프로바이더 인증 시스템**
   - JWT 토큰 기반 인증 및 SHA-256 해싱으로 보안 강화
   - [자세히 보기 →](블로그링크/02-JWT-인증-시스템)

3. **AI 기반 학습 콘텐츠 검증 및 평가**
   - Anthropic Claude API로 콘텐츠 정확성 검증, 답변 자동 채점, 문제 생성
   - [자세히 보기 →](블로그링크/03-AI-콘텐츠-검증)

4. **Docker Compose 7개 서비스 통합 및 CI/CD**
   - GitHub Actions 기반 자동 배포 파이프라인 구축
   - [자세히 보기 →](블로그링크/04-Docker-CICD)

---

### 트러블슈팅 경험

더 많은 내용은 블로그를 참고해주세요

1. **N+1 쿼리 최적화 - 301개 → 3개 쿼리 (99% 감소)**
   - ORM 최적화 및 복합 인덱싱으로 응답 시간 90% 개선 (500ms → 50ms)
   - [자세히 보기 →](블로그링크/05-N+1-쿼리-최적화)

2. **이메일 토큰 보안 강화 - SHA-256 해싱 및 Timing Attack 방어**
   - 평문 토큰 저장 취약점 발견 및 해시 기반 보안 강화
   - [자세히 보기 →](블로그링크/06-이메일-토큰-보안)

3. **Celery 시작 순서 문제 해결 - Docker Healthcheck 활용**
   - 마이그레이션 전 Celery 시작 에러 해결
   - [자세히 보기 →](블로그링크/07-Celery-시작-순서)

4. **Gunicorn Worker 최적화 - 동시성 2배 향상**
   - Redis Throttling 호환성 검증 후 Worker 증가로 성능 개선
   - [자세히 보기 →](블로그링크/08-Gunicorn-Worker-최적화)
```

---

## 📊 성과 지표

| 항목 | Before | After | 개선율 |
|------|--------|-------|--------|
| N+1 쿼리 개수 | 301개 | 3개 | 99% 감소 |
| API 응답 시간 | 500ms | 50ms | 90% 개선 |
| Gunicorn 동시성 | 2개 요청 | 4개 요청 | 100% 향상 |
| 보안 | 평문 토큰 | SHA-256 해싱 | 취약점 해결 |

---

## 🔗 링크 구조

### 블로그 포스트 URL 예시

```
https://yourblog.com/resee/01-복습-스케줄링-자동화
https://yourblog.com/resee/02-JWT-인증-시스템
https://yourblog.com/resee/03-AI-콘텐츠-검증
https://yourblog.com/resee/04-Docker-CICD
https://yourblog.com/resee/05-N+1-쿼리-최적화
https://yourblog.com/resee/06-이메일-토큰-보안
https://yourblog.com/resee/07-Celery-시작-순서
https://yourblog.com/resee/08-Gunicorn-Worker-최적화
```

---

## 📝 작성 팁

### 각 블로그 포스트에 포함할 내용

1. **문제 상황** - 어떤 문제를 해결하려고 했는가?
2. **기술 선택 이유** - 왜 이 기술을 선택했는가?
3. **구현 과정** - 단계별 코드 및 설명
4. **성과** - 측정 가능한 결과 (쿼리 감소, 응답 시간 개선 등)
5. **배운 점** - 핵심 개념 요약
6. **GitHub 링크** - 실제 코드 위치

### 면접 대비 포인트

- **N+1 쿼리**: "실제로 301개 쿼리를 3개로 줄인 경험이 있습니다"
- **보안**: "Timing Attack 방어를 위해 Constant-time 비교를 적용했습니다"
- **인프라**: "Docker Compose로 7개 서비스를 관리하고 CI/CD를 구축했습니다"
- **AI**: "Claude API를 활용해 비용 효율적으로 AI 서비스를 구현했습니다"

---

## 🎯 사용 방법

1. 각 문서를 블로그에 복사
2. 이미지 추가 (선택사항)
3. 블로그 URL 확인
4. 이력서에 링크 추가

---

**작성일**: 2025-10-21
**문서 수**: 8개 (핵심 구현 4개 + 트러블슈팅 4개)
