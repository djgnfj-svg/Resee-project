# Resee Backend 기능 정의서

## 🏗️ 전체 구조 개요

Resee는 Ebbinghaus 망각곡선 이론을 활용한 스마트 복습 플랫폼으로, Django REST Framework 기반의 6개 주요 앱으로 구성되어 있습니다.

## 📁 Core Apps (6개)

### 🔐 accounts/ - 사용자 및 구독 관리
| 파일 | 기능 |
|------|------|
| `models.py` | User, Subscription, SubscriptionTier, AIUsageTracking 모델 정의 |
| `legal_models.py` | GDPR 준수를 위한 CookieConsent, UserConsent, LegalDocument 모델 |
| `views.py` | 사용자 인증, 프로필 관리, 비밀번호 변경 API |
| `legal_views.py` | GDPR 동의 관리, 데이터 내보내기/삭제 요청 API |
| `subscription_views.py` | 구독 업그레이드/다운그레이드, 결제 내역 조회 API |
| `serializers.py` | 사용자 관련 데이터 직렬화 |
| `legal_serializers.py` | GDPR 관련 데이터 직렬화 |
| `utils.py` | IP 주소/User-Agent 수집 통합 유틸리티 |
| `exceptions.py` | 계정 관련 커스텀 예외 클래스 및 표준화된 에러 처리 |
| `google_auth.py` | Google OAuth 2.0 인증 처리 |
| `billing_service.py` | 구독 결제 및 갱신 로직 |
| `email_service.py` | 이메일 발송 및 템플릿 관리 통합 서비스 |

### 🤖 ai_review/ - AI 기반 학습 지원
| 파일 | 기능 |
|------|------|
| `models.py` | AIQuestion, WeeklyTest, AdaptiveTest, InstantContentCheck 모델 |
| `services/base_ai_service.py` | Claude API 연동 및 재시도 로직 |
| `services/question_generator.py` | AI 기반 객관식/주관식/빈칸 문제 생성 |
| `services/answer_evaluator.py` | AI 기반 답변 채점 및 피드백 생성 |
| `services/chat_service.py` | AI 챗봇 대화 처리 |
| `views/weekly_test_views.py` | 주간 시험 생성, 시작, 답변 제출 API |
| `views/content_check_views.py` | 실시간 콘텐츠 이해도 체크, 품질 분석 API |
| `views/ai_tools_views.py` | AI 학습 도구, 분석, 스터디 메이트 API (개발 예정) |
| `views/evaluation_views.py` | AI 답변 평가 및 피드백 제공 API |
| `views/health_views.py` | AI 서비스 상태 확인 API |
| `views/question_views.py` | AI 문제 생성 및 관리 API |
| `serializers.py` | AI 관련 데이터 직렬화 |

### 📚 content/ - 학습 콘텐츠 관리  
| 파일 | 기능 |
|------|------|
| `models.py` | Content, Category 모델 정의 |
| `views.py` | 콘텐츠 CRUD, 카테고리 관리, 카테고리별 콘텐츠 조회 API |
| `serializers.py` | 콘텐츠 및 카테고리 데이터 직렬화 |
| `admin.py` | Django 관리자 패널 콘텐츠 관리 |

### 🔄 review/ - 복습 일정 관리 (Ebbinghaus 곡선)
| 파일 | 기능 |
|------|------|
| `models.py` | ReviewSchedule, ReviewHistory 모델 |
| `utils.py` | Ebbinghaus 복습 간격 계산 및 일정 관리 알고리즘 |
| `views.py` | 오늘의 복습, 복습 완료 처리, 일정 조회 API |
| `tasks.py` | 만료된 복습 정리 Celery 백그라운드 태스크 |
| `serializers.py` | 복습 관련 데이터 직렬화 |

### 📊 analytics/ - 학습 분석 및 BI
| 파일 | 기능 |
|------|------|
| `models.py` | LearningPattern, SubscriptionAnalytics, SystemUsageMetrics 모델 |
| `tasks.py` | 일일 학습 패턴 수집, 콘텐츠 효과성 분석 Celery 태스크 |
| `views.py` | 대시보드 데이터, 학습 통계, 카테고리별 성과 분석 API |
| `services/bi_service.py` | Business Intelligence 데이터 처리 서비스 |
| `serializers.py` | 분석 데이터 직렬화 |

### ⚙️ resee/ - 프로젝트 설정 및 인프라
| 파일 | 기능 |
|------|------|
| `settings/base.py` | 공통 Django 설정 (DB, REST Framework, JWT, Celery) |
| `settings/development.py` | 개발 환경 전용 설정 |
| `settings/production.py` | 운영 환경 전용 설정 |
| `urls.py` | 전체 API URL 라우팅 설정 |
| `health.py` | 시스템 상태 체크 (DB, Redis, AI 서비스) |
| `cache_utils.py` | Redis 캐시 유틸리티 |

## 🔧 주요 기능 및 특징

### 인증 & 보안
- JWT 기반 인증 (Access: 60분, Refresh: 7일 자동 갱신)
- Google OAuth 2.0 통합 인증
- GDPR 완전 준수 (동의 관리, 데이터 내보내기/삭제)
- 구독 티어별 Rate Limiting (FREE: 500/h, BASIC: 1000/h, PRO: 2000/h)

### 스마트 복습 시스템
- Ebbinghaus 망각곡선 기반 복습 간격 자동 계산
- 구독별 차별화된 복습 간격 (FREE: 3일, BASIC: 90일, PRO: 180일)
- 복습 성공률에 따른 동적 일정 조정
- 과거 복습 누락분 자동 관리

### AI 학습 지원
- Claude API 기반 문제 자동 생성 (객관식, 주관식, 빈칸)
- 실시간 콘텐츠 이해도 체크
- 적응형 주간 시험 시스템 (난이도 자동 조절)
- AI 기반 답변 평가 및 맞춤 피드백

### 구독 & 결제
- 4단계 구독 티어 (FREE/BASIC/PREMIUM/PRO)
- 자동 갱신 및 프로레이션 결제
- 구독 변경 시 기존 복습 일정 자동 조정
- 결제 내역 및 다음 결제일 관리

### 성능 최적화
- Redis 기반 세션 관리 및 캐싱
- select_related/prefetch_related DB 쿼리 최적화
- Celery 백그라운드 태스크 (분석, 정리 작업)
- Nginx 리버스 프록시 및 정적 파일 서빙

## 📈 최신 개선사항 (2024.09)

### 코드 구조 개선
- 대형 파일 기능별 분리 (799줄 → 3개 모듈)
- 중복 코드 제거 및 유틸리티 함수 통합
- 표준화된 예외 처리 패턴 도입

### 성능 최적화
- 데이터베이스 쿼리 N+1 문제 해결
- Type hints 추가로 코드 안정성 향상
- Import 구조 정리로 모듈 로딩 속도 개선

### 테스트 커버리지
- 새로운 유틸리티 함수 테스트 추가
- 분리된 모듈 독립성 테스트
- 커스텀 예외 처리 테스트

## 🚀 개발자 가이드

### 로컬 개발 환경 설정
```bash
# 개발 서버 시작
docker-compose up -d

# 마이그레이션 실행
docker-compose exec backend python manage.py migrate

# 테스트 실행
docker-compose exec backend python -m pytest
```

### API 문서
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/docs/redoc/`

### 주요 환경 변수
- `ANTHROPIC_API_KEY`: Claude AI API 키
- `GOOGLE_OAUTH2_CLIENT_ID/SECRET`: Google OAuth 설정
- `DJANGO_SECRET_KEY`: Django 암호화 키
- `DATABASE_URL`: PostgreSQL 연결 정보