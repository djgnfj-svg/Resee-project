# 🛠️ Resee 개발자 가이드

## 📋 목차
1. [프로젝트 개요](#-프로젝트-개요)
2. [개발 환경 설정](#-개발-환경-설정)
3. [아키텍처 상세](#-아키텍처-상세)
4. [핵심 기능 구현](#-핵심-기능-구현)
5. [API 문서](#-api-문서)
6. [테스팅 가이드](#-테스팅-가이드)
7. [배포 가이드](#-배포-가이드)
8. [트러블슈팅](#-트러블슈팅)

---

## 🎯 프로젝트 개요

### 기술 스택
- **Backend**: Django 4.2 + Django REST Framework + PostgreSQL
- **Frontend**: React 18 + TypeScript + TailwindCSS + TanStack Query
- **AI**: Anthropic Claude API
- **Queue**: RabbitMQ + Celery
- **Cache**: Redis
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions

### 프로젝트 구조
```
Resee/
├── backend/                 # Django 백엔드
│   ├── accounts/           # 사용자 인증 및 구독 관리
│   ├── content/           # 학습 콘텐츠 관리
│   ├── review/            # 복습 시스템 (에빙하우스)
│   ├── ai_review/         # AI 문제 생성 및 평가
│   ├── analytics/         # 학습 분석 및 통계
│   ├── monitoring/        # 시스템 모니터링
│   └── resee/            # Django 설정
├── frontend/              # React 프론트엔드
│   ├── src/
│   │   ├── components/   # 재사용 컴포넌트
│   │   ├── pages/       # 페이지 컴포넌트
│   │   ├── hooks/       # 커스텀 훅
│   │   ├── contexts/    # 전역 상태
│   │   ├── utils/       # 유틸리티 함수
│   │   └── types/       # TypeScript 타입 정의
├── nginx/                # Nginx 설정
├── docker-compose.yml    # 개발 환경
└── .github/workflows/    # CI/CD 파이프라인
```

---

## 🚀 개발 환경 설정

### 필수 요구사항
- **Docker** 및 **Docker Compose**
- **Node.js** 18+ (프론트엔드 개발 시)
- **Python** 3.11+ (백엔드 개발 시)

### 1. 저장소 클론 및 환경 변수 설정
```bash
git clone https://github.com/djgnfj-svg/Resee-project.git
cd Resee-project

# 환경 변수 파일 생성
cp .env.example .env
# .env 파일에서 실제 값으로 수정
```

### 2. Docker 개발 환경 시작
```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend

# 서비스 상태 확인
docker-compose ps
```

### 3. 개발 서버 접속
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api
- **Django Admin**: http://localhost:8000/admin

### 4. 초기 데이터 설정
```bash
# 데이터베이스 마이그레이션
docker-compose exec backend python manage.py migrate

# 슈퍼유저 생성
docker-compose exec backend python manage.py createsuperuser

# 테스트 데이터 생성 (선택사항)
docker-compose exec backend python manage.py loaddata fixtures/test_data.json
```

---

## 🏗️ 아키텍처 상세

### 백엔드 아키텍처

#### Django Apps 구성
```python
DJANGO_APPS = [
    'accounts',      # 사용자, 인증, 구독
    'content',       # 학습 콘텐츠
    'review',        # 복습 시스템
    'ai_review',     # AI 기능
    'analytics',     # 학습 분석
    'monitoring',    # 시스템 모니터링
]
```

#### 데이터베이스 설계
```sql
-- 핵심 테이블 관계
User (1:1) → Subscription
User (1:N) → Content
Content (1:1) → ReviewSchedule  
User (1:N) → ReviewHistory
Content (1:N) → AIQuestion
```

#### API 인증 시스템
```python
# JWT 설정
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# Rate Limiting (구독별)
RATE_LIMIT_TIERS = {
    'free': {'hour': 500},
    'basic': {'hour': 1000}, 
    'pro': {'hour': 2000}
}
```

### 프론트엔드 아키텍처

#### 상태 관리
```typescript
// 전역 상태 (Context API)
- AuthContext: 사용자 인증 상태
- ThemeContext: 다크/라이트 모드

// 서버 상태 (TanStack Query)
- useContents(): 콘텐츠 목록
- useReviewToday(): 오늘의 복습
- useAnalytics(): 학습 분석 데이터
```

#### 컴포넌트 구조
```
components/
├── common/           # 공통 컴포넌트
├── forms/           # 폼 컴포넌트
├── layout/          # 레이아웃 컴포넌트
├── analytics/       # 분석 대시보드
└── dashboard/       # 메인 대시보드
```

---

## 🔧 핵심 기능 구현

### 1. 에빙하우스 망각곡선 복습 시스템

#### 복습 간격 정의
```python
# backend/review/utils.py
REVIEW_INTERVALS = {
    'free': [1, 3],  # 최대 3일
    'basic': [1, 3, 7, 14, 30, 60, 90],  # 최대 90일
    'pro': [1, 3, 7, 14, 30, 60, 120, 180],  # 최대 180일
}

def calculate_next_review(current_interval_index, result, user_tier):
    intervals = REVIEW_INTERVALS[user_tier]
    
    if result == 'remembered':
        # 다음 단계로
        next_index = min(current_interval_index + 1, len(intervals) - 1)
    elif result == 'partial':
        # 현재 단계 유지  
        next_index = current_interval_index
    else:  # forgot
        # 첫 단계로 리셋
        next_index = 0
    
    return intervals[next_index], next_index
```

#### 복습 스케줄 생성
```python
# backend/review/signals.py
@receiver(post_save, sender=Content)
def create_review_schedule(sender, instance, created, **kwargs):
    if created:
        ReviewSchedule.objects.create(
            user=instance.author,
            content=instance,
            next_review_date=timezone.now().date() + timedelta(days=1),
            interval_index=0
        )
```

### 2. AI 문제 생성 시스템

#### Claude API 통합
```python
# backend/ai_review/services/base_ai_service.py
class BaseAIService:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )
    
    def call_claude(self, prompt, max_tokens=1000):
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
```

#### 문제 생성 프롬프트
```python
# backend/ai_review/services/question_generator.py
def generate_multiple_choice_prompt(self, content):
    return f"""
다음 학습 내용을 바탕으로 객관식 문제를 생성해주세요.

학습 내용:
{content.content}

요구사항:
1. 4지선다 문제 1개
2. 정답은 반드시 포함
3. 오답도 그럴듯해야 함
4. JSON 형식으로 응답

응답 형식:
{{
    "question": "문제 내용",
    "options": ["선택지1", "선택지2", "선택지3", "선택지4"],
    "correct_answer": 0,
    "explanation": "해설"
}}
"""
```

### 3. 구독 및 사용량 제한

#### 미들웨어 기반 Rate Limiting
```python
# backend/resee/middleware.py
class RateLimitMiddleware:
    def process_request(self, request):
        if not request.user.is_authenticated:
            return self._check_ip_limits(request)
        
        user_tier = self._get_user_tier(request.user)
        return self._check_user_limits(request, user_tier)
    
    def _check_user_limits(self, request, tier):
        limits = self.TIER_LIMITS[tier]
        cache_key = f"rate_limit:user:{request.user.id}:hour"
        
        if self._is_rate_limited(cache_key, limits['hour'], 3600):
            return self._create_rate_limit_response(
                f"{tier} 구독 시간당 요청 한도 초과"
            )
```

#### AI 사용량 추적
```python
# backend/ai_review/models.py
class AIUsageTracking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    questions_generated = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'date']
```

### 4. 학습 분석 시스템

#### 학습 패턴 분석
```python
# backend/analytics/tasks.py
@shared_task
def collect_learning_patterns():
    """일일 학습 패턴 수집 및 분석"""
    
    for user in User.objects.filter(is_active=True):
        # 복습 완료율 계산
        reviews_today = ReviewHistory.objects.filter(
            user=user,
            reviewed_at__date=timezone.now().date()
        )
        
        completion_rate = calculate_completion_rate(user)
        memory_accuracy = calculate_memory_accuracy(reviews_today)
        
        # 학습 패턴 저장
        LearningPattern.objects.update_or_create(
            user=user,
            date=timezone.now().date(),
            defaults={
                'completion_rate': completion_rate,
                'memory_accuracy': memory_accuracy,
                'total_reviews': reviews_today.count()
            }
        )
```

---

## 📡 API 문서

### 인증 API
```
POST /api/auth/login/
POST /api/auth/register/  
POST /api/auth/refresh/
POST /api/auth/logout/
GET  /api/auth/user/
```

### 콘텐츠 API
```
GET    /api/content/contents/         # 콘텐츠 목록
POST   /api/content/contents/         # 콘텐츠 생성
GET    /api/content/contents/{id}/    # 콘텐츠 상세
PUT    /api/content/contents/{id}/    # 콘텐츠 수정
DELETE /api/content/contents/{id}/    # 콘텐츠 삭제
GET    /api/content/categories/       # 카테고리 목록
```

### 복습 API
```
GET  /api/review/today/              # 오늘의 복습
POST /api/review/complete/           # 복습 완료
GET  /api/review/history/            # 복습 기록
GET  /api/review/calendar/{date}/    # 캘린더 데이터
```

### AI 문제 API
```
POST /api/ai-review/generate-questions/    # 문제 생성
GET  /api/ai-review/questions/{id}/        # 문제 조회
POST /api/ai-review/submit-answer/         # 답안 제출
GET  /api/ai-review/usage/                 # 사용량 확인
```

### 분석 API
```
GET /api/analytics/dashboard/        # 대시보드 데이터
GET /api/analytics/learning-calendar/ # 학습 캘린더
GET /api/analytics/patterns/         # 학습 패턴
```

---

## 🧪 테스팅 가이드

### 백엔드 테스트

#### 테스트 실행
```bash
# 모든 테스트
docker-compose exec backend python -m pytest

# 특정 앱 테스트
docker-compose exec backend python -m pytest accounts/

# 커버리지 포함
docker-compose exec backend python -m pytest --cov=. --cov-report=html
```

#### 테스트 설정
```python
# backend/pytest.ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = resee.settings.testing
python_files = tests.py test_*.py *_tests.py
testpaths = accounts content review ai_review analytics monitoring
addopts = --tb=short --disable-warnings -v
```

#### 테스트 예시
```python
# backend/accounts/tests.py
class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
    
    def test_user_str_representation(self):
        user = User(email='test@example.com')
        self.assertEqual(str(user), 'test@example.com')
```

### 프론트엔드 테스트

#### 테스트 실행
```bash
# 모든 테스트
docker-compose exec frontend npm test -- --watchAll=false

# 커버리지 포함
docker-compose exec frontend npm run test:coverage

# CI 모드 (커버리지 + 종료)
docker-compose exec frontend npm run test:ci
```

#### 테스트 설정
```javascript
// frontend/jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
};
```

#### 테스트 예시
```typescript
// frontend/src/components/ContentForm.test.tsx
describe('ContentForm', () => {
  test('renders form fields correctly', () => {
    render(<ContentForm />);
    
    expect(screen.getByLabelText(/제목/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/내용/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/카테고리/i)).toBeInTheDocument();
  });
  
  test('submits form with valid data', async () => {
    const mockOnSubmit = jest.fn();
    render(<ContentForm onSubmit={mockOnSubmit} />);
    
    await userEvent.type(screen.getByLabelText(/제목/i), 'Test Title');
    await userEvent.click(screen.getByRole('button', { name: /저장/i }));
    
    expect(mockOnSubmit).toHaveBeenCalledWith({
      title: 'Test Title',
      // ...
    });
  });
});
```

### CI/CD 파이프라인

#### GitHub Actions 워크플로우
```yaml
# .github/workflows/ci.yml
name: Resee CI - Backend Only

on:
  push:
    branches: [ main, develop ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-django pytest-cov
        
    - name: Run tests
      run: |
        cd backend
        python -m pytest accounts/tests.py::UserModelTest -v
      env:
        DJANGO_SETTINGS_MODULE: resee.settings.testing
        SECRET_KEY: test-secret-key-for-ci
```

---

## 🚀 배포 가이드

### Docker 프로덕션 빌드
```bash
# 프로덕션 환경 변수 설정
cp .env.example .env.prod
# 실제 프로덕션 값으로 수정

# 프로덕션 빌드 및 실행
docker-compose -f docker-compose.prod.yml up -d --build
```

### 환경 변수 설정
```bash
# 필수 프로덕션 환경 변수
SECRET_KEY=your-super-secret-production-key
DEBUG=False
ANTHROPIC_API_KEY=your-anthropic-api-key
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://redis:6379/0
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
```

### Nginx 설정
```nginx
# nginx/nginx.conf
server {
    listen 80;
    server_name yourdomain.com;
    
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
    }
}
```

### 데이터베이스 마이그레이션
```bash
# 프로덕션 마이그레이션
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# 정적 파일 수집
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

---

## 🔍 트러블슈팅

### 자주 발생하는 문제들

#### 1. 데이터베이스 연결 오류
```bash
# 문제: psycopg2 설치 오류
# 해결: 시스템 의존성 설치
sudo apt-get install postgresql-dev python3-dev

# 문제: 데이터베이스 접근 권한 오류
# 해결: PostgreSQL 권한 확인
docker-compose exec db psql -U resee_user -d resee_db
```

#### 2. Redis 연결 오류
```bash
# Redis 서비스 상태 확인
docker-compose exec redis redis-cli ping

# Redis 메모리 사용량 확인
docker-compose exec redis redis-cli info memory
```

#### 3. Celery 작업 오류
```bash
# Celery 워커 상태 확인
docker-compose exec celery celery -A resee inspect active

# 작업 큐 상태 확인
docker-compose exec celery celery -A resee inspect scheduled
```

#### 4. 프론트엔드 빌드 오류
```bash
# 노드 모듈 재설치
docker-compose exec frontend rm -rf node_modules package-lock.json
docker-compose exec frontend npm install

# TypeScript 컴파일 확인
docker-compose exec frontend npm run typecheck
```

### 성능 최적화

#### 데이터베이스 쿼리 최적화
```python
# N+1 쿼리 해결
contents = Content.objects.select_related('category', 'author').all()

# 불필요한 필드 제외
users = User.objects.only('email', 'first_name', 'last_name')

# 인덱스 추가
class Content(models.Model):
    created_at = models.DateTimeField(db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['author', 'created_at']),
        ]
```

#### 캐시 활용
```python
# Redis 캐시 설정
from django.core.cache import cache

@cached_method(timeout=300, key_prefix='user_contents')
def get_user_contents(user_id):
    return Content.objects.filter(author_id=user_id)

# TanStack Query 캐시
const { data: contents } = useQuery({
  queryKey: ['contents', userId],
  queryFn: () => fetchUserContents(userId),
  staleTime: 5 * 60 * 1000, // 5분
});
```

### 로깅 및 모니터링

#### Django 로깅 설정
```python
# settings/base.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

#### 모니터링 엔드포인트
```python
# backend/monitoring/views.py
@api_view(['GET'])
def health_check(request):
    """시스템 상태 확인"""
    checks = {
        'database': check_database_connection(),
        'redis': check_redis_connection(),
        'celery': check_celery_workers(),
        'disk_space': check_disk_space(),
    }
    
    status_code = 200 if all(checks.values()) else 503
    return Response(checks, status=status_code)
```

---

## 📚 추가 리소스

### 공식 문서
- [Django Documentation](https://docs.djangoproject.com/)
- [React Documentation](https://react.dev/)
- [TanStack Query](https://tanstack.com/query/latest)
- [Anthropic Claude API](https://docs.anthropic.com/)

### 커뮤니티
- **GitHub Issues**: 버그 리포트 및 기능 요청
- **Wiki**: 상세한 기술 문서
- **Discussions**: 개발 관련 토론

### 기여하기
1. **Fork** 저장소
2. **Feature branch** 생성 (`git checkout -b feature/amazing-feature`)
3. **Commit** 변경사항 (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Pull Request** 생성

---

*이 가이드는 지속적으로 업데이트됩니다. 
최신 정보는 공식 저장소에서 확인하세요.*

**🚀 Happy Coding with Resee! 🎓**