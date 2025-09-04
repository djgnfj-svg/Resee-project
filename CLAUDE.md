# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🏗️ Project Overview
Resee is a smart review platform leveraging Ebbinghaus forgetting curve theory. Built with Django (backend) and React (frontend), managed via Docker Compose with multi-environment support.

### Core Services
- **Backend**: Django REST Framework + PostgreSQL + Celery
- **Frontend**: React + TypeScript + TailwindCSS + TipTap Editor
- **AI Service**: Claude API (Anthropic)
- **Message Queue**: RabbitMQ (Celery broker)
- **Cache**: Redis (cache + Celery results + sessions)
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

# Code formatting and linting
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

## 🚀 Production Deployment Commands

### Automated Deployment
```bash
# Full production deployment with SSL (auto-detects HTTP vs HTTPS)
./deploy-auto.sh yourdomain.com  # For domain with SSL
./deploy-auto.sh 192.168.1.100   # For IP with HTTP only

# Check deployment health
./scripts/check-deployment.sh

# Backup data before updates
./scripts/backup-data.sh

# Zero-downtime updates
./scripts/update-deployment.sh

# SSL certificate renewal
sudo certbot renew && docker-compose restart nginx
```

### Docker Environment Files
- **Development**: `docker-compose.yml` - Hot-reload, direct ports
- **Production**: `docker-compose.prod.yml` - Gunicorn, optimized builds
- **SSL Production**: `docker-compose.ssl.yml` - HTTPS with Let's Encrypt

## 🏗️ Architecture Overview

### Backend Structure
```
backend/
├── accounts/           # User authentication, subscriptions, email service
├── content/           # Learning content management
├── review/            # Review scheduling system (Ebbinghaus algorithm)
├── ai_review/         # AI question generation and evaluation
├── analytics/         # Learning statistics and patterns
├── monitoring/        # System monitoring and health checks
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

### Scripts Directory
```
scripts/
├── backup-data.sh         # Comprehensive data backup
├── check-deployment.sh    # Health check and monitoring
└── update-deployment.sh   # Zero-downtime updates
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
- `DJANGO_ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `CSRF_TRUSTED_ORIGINS`: Comma-separated list of trusted origins

### Required Frontend Variables
- `REACT_APP_API_URL`: Backend API URL
- `REACT_APP_GOOGLE_CLIENT_ID`: Google OAuth client ID

### Monitoring Variables (Optional)
- `SLACK_WEBHOOK_URL`: Slack integration for alerts
- `SLACK_DEFAULT_CHANNEL`: Default channel for notifications
- `ALERT_SUMMARY_RECIPIENTS`: Email recipients for alert summaries
- `SENTRY_DSN`: Error tracking integration

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

## 🤖 AI Integration Architecture

### AI Features Overview
Resee integrates 3 core AI features using Claude API for enhanced learning:

1. **Weekly Tests**: Adaptive difficulty testing with category-based questions
2. **Content Quality Check**: Real-time content analysis and feedback
3. **Explanation Evaluation**: AI-powered descriptive review assessment

### AI Service Structure (backend/ai_review/services/)
- **BaseAIService**: Core Claude API integration with retry logic
- **QuestionGenerator**: Creates multiple choice, fill-in-blank, and blur questions
- **AnswerEvaluator**: Scores user responses with detailed feedback

### AI API Endpoints
```
/api/ai-review/
├── weekly-test/start/           # Start adaptive weekly test
├── weekly-test/answer/          # Submit test answers
├── content-check/               # Content quality analysis
├── explanation-evaluation/      # Evaluate user explanations
└── instant-check/              # Alternative content check
```

### Content Editor Integration
- **TipTap Editor**: Rich text editor with Notion-like functionality
- **Location**: `frontend/src/components/TipTapEditor.tsx`
- **Features**: Link support, placeholder text, starter kit extensions
- **Usage**: Integrated into ContentFormV2 for content creation

### AI Usage Limits by Tier
- **FREE**: No AI features (upgrade required)
- **BASIC**: 30 AI requests/day (weekly tests, content checks, explanations)
- **PRO**: 200 requests/day (near unlimited usage)

### Review Mode Architecture
The review system now supports dual modes:

1. **Card Mode (All Tiers)**: 
   - Traditional flip-card interface
   - Show/hide content functionality
   - Self-assessment (remembered/partial/forgot)

2. **Explanation Mode (BASIC+)**:
   - User writes explanation in text area
   - AI evaluates explanation quality (0-100 score)
   - Detailed feedback with strengths/improvements
   - Concept coverage analysis
   - Original content comparison

### AI Model Configuration
- Primary: Claude 3 Haiku (fast, cost-effective)
- Request timeout: 30 seconds with exponential backoff
- Usage tracked via AIUsageTracking model
- Mock responses available for development (`AI_USE_MOCK_RESPONSES=True`)

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
- CI/CD: GitHub Actions with conditional testing and health checks

## 🔐 Security Features

### Production Security
- **SSL/TLS**: Automated Let's Encrypt certificate management
- **Firewall**: UFW configuration with essential ports only
- **Security Headers**: HSTS, CSP, X-Frame-Options, X-Content-Type-Options
- **Rate Limiting**: Multi-tier API throttling by subscription
- **CSRF Protection**: Domain-based CSRF validation
- **Session Security**: Redis-backed sessions with secure cookies

### Deployment Security
```bash
# The deploy-auto.sh script automatically configures:
- UFW firewall rules
- Nginx security headers
- SSL certificate provisioning
- HTTP to HTTPS redirect
- Rate limiting per IP
```

## 📊 Monitoring & Analytics

### System Monitoring
- **Health Checks**: Multi-service health monitoring endpoints
- **Performance Tracking**: Slow query detection, memory usage alerts
- **Alert System**: Slack/Email notifications for critical events
- **Automated Cleanup**: Old data purging with configurable retention

### Business Intelligence
- **Learning Pattern Analysis**: Daily automated collection
- **Content Effectiveness**: Performance-based optimization metrics
- **Subscription Analytics**: Revenue and usage patterns
- **System Metrics**: Infrastructure monitoring and alerts

## 🔍 Key Design Principles

1. **Overdue Review Handling**: Missed reviews don't disappear, shown on current date
2. **Subscription-based Limits**: Each tier has access to specific review ranges
3. **Ebbinghaus Optimization**: Scientifically-based forgetting curve intervals
4. **Real-time Adjustments**: Subscription changes auto-adjust existing schedules
5. **Performance**: TanStack Query for server state caching with immediate invalidation
6. **Email Verification**: Required for subscription features and AI access
7. **Clean Architecture**: Service layer abstraction, signal-based coordination
8. **Scalability**: Horizontal scaling with Gunicorn workers and Celery

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

### AI System Completion (Latest)
All 3 core AI features are now fully implemented and integrated:
- **Weekly Tests**: Complete with adaptive difficulty and category support
- **Content Quality Check**: NEW endpoint `/ai-review/content-check/` added
- **Explanation Evaluation**: Integrated into review page with dual-mode interface
- **Frontend Integration**: Review page supports card/explanation toggle with subscription gating

### Removed Components
- **payments app**: Completely removed (unused by frontend)
- **Frontend monitoring components**: MonitoringDashboard and related components removed
- **Fragmented email files**: Consolidated into single service file

## 📍 Important File Locations

### Core Business Logic
- **Ebbinghaus Algorithm**: `backend/review/utils.py`
- **Email Service**: `backend/accounts/email_service.py`
- **AI Question Generation**: `backend/ai_review/services/question_generator.py`
- **AI Content Quality Check**: `backend/ai_review/views/test_views.py` (ContentQualityCheckView)
- **Alert System**: `backend/monitoring/services/alert_engine.py`
- **Deployment Script**: `deploy-auto.sh`

### AI Integration Files
- **AI Views**: `backend/ai_review/views/test_views.py`
- **AI URLs**: `backend/ai_review/urls.py`
- **AI API Client**: `frontend/src/utils/ai-review-api.ts`
- **AI Types**: `frontend/src/types/ai-review.ts`

### Frontend Key Components
- **Review Page**: `frontend/src/pages/ReviewPage.tsx` (dual-mode review system)
- **TipTap Editor**: `frontend/src/components/TipTapEditor.tsx`
- **BI Dashboard**: `frontend/src/components/analytics/BIDashboard.tsx`
- **Learning Calendar**: `frontend/src/components/analytics/LearningCalendar.tsx`
- **Content Form**: `frontend/src/components/ContentFormV2.tsx`

### Configuration Files
- **Django Settings**: `backend/resee/settings/base.py`
- **Docker Compose**: `docker-compose.yml`, `docker-compose.prod.yml`, `docker-compose.ssl.yml`
- **Frontend Config**: `frontend/package.json`, `frontend/tailwind.config.js`
- **CI/CD Pipeline**: `.github/workflows/ci.yml`