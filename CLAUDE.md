# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
docker-compose exec backend flake8
docker-compose exec frontend npm run lint

# 2. 전체 테스트 실행
docker-compose exec backend pytest
docker-compose exec frontend npm test -- --watchAll=false

# 3. 프로덕션 빌드 테스트
docker-compose exec frontend npm run build

# 4. 마이그레이션 확인
docker-compose exec backend python manage.py showmigrations
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

### 개발 환경
```bash
# 시작/중지
docker-compose up -d
docker-compose down

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend

# 쉘 접속
docker-compose exec backend bash
docker-compose exec frontend bash
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

# 프론트엔드
docker-compose exec frontend npm test
docker-compose exec frontend npm test -- --coverage
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

## 🏗️ 아키텍처 핵심 요약

### 백엔드 구조
```
backend/
├── accounts/      # 사용자, 구독 관리
├── content/       # 학습 콘텐츠
├── review/        # 복습 시스템
├── ai_review/     # AI 기능
└── resee/         # 설정
```

### 프론트엔드 구조
```
frontend/src/
├── components/    # 재사용 컴포넌트
├── pages/         # 페이지 컴포넌트
├── contexts/      # 전역 상태 (Auth)
├── utils/         # API 클라이언트
└── types/         # TypeScript 타입
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
```