# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🏗️ 프로젝트 개요
Resee는 에빙하우스 망각곡선 이론을 활용한 스마트 복습 플랫폼입니다. Django(백엔드)와 React(프론트엔드)로 구성되어 있으며, Docker Compose로 전체 개발 환경을 관리합니다.

### 핵심 서비스
- **Backend**: Django REST Framework + PostgreSQL + Celery
- **Frontend**: React + TypeScript + TailwindCSS
- **AI Service**: Claude API (Anthropic)
- **Message Queue**: RabbitMQ (Celery 브로커)
- **Cache**: Redis
- **Reverse Proxy**: Nginx

## 🎯 해야할 것 (TODO)

### 1. 새로운 기능 개발 시
```bash
# 1. 브랜치 생성
git checkout -b feature/새기능명

# 2. 백엔드 앱 생성 (필요시)
docker-compose exec backend python manage.py startapp 앱이름
# resee/settings.py의 INSTALLED_APPS에 추가

# 3. 모델 생성 후
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate

# 4. 테스트 작성 및 실행
docker-compose exec backend pytest -k "test_새기능" -v

# 5. 프론트엔드 타입 체크
docker-compose exec frontend npx tsc --noEmit

# 6. E2E 테스트 실행
docker-compose exec frontend npx playwright test
```

### 2. 버그 수정 시
```bash
# 1. 재현 가능한 테스트 작성
docker-compose exec backend pytest -k "test_버그재현" -v --pdb

# 2. 로그 확인
docker-compose logs -f backend --since "10m"
docker-compose exec backend tail -f logs/django.log

# 3. 디버깅
# 코드에 추가: import ipdb; ipdb.set_trace()
docker-compose exec backend python manage.py shell_plus
```

### 3. 배포 전
```bash
# 1. 코드 품질 체크
docker-compose exec backend black . --check
docker-compose exec backend black .  # 코드 포맷팅 적용
docker-compose exec backend flake8
docker-compose exec backend python manage.py check  # Django 시스템 체크
docker-compose exec frontend npm run lint
docker-compose exec frontend npm run lint:fix  # 자동 수정
docker-compose exec frontend npx tsc --noEmit  # TypeScript 타입 체크

# 2. 전체 테스트 실행
docker-compose exec backend pytest
docker-compose exec frontend npm test -- --watchAll=false

# 3. 프로덕션 빌드 테스트
docker-compose exec frontend npm run build
docker-compose build --no-cache  # Docker 이미지 새로 빌드

# 4. 마이그레이션 확인
docker-compose exec backend python manage.py showmigrations
docker-compose exec backend python manage.py makemigrations --dry-run  # 예상 마이그레이션 확인
```

## 🔧 수정해야할 것 (FIX)

### 1. 일반적인 오류들

#### TypeError/AttributeError
```bash
# 1. 모델 필드 확인
docker-compose exec backend python manage.py shell
>>> from content.models import Content
>>> Content._meta.get_fields()

# 2. 시리얼라이저 필드 확인
>>> from content.serializers import ContentSerializer
>>> ContentSerializer().fields.keys()
```

#### 마이그레이션 충돌
```bash
# 1. 충돌하는 마이그레이션 제거
docker-compose exec backend python manage.py showmigrations
docker-compose exec backend rm app_name/migrations/0002_*.py

# 2. 다시 생성
docker-compose exec backend python manage.py makemigrations

# 3. fake 적용 (이미 적용된 경우)
docker-compose exec backend python manage.py migrate --fake app_name 0001
```

#### JWT 인증 오류
```bash
# 1. 토큰 확인
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@resee.com", "password": "test123!"}'

# 2. 토큰 디코드 확인
docker-compose exec backend python manage.py shell
>>> import jwt
>>> token = "YOUR_TOKEN"
>>> jwt.decode(token, options={"verify_signature": False})
```

### 2. 프론트엔드 오류

#### 타입스크립트 오류
```bash
# 1. 타입 정의 확인
docker-compose exec frontend npx tsc --noEmit --listFiles | grep "\.d\.ts"

# 2. 타입 생성 (백엔드 모델 기반)
# backend/content/types.py 생성 후
docker-compose exec backend python manage.py generate_typescript_types > frontend/src/types/generated.ts
```

#### React Query 캐시 문제
```typescript
// 캐시 무효화
queryClient.invalidateQueries(['contents']);

// 특정 쿼리만 새로고침
queryClient.refetchQueries(['contents', { category: 'programming' }]);
```

## ✅ 확인해야할 것 (CHECK)

### 1. 개발 시작 전
```bash
# 1. 환경 변수 확인
docker-compose exec backend python -c "import os; print('ANTHROPIC_API_KEY:', 'Set' if os.environ.get('ANTHROPIC_API_KEY') else 'Not set')"
docker-compose exec backend python -c "import os; print('GOOGLE_OAUTH2_CLIENT_ID:', 'Set' if os.environ.get('GOOGLE_OAUTH2_CLIENT_ID') else 'Not set')"

# 2. 서비스 상태 확인
docker-compose ps
curl http://localhost:8000/api/health/

# 3. 테스트 데이터 확인
docker-compose exec backend python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.filter(email__in=['admin@resee.com', 'test@resee.com', 'demo@resee.com']).exists()
```

### 2. AI 기능 작업 시
```bash
# 1. AI 사용량 확인
docker-compose exec backend python manage.py shell
>>> from ai_review.models import AIUsageTracking
>>> from django.contrib.auth import get_user_model
>>> user = get_user_model().objects.get(email='test@resee.com')
>>> usage = AIUsageTracking.get_daily_usage(user)
>>> print(f"Today: {usage['used']}/{usage['limit']} (Tier: {user.subscription.tier})")

# 2. Claude API 연결 테스트
>>> from ai_review.services import AIQuestionService
>>> service = AIQuestionService()
>>> service.test_connection()  # True면 정상
```

### 3. 복습 시스템 작업 시
```bash
# 1. 복습 스케줄 확인
docker-compose exec backend python manage.py shell
>>> from review.models import ReviewSchedule
>>> from django.utils import timezone
>>> today = timezone.now().date()
>>> ReviewSchedule.objects.filter(next_review_date=today).count()

# 2. Celery 작업 확인
docker-compose exec celery celery -A resee inspect active
docker-compose exec celery celery -A resee inspect scheduled
```

## 📋 기능별 플로우 정리

### 1. 사용자 인증 플로우

#### 회원가입
```
Frontend (RegisterPage) 
    → POST /api/accounts/users/register/
    → Backend (UserViewSet.register)
    → 이메일 인증 토큰 생성
    → Celery: send_verification_email 태스크
    → 사용자에게 인증 이메일 발송
```

#### 이메일 인증
```
이메일 링크 클릭
    → GET /api/accounts/users/verify-email/?token=xxx
    → Backend (UserViewSet.verify_email)
    → user.email_verified = True
    → 로그인 페이지로 리다이렉트
```

#### Google OAuth 로그인
```
Google 로그인 버튼 클릭
    → Google OAuth 동의 화면
    → 콜백: POST /api/accounts/users/google-auth/
    → Backend: ID 토큰 검증
    → 신규/기존 사용자 처리
    → JWT 토큰 발급
    → Frontend: 토큰 저장 및 대시보드 이동
```

### 2. 콘텐츠 생성 및 복습 플로우

#### 콘텐츠 생성
```
ContentForm (TipTap Editor)
    → POST /api/content/contents/
    → Django Signal: post_save
    → Celery: create_review_schedule_for_content
    → ReviewSchedule 생성 (initial_review_completed=False)
    → 즉시 복습 가능 상태
```

#### 복습 프로세스
```
복습 페이지 접속
    → GET /api/review/today/
    → 오늘 복습할 콘텐츠 목록
    → 사용자 복습 수행
    → POST /api/review/complete/
    → ReviewHistory 생성
    → ReviewSchedule 업데이트 (다음 간격으로)
```

### 3. AI 질문 생성 플로우

#### 질문 생성
```
콘텐츠 상세 페이지
    → "AI 질문 생성" 버튼
    → POST /api/ai-review/generate-questions/
    → AIQuestionService.generate_questions()
    → Claude API 호출
    → AIQuestion 모델에 저장
    → AIUsageTracking 업데이트
    → Frontend에 질문 표시
```

#### 사용량 제한 체크
```
요청 전:
    → AIUsageTracking.can_generate() 체크
    → 구독 티어별 일일 한도 확인
    → 초과 시 에러 반환
    → 정상 시 질문 생성 진행
```

### 4. 구독 시스템 플로우

#### 구독 업그레이드
```
구독 페이지
    → 플랜 선택
    → POST /api/accounts/subscription/upgrade/
    → Subscription 모델 업데이트
    → 새로운 기능 한도 적용
    → Celery: 구독 만료 스케줄링
```

## 🚀 필수 명령어 Quick Reference

### 개발 환경 설정
```bash
# 최초 실행 시
docker-compose up -d
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py create_test_users

# 시작/중지
docker-compose up -d
docker-compose down

# 특정 서비스만 재시작
docker-compose restart backend
docker-compose restart frontend
docker-compose restart celery

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery
docker-compose logs -f rabbitmq

# 쉘 접속
docker-compose exec backend bash
docker-compose exec frontend bash

# Django shell (향상된 shell_plus)
docker-compose exec backend python manage.py shell_plus
```

### 데이터베이스
```bash
# 마이그레이션
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate

# DB 쉘
docker-compose exec db psql -U resee_user -d resee_db

# 백업
docker-compose exec db pg_dump -U resee_user resee_db > backup.sql
```

### 테스트
```bash
# 백엔드
docker-compose exec backend pytest -v
docker-compose exec backend pytest -k "특정테스트" -v
docker-compose exec backend pytest -m unit  # 유닛 테스트만
docker-compose exec backend pytest -m integration  # 통합 테스트만
docker-compose exec backend pytest -m "not slow"  # 느린 테스트 제외
docker-compose exec backend pytest --pdb  # 실패 시 디버거 실행

# 프론트엔드
docker-compose exec frontend npm test
docker-compose exec frontend npm test -- --coverage
docker-compose exec frontend npm run test:coverage  # 커버리지 리포트
docker-compose exec frontend npm run test:ci  # CI 환경용

# E2E 테스트
docker-compose exec frontend npx playwright test
docker-compose exec frontend npx playwright test --ui  # UI 모드
docker-compose exec frontend npx playwright test --headed  # 브라우저 보며 실행
docker-compose exec frontend npx playwright test --debug  # 디버그 모드
```

### 프로덕션
```bash
# 배포
./ops.sh deploy

# 상태 확인
./ops.sh status
./ops.sh health --detailed

# 백업
./ops.sh backup daily
```

## 🧪 테스트 데이터 생성

### 샘플 데이터 생성
```bash
# 테스트 사용자 생성
docker-compose exec backend python manage.py create_test_users

# 샘플 콘텐츠 생성
docker-compose exec backend python manage.py create_sample_data
```

## 🏗️ 아키텍처 핵심 요약

### 백엔드 구조
```
backend/
├── accounts/      # 사용자, 구독 관리
├── content/       # 학습 콘텐츠
├── review/        # 복습 시스템
├── ai_review/     # AI 기능
├── analytics/     # 학습 분석
├── monitoring/    # 시스템 모니터링
└── resee/         # 설정
```

### 프론트엔드 구조
```
frontend/src/
├── components/    # 재사용 컴포넌트
│   ├── ai/       # AI 관련 컴포넌트
│   └── analytics/ # 분석 차트 컴포넌트
├── pages/         # 페이지 컴포넌트
├── contexts/      # 전역 상태 (Auth, Theme)
├── hooks/         # 커스텀 훅
├── utils/         # API 클라이언트
├── types/         # TypeScript 타입
└── styles/        # 전역 스타일
```

### 핵심 모델 관계
- User → Content (1:N)
- User → ReviewSchedule (1:N)
- Content → ReviewSchedule (1:1)
- Content → AIQuestion (1:N)
- User → Subscription (1:1)

### API 인증
- JWT (Access: 5분, Refresh: 7일)
- 이메일 기반 로그인
- Google OAuth 2.0 지원

### 복습 간격
- 즉시 → 1일 → 3일 → 7일 → 14일 → 30일
- 구독 티어별 최대 간격 제한

## 🔍 디버깅 팁

### 1. 500 에러 발생 시
```bash
# 1. Django 로그 확인
docker-compose logs backend --tail=50

# 2. Sentry 또는 로컬 로그 파일
docker-compose exec backend tail -f logs/error.log

# 3. DEBUG 모드로 상세 확인
# .env에서 DEBUG=True 설정 후 재시작
```

### 2. Celery 태스크 실패 시
```bash
# 1. Worker 로그 확인
docker-compose logs celery -f

# 2. RabbitMQ 상태 확인
docker-compose exec rabbitmq rabbitmqctl list_queues

# 3. 수동 실행 테스트
docker-compose exec backend python manage.py shell
>>> from review.tasks import send_daily_review_notifications
>>> send_daily_review_notifications.apply_async()
```

### 3. 프론트엔드 빌드 실패 시
```bash
# 1. 의존성 정리
docker-compose exec frontend rm -rf node_modules package-lock.json
docker-compose exec frontend npm install

# 2. 타입 오류 확인
docker-compose exec frontend npx tsc --noEmit

# 3. 환경 변수 확인
docker-compose exec frontend printenv | grep REACT_APP_

# 4. 컨테이너 재시작 (메모리 부족 시)
docker-compose restart frontend
```

### 4. 캘린더 히트맵 문제 해결
```bash
# 1. 백엔드 데이터 확인
docker-compose exec backend python manage.py shell
>>> from review.models import ReviewHistory
>>> from django.contrib.auth import get_user_model
>>> user = get_user_model().objects.get(email='test@resee.com')
>>> ReviewHistory.objects.filter(user=user).count()

# 2. API 응답 확인
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/analytics/calendar/

# 3. 프론트엔드 캐시 무효화
queryClient.invalidateQueries({ queryKey: ['learning-calendar'] });
```

### 5. 주간 목표 및 진행률 문제
```bash
# 1. 사용자 설정 확인
docker-compose exec backend python manage.py shell
>>> from accounts.models import UserProfile
>>> profile = UserProfile.objects.get(user__email='test@resee.com')
>>> print(f"Weekly goal: {profile.weekly_goal}")

# 2. 이번 주 복습 횟수 확인
>>> from review.models import ReviewHistory
>>> from django.utils import timezone
>>> from datetime import timedelta
>>> week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
>>> count = ReviewHistory.objects.filter(user=profile.user, completed_at__date__gte=week_start).count()
>>> print(f"This week reviews: {count}")
```

## 🌐 환경 변수 설정

### 필수 환경 변수
```bash
# Backend (.env)
SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=postgres://resee_user:resee_password@db:5432/resee_db
CELERY_BROKER_URL=amqp://resee:resee_password@rabbitmq:5672//
REDIS_URL=redis://redis:6379/0

# AI 서비스
ANTHROPIC_API_KEY=your-anthropic-api-key

# Google OAuth
GOOGLE_OAUTH2_CLIENT_ID=your-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret

# Email (AWS SES)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_SES_REGION_NAME=us-east-1

# Frontend (.env)
REACT_APP_API_URL=http://localhost:8000
REACT_APP_GOOGLE_CLIENT_ID=your-client-id
```

## 🔐 인증 및 보안

### JWT 토큰 설정
- Access Token: 5분 (자동 갱신)
- Refresh Token: 7일
- 토큰은 httpOnly 쿠키로 저장

### CORS 설정
개발 환경에서는 `http://localhost:3000`에서의 요청을 허용합니다.
프로덕션에서는 실제 도메인으로 변경 필요.

## 📱 PWA 기능

### PWA 아이콘 생성
```bash
docker-compose exec frontend npm run pwa:icons
```

### PWA 테스트
```bash
docker-compose exec frontend npm run pwa:test
```

### Lighthouse 성능 테스트
```bash
# 프론트엔드 실행 중에
docker-compose exec frontend npx lighthouse http://localhost:3000 --view
```

## 🔧 유용한 개발 도구 명령어

### Django 관리 명령어
```bash
# 슈퍼유저 생성
docker-compose exec backend python manage.py createsuperuser

# 특정 앱의 마이그레이션만 생성
docker-compose exec backend python manage.py makemigrations app_name

# SQL 쿼리 확인
docker-compose exec backend python manage.py sqlmigrate app_name 0001

# 모든 URL 패턴 확인
docker-compose exec backend python manage.py show_urls

# 데이터베이스 플러시 (주의: 모든 데이터 삭제)
docker-compose exec backend python manage.py flush

# 정적 파일 수집 (프로덕션용)
docker-compose exec backend python manage.py collectstatic --noinput
```

### Celery 작업 관리
```bash
# Celery 워커 상태 확인
docker-compose exec celery celery -A resee status

# 대기 중인 작업 확인
docker-compose exec celery celery -A resee inspect active

# 예약된 작업 확인
docker-compose exec celery celery -A resee inspect scheduled

# 특정 큐의 작업 삭제
docker-compose exec celery celery -A resee purge -Q celery
```

### 성능 모니터링
```bash
# Django Debug Toolbar 활성화 (settings.py에서 DEBUG=True 필요)
# 브라우저에서 http://localhost:8000/__debug__/ 접속

# 데이터베이스 쿼리 분석
docker-compose exec backend python manage.py debugsqlshell
```

## 🐛 자주 발생하는 문제들

### 1. 캘린더 히트맵이 업데이트되지 않는 경우
**원인**: 프론트엔드 캐시와 백엔드 날짜 범위 문제
**해결**: 
- 백엔드: `analytics/views.py`에서 날짜 범위를 정확히 365일(오늘 포함)로 설정
- 프론트엔드: React Query 캐시 무효화 및 실제 API 데이터 범위 사용

### 2. 주간 목표가 100% 초과 시 표시되지 않는 경우  
**원인**: Math.min()으로 진행률을 100%로 제한
**해결**: Math.min() 제거하고 초과 표시 UI 추가

### 3. TypeScript 컴파일 오류로 프론트엔드 컨테이너 중단
**원인**: 변수 선언 전 사용, 타입 불일치
**해결**: 
```bash
docker-compose exec frontend npx tsc --noEmit  # 오류 확인
docker-compose restart frontend  # 컨테이너 재시작
```

### 4. 시간 표시가 영어(AM/PM)로 나오는 경우
**원인**: date-fns 기본 로케일이 영어
**해결**: 수동으로 한국어 포맷 함수 구현
```typescript
const formatHour = (hour: number) => {
  if (hour === 0) return '오전 12시';
  if (hour < 12) return `오전 ${hour}시`;
  if (hour === 12) return '오후 12시';  
  return `오후 ${hour - 12}시`;
};
```

### 5. 복습 완료 후 진행률이 정확하지 않은 경우
**원인**: 백엔드와 프론트엔드 간 데이터 동기화 문제
**해결**: 복습 완료 후 관련 쿼리 캐시 무효화
```typescript
queryClient.invalidateQueries({ queryKey: ['learning-calendar'] });
queryClient.invalidateQueries({ queryKey: ['advanced-analytics'] });
```

### 6. Git 커밋 작성자 정보 변경
**원인**: 잘못된 사용자 정보로 커밋됨
**해결**:
```bash
# 모든 unpushed 커밋의 작성자 변경
git filter-branch --env-filter 'AUTHOR_NAME="djgnfj-svg"; AUTHOR_EMAIL="djgnfj@naver.com"; COMMITTER_NAME="djgnfj-svg"; COMMITTER_EMAIL="djgnfj@naver.com"' HEAD~48..HEAD
```

## 🔍 성능 최적화 팁

### 1. React Query 설정
- staleTime과 cacheTime을 적절히 설정하여 불필요한 API 호출 방지
- 캐시 무효화는 데이터 변경 시에만 수행

### 2. 타입스크립트 컴파일 최적화
- incremental 컴파일 활성화
- strict 모드 사용으로 런타임 오류 방지

### 3. Docker 컨테이너 메모리 관리
- 프론트엔드 빌드 시 메모리 부족 현상 발생 가능
- 필요시 컨테이너 재시작으로 해결

## 🔌 API 테스트 및 디버깅

### API 엔드포인트 테스트
```bash
# 헬스체크
curl http://localhost:8000/api/health/

# JWT 토큰 획득
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@resee.com", "password": "test123!"}'

# 인증된 요청 예시
TOKEN="your-access-token"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/content/contents/

# API 문서 확인 (Swagger UI)
# 브라우저에서 http://localhost:8000/api/docs/ 접속
```

### React 개발 도구
```bash
# 번들 크기 분석
docker-compose exec frontend npm run build -- --stats
docker-compose exec frontend npx webpack-bundle-analyzer build/bundle-stats.json

# 의존성 업데이트 확인
docker-compose exec frontend npm outdated

# 의존성 보안 취약점 검사
docker-compose exec frontend npm audit
docker-compose exec frontend npm audit fix  # 자동 수정
```

## 🔒 보안 체크리스트

### 개발 시 주의사항
- 절대 시크릿 키나 API 키를 코드에 하드코딩하지 않음
- 환경 변수는 .env 파일로 관리 (.env는 .gitignore에 포함)
- 사용자 입력은 항상 검증 및 sanitize
- SQL 인젝션 방지를 위해 ORM 쿼리 사용
- XSS 방지를 위해 React의 기본 이스케이핑 활용

### 보안 검사 명령어
```bash
# Django 보안 체크
docker-compose exec backend python manage.py check --deploy

# 의존성 보안 취약점 검사
docker-compose exec backend pip-audit
docker-compose exec frontend npm audit
```

## 🐳 Docker 문제 해결

### 일반적인 Docker 문제
```bash
# 컨테이너가 시작되지 않을 때
docker-compose ps  # 상태 확인
docker-compose logs service_name  # 특정 서비스 로그

# 모든 컨테이너 재빌드
docker-compose down -v  # 볼륨 포함 삭제
docker-compose build --no-cache
docker-compose up -d

# 디스크 공간 정리
docker system prune -a  # 사용하지 않는 이미지, 컨테이너 삭제
docker volume prune  # 사용하지 않는 볼륨 삭제

# 특정 서비스만 로그 확인
docker-compose logs --tail=100 backend
docker-compose logs --since="10m" frontend

# 컨테이너 내부 프로세스 확인
docker-compose exec backend ps aux
docker-compose exec backend top
```

### 데이터베이스 연결 문제
```bash
# PostgreSQL 연결 테스트
docker-compose exec backend python manage.py dbshell

# 데이터베이스 직접 접속
docker-compose exec db psql -U resee_user -d resee_db

# 연결 상태 확인
docker-compose exec db pg_isready
```