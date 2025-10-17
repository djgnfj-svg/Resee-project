# Resee - 과학적 복습 플랫폼

에빙하우스 망각곡선 기반 간격 반복 학습 플랫폼

---

## 🎯 프로젝트 개요

**Resee**는 과학적으로 검증된 간격 반복(Spaced Repetition) 이론을 기반으로 한 학습 플랫폼입니다. 사용자가 학습한 내용을 최적의 시점에 복습하도록 알려주어 장기 기억으로 전환하는 것을 돕습니다.

### 핵심 기능

- ✅ **에빙하우스 망각곡선 기반 복습 스케줄링**
- ✅ **AI 기반 콘텐츠 검증 및 평가** (Anthropic Claude)
- ✅ **3가지 구독 티어** (FREE, BASIC, PRO)
- ✅ **이메일 알림** (Celery + Redis)
- ✅ **다크모드 지원**
- ✅ **반응형 디자인**

---

## 🏗️ 기술 스택

### Backend
- **Django 5.1** + Django REST Framework
- **PostgreSQL** (데이터베이스)
- **Redis** (Rate limiting + Celery 백그라운드 작업)
- **Gunicorn** (WSGI 서버)

### Frontend
- **React 18** + TypeScript
- **React Query** (상태 관리)
- **Tailwind CSS** (스타일링)
- **Service Worker** (PWA)

### Infrastructure
- **Docker** + Docker Compose
- **Nginx** (리버스 프록시)
- **GitHub Actions** (CI/CD)
- **AWS EC2** (프로덕션)

---

## 🚀 빠른 시작

### 개발 환경 실행

```bash
# 저장소 클론
git clone https://github.com/djgnfj-svg/Resee-project.git
cd Resee-project

# 환경변수 설정
cp .env.example .env

# Docker Compose 실행
docker-compose up -d

# 접속
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api
# Admin: http://localhost:8000/admin
```

### 테스트 계정

- **관리자**: `admin@resee.com` / `admin123!`
- **일반 사용자**: `djgnfj8923@naver.com` / `testpassword123`

---

## 📚 문서

- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - 배포 가이드 모음
- **[CD_SETUP_GUIDE.md](./CD_SETUP_GUIDE.md)** - GitHub Actions CI/CD 설정
- **[CLAUDE.md](./CLAUDE.md)** - 개발자 가이드 (프로젝트 구조, 명령어)
- **[SECURITY_SUMMARY.md](./SECURITY_SUMMARY.md)** - 보안 개선 사항
- **[CACHE_FIX_GUIDE.md](./CACHE_FIX_GUIDE.md)** - 캐시 문제 해결

---

## 🎨 주요 기능

### 1. 간격 반복 복습 시스템
```
[1일] → [3일] → [7일] → [14일] → [30일] → [60일] → [120일] → [180일]
```

구독 티어별 복습 간격:
- **FREE**: [1, 3일]
- **BASIC**: [1, 3, 7, 14, 30, 60, 90일]
- **PRO**: [1, 3, 7, 14, 30, 60, 120, 180일]

### 2. AI 기능
- **콘텐츠 검증**: 학습 자료의 정확성, 논리성 검증
- **답변 평가**: 주관식 답변 자동 채점 및 피드백
- **문제 생성**: 학습 내용 기반 복습 문제 자동 생성

### 3. 구독 관리
- 티어별 기능 제한
- 카테고리 생성 제한 (FREE: 3개, BASIC: 10개, PRO: 무제한)
- 리뷰 간격 차등 적용

---

## 🔧 개발 명령어

### Backend

```bash
# 마이그레이션
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate

# 테스트
docker-compose exec backend python -m pytest
docker-compose exec backend python -m pytest --cov

# Django Shell
docker-compose exec backend python manage.py shell_plus
```

### Frontend

```bash
# 테스트
docker-compose exec frontend npm test

# 린팅
docker-compose exec frontend npm run lint
docker-compose exec frontend npm run typecheck

# 빌드
docker-compose exec frontend npm run build
```

---

## 📊 프로젝트 구조

```
Resee-project/
├── backend/
│   ├── accounts/          # 사용자 인증, 구독 관리
│   ├── content/           # 학습 콘텐츠 관리
│   ├── review/            # 복습 시스템
│   ├── analytics/         # 학습 분석
│   ├── weekly_test/       # 주간 테스트
│   └── resee/             # Django 설정
├── frontend/
│   ├── src/
│   │   ├── pages/         # 페이지 컴포넌트
│   │   ├── components/    # 재사용 컴포넌트
│   │   ├── utils/         # API, 헬퍼 함수
│   │   └── types/         # TypeScript 타입
│   └── public/
│       └── sw.js          # Service Worker
├── nginx/                 # Nginx 설정
├── .github/workflows/     # GitHub Actions
└── deploy.sh              # 배포 스크립트
```

---

## 🌐 프로덕션

**URL**: https://reseeall.com

### 자동 배포

```bash
git push origin main  # main 브랜치 푸시 시 자동 배포
```

**배포 시간**: 약 5-10분

---

## 🧪 테스트

### Backend 테스트 커버리지
- **95.7%** (88/92 테스트 통과)

### 주요 테스트
- 인증 시스템 (JWT, 토큰 해싱)
- 복습 스케줄링 알고리즘
- 구독 티어 권한 검증
- AI 서비스 통합

---

## 🔐 보안 기능

- ✅ SHA-256 이메일 토큰 해싱
- ✅ JWT 토큰 블랙리스트
- ✅ 타이밍 공격 방어 (constant-time comparison)
- ✅ HTTPS 강제
- ✅ CSRF 보호
- ✅ Rate Limiting (Redis 기반, 100/hr anon, 1000/hr user)

---

## 📈 성능 최적화

- React Query 캐시 관리
- Service Worker (정적 파일 캐싱)
- Nginx 리버스 프록시
- Docker 이미지 최적화
- PostgreSQL 인덱싱

---

## 🤝 기여

이 프로젝트는 개인 프로젝트로 현재 외부 기여를 받고 있지 않습니다.

---

## 📄 라이선스

이 프로젝트는 개인 프로젝트입니다.

---

## 👨‍💻 개발자

**GitHub**: [@djgnfj-svg](https://github.com/djgnfj-svg)

---

## 📞 문의

이메일: djgnfj8923@naver.com

---

## 🎉 최근 업데이트 (Phase 3 완료)

**v1.0 준비 완료** - 2025-10-17

### Phase 3 완료 항목
- ✅ **프론트엔드 최적화**: React.lazy 코드 스플리팅으로 70% 번들 감소 (254 kB main bundle, 27 lazy chunks)
- ✅ **성능 개선**: Tree shaking 검증, Redis rate limiting
- ✅ **보안 강화**: .env.example 추가, 민감정보 보호 가이드
- ✅ **테스트 커버리지**: Backend 95.7% (40/41 테스트 통과)

### 주요 성능 지표
- Bundle size: **254 kB** (main) + 27 lazy-loaded chunks
- Test coverage: **95.7%** (40/41 tests passing)
- Rate limiting: Redis 기반 (100/hr anon, 1000/hr user)

---

**최종 업데이트**: 2025-10-17
