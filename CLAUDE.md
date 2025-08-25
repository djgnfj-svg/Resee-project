# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🏗️ Project Overview
Resee is a smart review platform leveraging Ebbinghaus forgetting curve theory. Built with Django (backend) and React (frontend), managed via Docker Compose.

### Core Services
- **Backend**: Django REST Framework + PostgreSQL + Celery
- **Frontend**: React + TypeScript + TailwindCSS + TipTap Editor
- **AI Service**: Claude API (Anthropic)
- **Message Queue**: RabbitMQ (Celery broker)
- **Cache**: Redis
- **Reverse Proxy**: Nginx

## 🎯 Common Development Commands

### Starting Development Environment
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery
```

### Backend Commands
```bash
# Run migrations
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate

# Django shell
docker-compose exec backend python manage.py shell_plus

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Code formatting
docker-compose exec backend black .
docker-compose exec backend flake8
```

### Frontend Commands
```bash
# Run tests
docker-compose exec frontend npm test
docker-compose exec frontend npm test -- --watchAll=false
docker-compose exec frontend npm run test:coverage
docker-compose exec frontend npm run test:ci  # For CI environments

# Linting and type checking
docker-compose exec frontend npm run lint
docker-compose exec frontend npm run lint:fix
docker-compose exec frontend npm run typecheck

# Build and quick CI
docker-compose exec frontend npm run build
docker-compose exec frontend npm run ci:quick  # Typecheck + build
```

## 🏗️ Architecture Overview

### Backend Structure
```
backend/
├── accounts/           # User authentication, subscriptions, email service
├── content/           # Learning content management
├── review/            # Review scheduling system (Ebbinghaus algorithm)
├── ai_review/         # AI question generation and evaluation
├── analytics/         # Learning statistics and patterns
├── business_intelligence/ # Advanced analytics and user insights
├── monitoring/        # System monitoring and health checks
├── alerts/            # Alert system with Slack/Email notifications
├── legal/             # Terms, privacy policies, user data management
└── resee/             # Django settings and configuration
```

### Frontend Structure
```
frontend/src/
├── components/        # Reusable components
│   ├── analytics/    # BI dashboard, learning calendar, progress visualization
│   └── dashboard/    # Dashboard hero, stats cards, empty states
├── pages/            # Main application pages
├── contexts/         # Global state (Auth, Theme)
├── hooks/            # Custom React hooks (subscription, monitoring)
├── utils/            # API client utilities and helpers
├── types/            # TypeScript type definitions
└── styles/           # Global styles and animations
```

### Core Model Relationships
- User → Content (1:N)
- User → ReviewSchedule (1:N)
- Content → ReviewSchedule (1:1)
- Content → AIQuestion (1:N)
- User → Subscription (1:1)
- User → ReviewHistory (1:N)

### Review System Architecture
**Ebbinghaus Forgetting Curve Implementation**

1. **ReviewSchedule Model**: Manages review schedules per content
   - `interval_index`: Current review interval stage (0-7)
   - `next_review_date`: Next scheduled review
   - `initial_review_completed`: First review status

2. **ReviewHistory Model**: Tracks review performance
   - `result`: remembered/partial/forgot
   - `time_spent`: Time spent on review
   - Performance analysis for personalized learning patterns

3. **Subscription-based Limitations**:
   - Each tier has maximum review interval access
   - Overdue reviews filtered by subscription range
   - Automatic schedule adjustment on subscription change

4. **Review Intervals** (Ebbinghaus-based):
   - FREE: [1, 3] - Max 3 days
   - BASIC: [1, 3, 7, 14, 30, 60, 90] - Max 90 days
   - PRO: [1, 3, 7, 14, 30, 60, 120, 180] - Max 180 days

### API Authentication
- JWT (Access: 60 min, Refresh: 7 days with rotation)
- Email-based login with verification required
- Google OAuth 2.0 support
- Rate limiting by subscription tier (FREE: 500/hour, BASIC: 1000/hour, PRO: 2000/hour)

## 🔧 Important Debugging Commands

### Database Issues
```bash
# Check database connection
docker-compose exec backend python manage.py dbshell

# Reset specific app migrations
docker-compose exec backend python manage.py migrate app_name zero
docker-compose exec backend python manage.py migrate app_name

# Direct PostgreSQL access
docker-compose exec db psql -U resee_user -d resee_db
```

### Celery Task Debugging
```bash
# Monitor active tasks
docker-compose exec celery celery -A resee inspect active

# Check scheduled tasks
docker-compose exec celery celery -A resee inspect scheduled

# Purge task queue
docker-compose exec celery celery -A resee purge -Q celery
```

### React Query Cache Issues
```typescript
// Force cache invalidation
queryClient.invalidateQueries(['contents']);
queryClient.invalidateQueries(['learning-calendar']);
```

## 🌐 Environment Variables

### Required Backend Variables
- `ANTHROPIC_API_KEY`: Claude API key
- `GOOGLE_OAUTH2_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_OAUTH2_CLIENT_SECRET`: Google OAuth secret
- `ENFORCE_EMAIL_VERIFICATION`: Email verification requirement (default: False)

### Required Frontend Variables
- `REACT_APP_API_URL`: Backend API URL
- `REACT_APP_GOOGLE_CLIENT_ID`: Google OAuth client ID

## 📋 Core Workflows

### Content Creation Flow
```
User creates content → 
Django signal triggers → 
ReviewSchedule created → 
Immediate review available
```

### Review Process Flow
```
GET /api/review/today/ → 
Filter by subscription tier → 
User completes review → 
POST /api/review/complete/ → 
Update ReviewSchedule based on result:
  - remembered: next interval
  - partial: same interval
  - forgot: reset to day 1
```

### AI Question Generation Flow
```
Request generation → 
Check AIUsageTracking limits → 
Call Claude API → 
Store in AIQuestion model → 
Update usage tracking
```

### Subscription Change Flow
```
User changes tier → 
Django signal fires → 
adjust_review_schedules_on_subscription_change → 
Existing schedules auto-adjusted to new limits
```

### Business Intelligence Flow
```
User activity → 
BI analytics engine → 
Generate insights → 
Frontend BIDashboard displays → 
UserAnalytics provides recommendations
```

## 🚀 베타 배포

### 베타 배포 실행
```bash
# 환경변수 설정
cp .env.beta.example .env.beta
# .env.beta 파일 편집 (RDS URL, API 키 등)

# 배포 실행
chmod +x deploy-beta.sh
./deploy-beta.sh
```

### 베타 환경 특징
- **AWS RDS PostgreSQL**: 클라우드 데이터베이스
- **Docker Compose**: 간소화된 컨테이너 관리
- **보안 강화**: Rate limiting, SQL injection 방지
- **헬스체크**: 자동 서비스 상태 모니터링

## 🤖 AI Integration Architecture

### AI Service Structure (backend/ai_review/services/)
- **BaseAIService**: Core Claude API integration with retry logic
- **QuestionGenerator**: Creates multiple choice, fill-in-blank, and blur questions
- **AnswerEvaluator**: Scores user responses with detailed feedback

### Content Editor Integration
- **TipTap Editor**: Rich text editor with Notion-like functionality
- **Location**: `frontend/src/components/TipTapEditor.tsx`
- **Features**: Link support, placeholder text, starter kit extensions
- **Usage**: Integrated into ContentFormV2 for content creation

### AI Usage Limits by Tier
- FREE: 0 questions/day (no AI features)
- BASIC: 30 questions/day
- PRO: 200 questions/day (near unlimited)

### AI Model Configuration
- Primary: Claude 3 Haiku (fast, cost-effective)
- Request timeout: 30 seconds with exponential backoff
- Usage tracked via AIUsageTracking model

## 🧪 Testing Architecture

### Backend Testing
```bash
# Run all tests
docker-compose exec backend python -m pytest

# Run specific test file
docker-compose exec backend python -m pytest accounts/tests.py -v

# Run specific test method
docker-compose exec backend python -m pytest -k "test_name" -v

# Run with coverage
docker-compose exec backend python -m pytest --cov=. --cov-report=html

# Code quality checks
docker-compose exec backend black . --check
docker-compose exec backend flake8
```

### Frontend Testing (70% coverage threshold)
```bash
# Run all tests
docker-compose exec frontend npm test -- --watchAll=false

# Run specific test file
docker-compose exec frontend npm test ContentFormV2.test.tsx --watchAll=false

# Coverage report
docker-compose exec frontend npm run test:coverage

# CI mode (coverage + exit)
docker-compose exec frontend npm run test:ci

# Quick typecheck + build
docker-compose exec frontend npm run ci:quick
```

### Testing Environment
- Backend: SQLite in-memory database, mocked services, disabled migrations
- Frontend: React Testing Library + MSW for API mocking
- Coverage thresholds: 70% branches, functions, lines, statements

## 🔍 Key Design Principles

1. **Overdue Review Handling**: Missed reviews don't disappear, shown on current date
2. **Subscription-based Limits**: Each tier has access to specific review ranges
3. **Ebbinghaus Optimization**: Scientifically-based forgetting curve intervals (see /backend/review/utils.py)
4. **Real-time Adjustments**: Subscription changes auto-adjust existing schedules
5. **Performance**: TanStack Query for server state caching with immediate invalidation on changes
6. **Email Verification**: Required for subscription features and AI access
7. **Comprehensive Monitoring**: Alert system with Slack/Email notifications for system health

## 🚨 Alert System

### Quick Commands
```bash
# Test alert integrations
docker-compose exec backend python manage.py shell
>>> from alerts.services.metric_collector import MetricCollector
>>> collector = MetricCollector()
>>> collector.get_metric_value('cpu_usage', 5)

# Create alert rule via API
curl -X POST http://localhost:8000/api/alerts/rules/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"name":"High CPU","metric_name":"cpu_usage","condition":"gt","threshold_value":80}'

# Check Celery alert tasks
docker-compose exec celery celery -A resee inspect scheduled
```

### Key Features
- **24 Metric Types**: System, API, Database, AI, Business metrics
- **Flexible Conditions**: >, >=, <, <=, =, != with configurable time windows
- **Multi-channel Notifications**: Slack webhooks + Email alerts
- **Real-time Dashboard**: Monitoring overview at `/monitoring`
- **Alert Management**: Create/edit/resolve via API or admin interface

See `ALERT_SYSTEM_README.md` for comprehensive documentation.

## 🔄 Recent Architecture Changes

### Email System Consolidation
The email system has been consolidated into a single service:
- **Location**: `backend/accounts/email_service.py`
- **Models**: EmailLog, EmailTemplate
- **Service Class**: EmailService with template-based email sending
- **Celery Tasks**: send_verification_email_task with retry logic
- **Usage**: Import from `accounts.email_service` instead of separate modules

### Subscription Model Enhancement
Payment data is now stored directly in the Subscription model:
- **New Field**: `amount_paid` in `accounts.models.Subscription`
- **Usage**: Legal and BI services use subscription.amount_paid instead of separate payment records

### Removed Components
- **payments app**: Completely removed (unused by frontend)
- **Frontend monitoring components**: MonitoringDashboard and related components removed
- **Fragmented email files**: Consolidated into single service file

## 🎯 Key Development Guidelines

### Test Strategy
- Always run tests before committing: `docker-compose exec backend python -m pytest` and `docker-compose exec frontend npm run test:ci`
- Backend uses pytest with Django test database
- Frontend requires 70% test coverage threshold
- Use factory-boy for test data generation in backend

### Code Quality Standards
- Backend: Black formatting + Flake8 linting
- Frontend: ESLint + TypeScript strict mode
- All new features require corresponding tests
- Database changes require proper migrations

### Environment Management
- `.env` file for local development variables
- `.env.beta` for beta deployment configuration
- Testing environment uses in-memory databases and mocked services
- Production settings in `backend/resee/settings/production.py`

### Performance Considerations
- Use TanStack Query for API caching in frontend
- Review system optimized for subscription tier access patterns
- Celery workers handle background tasks (email, notifications, AI processing)
- Monitoring system tracks performance metrics automatically

## 📍 Important File Locations

### Core Business Logic
- **Ebbinghaus Algorithm**: `backend/review/utils.py`
- **Email Service**: `backend/accounts/email_service.py`
- **AI Question Generation**: `backend/ai_review/services/question_generator.py`
- **Business Intelligence**: `backend/business_intelligence/services/analytics_engine.py`
- **Alert System**: `backend/alerts/services/alert_engine.py`

### Frontend Key Components
- **TipTap Editor**: `frontend/src/components/TipTapEditor.tsx`
- **BI Dashboard**: `frontend/src/components/analytics/BIDashboard.tsx`
- **Learning Calendar**: `frontend/src/components/analytics/LearningCalendar.tsx`
- **Content Form**: `frontend/src/components/ContentFormV2.tsx`

### Configuration Files
- **Django Settings**: `backend/resee/settings/base.py`
- **Docker Compose**: `docker-compose.yml`
- **Frontend Config**: `frontend/package.json`, `frontend/tailwind.config.js`