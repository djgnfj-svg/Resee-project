# Resee 기능 명세서

## 📋 목차
1. [인증 시스템](#1-인증-시스템)
2. [콘텐츠 관리](#2-콘텐츠-관리)
3. [복습 시스템](#3-복습-시스템)
4. [주간 테스트](#4-주간-테스트)
5. [구독 시스템](#5-구독-시스템)
6. [분석 대시보드](#6-분석-대시보드)
7. [설정 및 프로필](#7-설정-및-프로필)
8. [헬스체크 및 모니터링](#8-헬스체크-및-모니터링)

---

## 1. 인증 시스템

### 1.1 회원가입
- **엔드포인트**: `POST /api/accounts/users/register/`
- **기능**:
  - 이메일/비밀번호 기반 회원가입
  - 이메일 중복 검사
  - 비밀번호 강도 검증 (8자 이상, 숫자/문자 포함)
  - 이메일 인증 메일 발송
  - 약관 동의 (서비스 이용약관, 개인정보처리방침)
- **자동 처리**:
  - FREE 구독 플랜 자동 생성
  - 프로필 생성

### 1.2 로그인
- **엔드포인트**: `POST /api/auth/token/`
- **기능**:
  - 이메일/비밀번호 로그인
  - JWT 토큰 발급 (Access: 60분, Refresh: 7일)
  - 이메일 미인증시 로그인 제한 (설정 가능)
- **보안**:
  - Rate limiting (분당 5회 제한)
  - 실패 시 점진적 지연

### 1.3 Google OAuth 로그인
- **엔드포인트**: `POST /api/accounts/google-oauth/`
- **기능**:
  - Google 계정으로 원클릭 로그인/회원가입
  - 기존 이메일 계정과 자동 연동
  - 이메일 자동 인증 처리
- **상태**: ⚠️ 개발 환경 Client ID 미설정

### 1.4 이메일 인증
- **엔드포인트**:
  - `POST /api/accounts/verify-email/` - 인증 처리
  - `POST /api/accounts/resend-verification/` - 재발송
- **기능**:
  - 토큰 기반 이메일 인증
  - 인증 메일 재발송 (24시간 내 3회 제한)
  - 인증 후 자동 로그인

### 1.5 비밀번호 관리
- **엔드포인트**: `POST /api/accounts/password/change/`
- **기능**:
  - 현재 비밀번호 확인 후 변경
  - 비밀번호 강도 검증
- **미구현**: 비밀번호 찾기/재설정

---

## 2. 콘텐츠 관리

### 2.1 카테고리
- **엔드포인트**:
  - `GET /api/categories/` - 목록 조회
  - `POST /api/categories/` - 생성
  - `PUT /api/categories/{id}/` - 수정
  - `DELETE /api/categories/{id}/` - 삭제
- **기능**:
  - 학습 콘텐츠 분류
  - 사용자별 독립적 관리
  - 카테고리별 통계 제공

### 2.2 콘텐츠
- **엔드포인트**:
  - `GET /api/contents/` - 목록 조회 (페이지네이션)
  - `POST /api/contents/` - 생성
  - `GET /api/contents/{id}/` - 상세 조회
  - `PUT /api/contents/{id}/` - 수정
  - `DELETE /api/contents/{id}/` - 삭제
  - `GET /api/contents/by_category/` - 카테고리별 조회
- **기능**:
  - 마크다운 지원
  - 카테고리 분류
  - 생성 즉시 복습 스케줄 자동 생성 (신호 기반)
- **제한사항**:
  - FREE: 최대 50개
  - BASIC: 최대 500개
  - PRO: 무제한

---

## 3. 복습 시스템 (Ebbinghaus)

### 3.1 복습 스케줄
- **엔드포인트**:
  - `GET /api/review/today/` - 오늘의 복습 목록
  - `POST /api/review/complete/` - 복습 완료 처리
- **기능**:
  - Ebbinghaus 망각곡선 기반 자동 스케줄링
  - 복습 간격:
    - FREE: [1, 3일]
    - BASIC: [1, 3, 7, 14, 30, 60, 90일]
    - PRO: [1, 3, 7, 14, 30, 60, 120, 180일]
  - 성공/실패에 따른 간격 조정

### 3.2 복습 프로세스
1. 콘텐츠 생성 → ReviewSchedule 자동 생성
2. 다음날부터 복습 시작
3. 복습 완료 시:
   - 성공: 다음 간격으로 진행
   - 실패: 첫 간격으로 리셋
4. 모든 간격 완료 시 장기 기억 전환

### 3.3 복습 통계
- **엔드포인트**: `GET /api/review/stats/category/`
- **제공 정보**:
  - 카테고리별 복습 진행률
  - 성공률
  - 평균 복습 간격

---

## 4. 주간 테스트

### 4.1 테스트 생성
- **엔드포인트**: `POST /api/weekly-test/tests/`
- **기능**:
  - 주 1회 자동 생성 가능
  - AI 문제 생성 (현재 비활성화)
  - 카테고리 선택식
- **제한사항**:
  - FREE: 주 1회
  - BASIC/PRO: 무제한

### 4.2 테스트 진행
- **엔드포인트**:
  - `POST /api/weekly-test/start/` - 시작
  - `POST /api/weekly-test/submit/` - 답안 제출
  - `POST /api/weekly-test/complete/` - 완료
  - `GET /api/weekly-test/results/{id}/` - 결과 조회
- **기능**:
  - 시간 제한 설정 가능
  - 문제별 피드백
  - 점수 및 성과 기록

### 4.3 상태 관리
- `preparing`: AI API 미사용시 대기 상태
- `ready`: 시작 가능
- `in_progress`: 진행 중
- `completed`: 완료

---

## 5. 구독 시스템

### 5.1 구독 플랜
- **엔드포인트**: `GET /api/accounts/subscription/tiers/`
- **플랜 종류**:
  ```
  FREE (무료):
  - 콘텐츠 50개
  - 복습 간격 3일
  - 주간 테스트 1회

  BASIC ($9.99/월):
  - 콘텐츠 500개
  - 복습 간격 90일
  - 주간 테스트 무제한

  PRO ($19.99/월):
  - 콘텐츠 무제한
  - 복습 간격 180일
  - 주간 테스트 무제한
  - AI 기능 (예정)
  ```

### 5.2 구독 관리
- **엔드포인트**:
  - `GET /api/accounts/subscription/` - 현재 구독 정보
  - `POST /api/accounts/subscription/upgrade/` - 업그레이드
  - `POST /api/accounts/subscription/downgrade/` - 다운그레이드
  - `POST /api/accounts/subscription/cancel/` - 취소
  - `POST /api/accounts/subscription/toggle-auto-renewal/` - 자동갱신 설정
- **상태**: ⚠️ 결제 시스템 미연동 (Stripe 예정)

### 5.3 결제 내역
- **엔드포인트**:
  - `GET /api/accounts/payment-history/` - 결제 이력
  - `GET /api/accounts/billing-schedule/` - 예정 결제

---

## 6. 분석 대시보드

### 6.1 기본 통계
- **엔드포인트**: `GET /api/analytics/dashboard/basic/`
- **제공 정보**:
  - 오늘의 복습 (완료/전체)
  - 전체 콘텐츠 수
  - 30일 복습 성공률
- **특징**: 게임화 요소 제거 (스트릭, 성취도 등)

---

## 7. 설정 및 프로필

### 7.1 프로필 관리
- **엔드포인트**:
  - `GET /api/accounts/profile/` - 조회
  - `PUT /api/accounts/profile/` - 수정
- **관리 항목**:
  - 이름
  - 프로필 이미지 (URL)
  - 주간 목표

### 7.2 계정 삭제
- **엔드포인트**: `POST /api/accounts/account/delete/`
- **기능**:
  - 비밀번호 확인
  - "DELETE" 문자 입력 확인
  - 모든 데이터 영구 삭제

### 7.3 알림 설정
- **UI 존재**: `NotificationTab.tsx`
- **상태**: ❌ 백엔드 미구현

---

## 8. 헬스체크 및 모니터링

### 8.1 헬스체크
- **엔드포인트**:
  - `GET /api/health/` - 기본 상태
  - `GET /api/health/detailed/` - 상세 정보
  - `GET /api/health/ready/` - 준비 상태
  - `GET /api/health/live/` - 생존 확인
- **체크 항목**:
  - 데이터베이스 연결
  - 캐시 시스템 (로컬 메모리)
  - 디스크 공간

---

## 🚧 미구현 기능

### 필수 기능
1. **이메일 알림 시스템** (v0.2)
   - 복습 알림
   - 주간 요약
   - 스케줄링 시스템 필요

2. **결제 시스템** (v0.5)
   - Stripe 연동
   - 실제 구독 결제

3. **비밀번호 재설정**
   - 이메일 기반 재설정

### 선택 기능
1. **AI 기능** (v0.4)
   - 주관식 복습
   - 스마트 문제 생성
   - 콘텐츠 품질 분석

2. **모바일 앱**
   - React Native
   - 푸시 알림

---

## 📝 기술 스택
- **Backend**: Django 4.2, Django REST Framework
- **Frontend**: React 18, TypeScript, TailwindCSS
- **Database**: PostgreSQL
- **Cache**: Django Local Memory Cache
- **인증**: JWT (simplejwt)
- **배포**: Docker Compose, Nginx

## 🔒 보안 기능
- JWT 기반 인증
- Rate Limiting (API 요청 제한)
- CORS 설정
- SQL Injection 방어 (Django ORM)
- XSS 방어 (React)
- CSRF 보호

## 📊 현재 상태 (2025-09-28)
- **v0.1** 완료: 기본 학습 시스템
- **v0.2** 진행 중: Google OAuth (90%), 이메일 알림 (0%)
- **활성 사용자**: 테스트 계정만
- **코드 품질**: 테스트 커버리지 70%+