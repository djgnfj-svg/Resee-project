# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Developer Role & Expertise
I am a Senior Full-Stack Web Developer with 8+ years of experience in building scalable, high-performance web applications. I have deep expertise in modern development practices, architectural patterns, and leading development teams.

### Development Approach
- **Test-Driven Development (TDD)** - Write tests first, then implement features
- **Clean Code Principles** - SOLID, DRY, KISS principles
- **Performance First** - Optimize for speed and scalability
- **Security by Design** - Implement security best practices from the start
- **Comprehensive Documentation** - Clear code documentation and architecture decisions

### Technical Standards
- **Code Coverage**: 90%+ unit test coverage
- **Type Safety**: Full TypeScript typing, Django type hints
- **Code Quality**: ESLint, Prettier, Black, isort, flake8
- **Performance Monitoring**: Application metrics and monitoring
- **Security**: OWASP Top 10 compliance, regular dependency updates

### Response Format for Development Tasks
When implementing features, I will provide:
1. **Architecture Overview** - System design and technical approach
2. **Implementation Strategy** - Step-by-step development plan with TDD
3. **Code Examples** - Production-ready code with tests
4. **Testing Strategy** - Unit, integration, and E2E test plans
5. **Deployment & DevOps** - CI/CD and infrastructure considerations

## Project Overview

**Resee** is a scientific review platform implementing spaced repetition learning based on the Ebbinghaus forgetting curve. It consists of a Django REST API backend with PostgreSQL/Redis/RabbitMQ and a React TypeScript frontend using Tiptap editor.

### v0.3 배포 준비 완료 (2025-07-18)
- **✅ 프론트엔드 빌드 오류 수정**: BlockNote 의존성 문제 해결, 커스텀 마크다운 에디터로 교체
- **✅ 백엔드 의존성 문제 해결**: `django-ipware` 라이브러리 추가, 미들웨어 설정 최적화
- **✅ 테스트 계정 생성**: admin, testuser, demo 계정 자동 생성 스크립트 완성
- **✅ 샘플 데이터**: 각 계정별 5개씩 총 16개 학습 콘텐츠 자동 생성
- **✅ 회원가입 에러 개선**: 한국어 상세 에러 메시지, 필드별 유효성 검사 강화
- **✅ 포괄적인 테스트 스위트**: 백엔드 203개 테스트, 프론트엔드/E2E 테스트 완성
- **✅ 보안 강화**: JWT 인증, CORS, 레이트 리미팅, SQL 인젝션 방지 미들웨어
- **✅ 코드 품질**: ESLint, Prettier, Black, TypeScript 타입 안전성 확보

### v0.2 Previous Updates
- **✅ Immediate Review Feature**: Content can be reviewed immediately after creation
- **✅ Initial Review Tracking**: Added `initial_review_completed` field to distinguish first reviews
- **✅ Enhanced Review Flow**: Seamless transition from immediate review to spaced repetition
- **✅ Playwright Testing**: Full workflow automated testing implemented

## Development Commands

### Docker Environment
```bash
# Start all services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild services
docker-compose build

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Backend (Django)
```bash
# Access backend container
docker-compose exec backend bash

# Database migrations
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Run tests
docker-compose exec backend python manage.py test
docker-compose exec backend pytest
docker-compose exec backend pytest --cov=.

# Django shell
docker-compose exec backend python manage.py shell

# Collect static files
docker-compose exec backend python manage.py collectstatic

# Run specific test file
docker-compose exec backend python manage.py test tests.test_content

# Run pytest with specific markers
docker-compose exec backend pytest -m unit
docker-compose exec backend pytest -m "not slow"

# Code quality checks
docker-compose exec backend flake8
docker-compose exec backend black .
docker-compose exec backend isort .

# Debug mode Django shell
docker-compose exec backend python manage.py shell_plus --ipython
```

### Frontend (React)
```bash
# Access frontend container
docker-compose exec frontend bash

# Install dependencies
docker-compose exec frontend npm install

# Run tests
docker-compose exec frontend npm test

# Build production
docker-compose exec frontend npm run build

# Run linting
docker-compose exec frontend npm run lint

# Test with coverage
docker-compose exec frontend npm test -- --coverage --watchAll=false

# Type checking
docker-compose exec frontend npx tsc --noEmit

# Build and analyze bundle size
docker-compose exec frontend npm run build -- --stats
```

### Celery (Background Tasks)
```bash
# Monitor celery worker
docker-compose exec celery celery -A resee worker -l info

# Monitor celery beat scheduler
docker-compose exec celery-beat celery -A resee beat -l info

# Celery monitoring (flower)
docker-compose exec celery celery -A resee flower

# Purge all tasks from queue
docker-compose exec celery celery -A resee purge -f

# Inspect active tasks
docker-compose exec celery celery -A resee inspect active

# Inspect scheduled tasks
docker-compose exec celery celery -A resee inspect scheduled
```

## Architecture Overview

### Backend (Django)
- **Django 4.2** with DRF for RESTful APIs
- **PostgreSQL** for main database
- **Redis** for caching and Celery results
- **RabbitMQ** for Celery message broker
- **JWT authentication** with SimpleJWT
- **Celery** for background tasks (review scheduling, notifications)

**Core Apps:**
- `accounts/` - User management with custom User model
- `content/` - Learning content with categories, tags, and image upload
- `review/` - Spaced repetition system with ReviewSchedule and ReviewHistory
- `analytics/` - Dashboard metrics and statistics

### Frontend (React + TypeScript)
- **React 18** with TypeScript for type safety
- **BlockNote** for notion-like rich text editing with real-time markdown rendering
- **React Query** for server state management
- **React Hook Form** for form validation
- **Tailwind CSS** for styling
- **Recharts** for data visualization

**Key Components:**
- `AuthContext` - Global authentication state
- `ProtectedRoute` - Route protection wrapper
- `ContentFormV2` - Content creation/editing with BlockNote editor
- `BlockNoteEditor` - Notion-like rich text editor with image support
- `Layout` - Main application layout with navigation

## Database Models

### Core Models
- **User** - Custom user with timezone and notification settings
- **Content** - Learning materials with title, markdown content, category, tags, priority
- **Category** - Per-user + global content categories
- **Tag** - Global content tags
- **ReviewSchedule** - Spaced repetition scheduling (intervals: 1, 3, 7, 14, 30 days)
- **ReviewHistory** - Review session records with results (remembered/partial/forgot)

### Key Relationships
- User has many Content, ReviewSchedule, ReviewHistory, Category
- Content belongs to Category, has many Tags (many-to-many)
- ReviewSchedule links User and Content with timing logic

## API Endpoints

### Authentication
- `POST /api/auth/token/` - Login (JWT)
- `POST /api/auth/token/refresh/` - Refresh JWT
- `POST /api/accounts/users/register/` - Register
- `GET/PUT /api/accounts/profile/` - Profile management

### Content Management
- `GET/POST /api/content/contents/` - Content CRUD
- `GET /api/content/contents/by_category/` - Grouped by category
- `GET/POST /api/content/categories/` - Category management
- `GET/POST /api/content/tags/` - Tag management
- `POST /api/content/upload-image/` - Image upload with optimization

### Review System
- `GET /api/review/today/` - Today's due reviews
- `POST /api/review/complete/` - Complete review session
- `GET /api/review/category-stats/` - Category statistics
- `GET /api/review/schedules/` - Review schedule management
- `GET /api/review/history/` - Review history

### Analytics
- `GET /api/analytics/dashboard/` - Dashboard overview
- `GET /api/analytics/review-stats/` - Review statistics

## Spaced Repetition Logic

**Review Intervals:** [immediate, 1, 3, 7, 14, 30] days

**Review Flow:**
1. **Immediate Review**: Content available for review immediately after creation (`initial_review_completed = false`)
2. **Spaced Repetition**: After first review completion, standard intervals apply

**Review Results:**
- **Remembered** - Advance to next interval
- **Partial** - Repeat current interval  
- **Forgot** - Reset to first interval (1 day)

**Background Tasks:**
- `create_review_schedule_for_content` - Auto-creates schedules with immediate availability
- `send_daily_review_notifications` - Daily 9AM reminders
- `cleanup_old_review_history` - Weekly cleanup of old history

## File Structure

```
resee/
├── backend/                 # Django backend
│   ├── accounts/           # User management
│   ├── content/            # Content management
│   ├── review/             # Spaced repetition system
│   ├── analytics/          # Statistics and analytics
│   ├── resee/              # Django project settings
│   └── tests/              # Test files
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── contexts/       # React contexts
│   │   ├── utils/          # Utilities (API client)
│   │   └── types/          # TypeScript types
│   └── public/             # Static assets
└── docker-compose.yml      # Docker services
```

## Development Notes

### Backend Patterns
- Use Django signals for automatic review schedule creation
- Celery tasks for background processing
- JWT tokens with automatic refresh
- Per-user data isolation with proper filtering
- Image optimization with Pillow (800x600 max, 85% quality)
- `initial_review_completed` field for immediate review tracking

### Frontend Patterns
- React Query for server state with caching
- Context API for global authentication state
- React Hook Form for form validation
- Tailwind CSS utility classes
- TypeScript interfaces for all data contracts
- Conditional rendering for "첫 번째 복습" vs "N번째 복습"

### Testing
- Backend: Django TestCase and pytest with factory-boy
- Frontend: React Testing Library with Jest
- E2E Testing: Playwright for full workflow testing
- Test database isolation and cleanup
- Test coverage with pytest-cov

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://resee_user:resee_password@db:5432/resee_db
CELERY_BROKER_URL=amqp://resee:resee_password@rabbitmq:5672//
CELERY_RESULT_BACKEND=redis://redis:6379/0
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,backend
```

### Frontend
```
REACT_APP_API_URL=http://localhost:8000/api
```

## Service URLs (Docker Development)
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api
- **Django Admin**: http://localhost:8000/admin
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

## 테스트 계정 정보

**자동 생성된 테스트 계정들:**

### 관리자 계정
- **사용자명**: `admin`
- **비밀번호**: `admin123!` 
- **이메일**: `admin@resee.com`
- **권한**: 슈퍼유저, Django 관리자 접근 가능

### 일반 사용자 계정
- **사용자명**: `testuser`
- **비밀번호**: `test123!`
- **이메일**: `test@resee.com` 
- **권한**: 일반 사용자

### 데모 계정
- **사용자명**: `demo`
- **비밀번호**: `demo123!`
- **이메일**: `demo@resee.com`
- **권한**: 일반 사용자

**자동 생성된 샘플 데이터:**
- 각 계정별 5개씩 총 **16개 학습 콘텐츠**
- **4개 카테고리**: 프로그래밍, 과학, 언어학습, 일반상식
- **샘플 콘텐츠**: Python 기초, 메모리 관리, 영어 불규칙동사, 뉴턴 법칙, 세계 수도 등

**테스트 계정 생성 명령어:**
```bash
# 테스트 계정 및 샘플 데이터 생성
docker-compose exec -T backend python create_test_accounts.py
```

## Korean Localization
- Default timezone: Asia/Seoul
- Korean language support in documentation
- User timezone setting in User model
- 회원가입/로그인 한국어 에러 메시지 지원
- 상세한 필드별 유효성 검사 메시지

## E2E Testing with Playwright

### Running E2E Tests
```bash
# Install Playwright browsers (first time only)
npx playwright install

# Run all E2E tests
npx playwright test

# Run specific test file
npx playwright test e2e/auth.spec.ts

# Run tests in headed mode (see browser)
npx playwright test --headed

# Run tests in UI mode (interactive)
npx playwright test --ui

# Debug a specific test
npx playwright test --debug

# Generate test reports
npx playwright show-report
```

### E2E Test Files
- `e2e/auth.spec.ts` - Login, registration, logout flows
- `e2e/content-management.spec.ts` - CRUD operations for learning content
- `e2e/review-workflow.spec.ts` - Spaced repetition review process

## API Documentation

### Interactive API Documentation
- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

### Quick API Testing
```bash
# Get JWT token
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "test123!"}'

# Use token for authenticated requests
curl -X GET http://localhost:8000/api/content/contents/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Debugging & Troubleshooting

### Container Management
```bash
# View all container logs
docker-compose logs

# Follow specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery

# Restart a specific service
docker-compose restart backend
docker-compose restart frontend

# Rebuild containers after dependency changes
docker-compose build --no-cache backend
docker-compose build --no-cache frontend

# Check container health
docker-compose ps
```

### Database Operations
```bash
# Access PostgreSQL directly
docker-compose exec db psql -U resee_user -d resee_db

# Backup database
docker-compose exec db pg_dump -U resee_user resee_db > backup.sql

# Reset database (CAUTION: destroys all data)
docker-compose exec backend python manage.py flush --no-input
docker-compose exec backend python manage.py migrate

# Show migration status
docker-compose exec backend python manage.py showmigrations

# Create empty migration
docker-compose exec backend python manage.py makemigrations --empty content

# Load test data
docker-compose exec -T backend python create_test_accounts.py
```

### Debugging Tools
```bash
# Django debug toolbar (available in DEBUG mode)
# Access at http://localhost:8000/__debug__/

# Interactive debugging with ipdb
# Add to code: import ipdb; ipdb.set_trace()

# Django shell with enhanced features
docker-compose exec backend python manage.py shell_plus

# Print SQL queries for a view
docker-compose exec backend python manage.py debugsqlshell

# Check Redis connection
docker-compose exec redis redis-cli ping

# Monitor Redis in real-time
docker-compose exec redis redis-cli monitor
```

### Common Issues & Solutions

**Frontend not updating:**
```bash
# Clear node_modules and reinstall
docker-compose exec frontend rm -rf node_modules
docker-compose exec frontend npm install

# Clear React cache
docker-compose exec frontend npm start -- --reset-cache
```

**Backend API errors:**
```bash
# Check for missing migrations
docker-compose exec backend python manage.py makemigrations --check

# Validate models
docker-compose exec backend python manage.py validate_models

# Check static files
docker-compose exec backend python manage.py findstatic admin/css/base.css
```

**Celery tasks not running:**
```bash
# Check RabbitMQ connection
docker-compose exec backend python -c "from resee.celery import app; print(app.control.inspect().active())"

# Manually trigger a task
docker-compose exec backend python manage.py shell
>>> from review.tasks import send_daily_review_notifications
>>> send_daily_review_notifications.delay()
```

## Quick Reference - Review Interface Keyboard Shortcuts
- **Space** or **Enter**: Show answer
- **1**: Forgot (review again tomorrow)
- **2**: Partial (review at same interval)
- **3**: Remembered (advance to next interval)
- **→** or **N**: Next review item