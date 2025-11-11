# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Table of Contents
1. [Quick Start](#quick-start) - Get started in 5 minutes
2. [Core Concepts](#core-concepts) - Understand the domain
3. [Development Workflow](#development-workflow) - Daily commands and tasks
4. [System Architecture](#system-architecture) - Technical structure
5. [AI Services](#ai-services) - Anthropic Claude integration details
6. [Reference](#reference) - Detailed specifications
7. [Recent Changes](#recent-changes) - Latest updates

---

## Quick Start

### Project Overview
Resee is a focused spaced repetition learning platform implementing the Ebbinghaus forgetting curve theory. Built with Django (backend) and React (frontend).

**Key Philosophy**: Pure learning effectiveness over engagement metrics. No streaks, achievements, or gamification - just scientifically-proven spaced repetition for optimal knowledge retention.

**Deployment**:
- **Development**: Docker Compose (local development)
- **Production**: AWS ECS (backend), Vercel (frontend)

### Access URLs

**Production**:
- Frontend: Vercel deployment
- Backend API: AWS ALB (resee-alb-64869428.ap-northeast-2.elb.amazonaws.com)
- Health Check: http://resee-alb-64869428.ap-northeast-2.elb.amazonaws.com/api/health/

**Development (Local)**:
```bash
# Nginx (Recommended - production-like)
http://localhost

# Development servers
http://localhost:3000     # React dev server
http://localhost:8000/api # Django API
http://localhost:8000/admin
```

### Test Accounts

**Development**:
- Admin: `admin@resee.com` / `admin123!` (PRO, 180-day intervals)
- Email Test: `djgnfj8923@naver.com` / `testpassword123` (BASIC, 90-day)
- MCP Test: `mcptest@example.com` / `mcptest123!` (FREE, 3-day)

### Start Development
```bash
docker-compose up -d
docker-compose logs -f backend
```

---

## Core Concepts

### Ebbinghaus Spaced Repetition

The system implements scientifically-proven intervals for optimal memory retention:

**Subscription Tiers & Intervals**:
- **FREE**: [1, 3 days]
- **BASIC**: [1, 3, 7, 14, 30, 60, 90 days]
- **PRO**: [1, 3, 7, 14, 30, 60, 120, 180 days]

**Core Algorithm**: `backend/review/utils.py:calculate_next_review_date()`

### Domain Flow

```
1. Content Creation
   User creates content
   → Django signal triggers (content/signals.py)
   → ReviewSchedule auto-created
   → Available for review next day

2. Review Process
   User submits review
   → Update interval_index
   → Calculate next review date (Ebbinghaus curve)
   → Store review history
   → Update analytics

3. Subscription Check
   Review submission
   → Check user tier
   → Validate interval_index within tier limits
   → Apply tier-specific intervals
```

### Key Models

- **User**: Email-based authentication with hashed verification tokens (SHA-256)
- **Content**: User-created learning material with AI validation
- **ReviewSchedule**: Tracks next review date, interval_index, initial_review_completed
- **ReviewHistory**: Performance records with AI scoring
- **Subscription**: User tier (FREE/BASIC/PRO), billing cycles, auto-renewal
- **PaymentHistory**: Payment records (upgrade/downgrade/cancellation) with gateway IDs
- **BillingSchedule**: Automated billing schedules for renewals
- **NotificationPreference**: Email notification settings with unsubscribe tokens

---

## Development Workflow

### Common Commands

#### Start/Stop Services (Local Development)
```bash
docker-compose up -d
docker-compose down
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery
docker-compose logs -f celery-beat
```

#### Production Commands (AWS)
```bash
# Check ECS cluster status
aws ecs list-clusters
aws ecs list-services --cluster resee-cluster

# Check service status
aws ecs describe-services --cluster resee-cluster --services resee-backend-service resee-celery-worker-service resee-celery-beat-service

# Check task status
aws ecs list-tasks --cluster resee-cluster --service-name resee-backend-service
aws ecs describe-tasks --cluster resee-cluster --tasks <task-id>

# Check service events
aws ecs describe-services --cluster resee-cluster --services resee-backend-service --query 'services[0].events[:5]'

# Check ALB status
aws elbv2 describe-load-balancers --names resee-alb
aws elbv2 describe-target-groups --target-group-arns <target-group-arn>

# Test backend health
curl http://resee-alb-64869428.ap-northeast-2.elb.amazonaws.com/api/health/
curl http://resee-alb-64869428.ap-northeast-2.elb.amazonaws.com/api/health/detailed/
```

#### Backend Development
```bash
# Migrations
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate

# Tests
docker-compose exec backend python -m pytest
docker-compose exec backend python -m pytest --cov=. --cov-report=html

# Shell
docker-compose exec backend python manage.py shell_plus

# Management Commands
docker-compose exec backend python manage.py create_initial_users
docker-compose exec backend python manage.py health_check
docker-compose exec backend python manage.py rate_limit_status

# Formatting
docker-compose exec backend black .
```

#### Frontend Development
```bash
# Tests
docker-compose exec frontend npm test -- --watchAll=false
docker-compose exec frontend npm run test:coverage

# Linting (REQUIRED before commit)
docker-compose exec frontend npm run lint
docker-compose exec frontend npm run typecheck

# Build & Analysis
docker-compose exec frontend npm run build
docker-compose exec frontend npm run analyze  # Bundle size analysis
```

### Key File Locations

#### Backend Critical Files
```
backend/
├── review/
│   ├── utils.py                       # Ebbinghaus algorithm, interval calculations
│   ├── ai_evaluation.py               # AI answer evaluation (claude-3-haiku)
│   ├── tasks.py                       # Email reminder tasks
│   ├── backup_tasks.py                # Automated database backups
│   └── services.py                    # Review business logic
├── content/
│   ├── signals.py                     # ReviewSchedule auto-creation
│   └── ai_validation.py               # AI content validation (claude-3-5-sonnet)
├── accounts/
│   ├── models.py                      # User, Subscription, PaymentHistory, BillingSchedule
│   ├── auth/
│   │   ├── views.py                   # JWT login/logout/refresh
│   │   ├── authentication.py          # JWT authentication classes
│   │   └── middleware.py              # Auth middleware
│   ├── subscription/
│   │   ├── toss_service.py            # Toss Payments API integration
│   │   ├── subscription_views.py      # Payment APIs (checkout, confirm, webhook)
│   │   ├── billing_service.py         # Billing schedule automation
│   │   └── services.py                # Subscription & permission logic
│   ├── email/
│   │   ├── email_service.py           # Email sending logic
│   │   └── email_views.py             # Verification endpoints
│   ├── health/
│   │   ├── health_views.py            # Health check endpoints
│   │   ├── monitoring_views.py        # Monitoring endpoints
│   │   └── log_views.py               # Log viewing endpoints
│   └── legal/
│       └── legal_views.py             # Terms, privacy, GDPR compliance
├── weekly_test/
│   └── ai_service.py                  # AI question generation (claude-3-haiku)
├── utils/
│   ├── slack_notifications.py         # Slack alert integration
│   └── monitoring.py                  # Metrics tracking utilities
└── resee/
    ├── settings/
    │   ├── base.py                    # Common settings
    │   ├── development.py             # Dev environment
    │   └── production.py              # Production environment
    ├── celery.py                      # Celery configuration
    ├── throttling.py                  # Redis-based rate limiting
    ├── structured_logging.py          # JSON logging formatters
    ├── permissions.py                 # Custom DRF permissions
    └── middleware.py                  # Custom middleware
```

#### Frontend Critical Files
```
frontend/src/
├── App.tsx                            # Main app with lazy loading (21 pages)
├── index.tsx                          # Entry point with PWA setup
├── utils/
│   ├── api.ts                         # JWT interceptor, API client
│   ├── api/
│   │   ├── auth.ts                    # Authentication API
│   │   ├── content.ts                 # Content API
│   │   ├── review.ts                  # Review API
│   │   ├── subscription.ts            # Subscription API
│   │   ├── analytics.ts               # Analytics API
│   │   └── weeklyTest.ts              # Weekly test API
│   ├── sw-registration.ts             # PWA service worker setup
│   ├── logger.ts                      # Client-side logging
│   └── permissions.ts                 # Permission checks
├── contexts/
│   ├── AuthContext.tsx                # Authentication context
│   └── ThemeContext.tsx               # Dark/light theme
├── pages/ (21 pages, all lazy-loaded)
│   ├── HomePage.tsx                   # Landing page
│   ├── LoginPage.tsx                  # Login form
│   ├── RegisterPage.tsx               # Registration
│   ├── EmailVerificationPage.tsx      # Email verification
│   ├── VerificationPendingPage.tsx    # Pending verification notice
│   ├── DashboardPage.tsx              # Main dashboard
│   ├── ContentPage.tsx                # Content list
│   ├── CreateContentPage.tsx          # Content creation
│   ├── EditContentPage.tsx            # Content editing
│   ├── ReviewPage.tsx                 # Review interface
│   ├── WeeklyTestPage.tsx             # Weekly tests
│   ├── ProfilePage.tsx                # User profile
│   ├── SettingsPage.tsx               # User settings
│   ├── SubscriptionPage.tsx           # Subscription tiers, pricing
│   ├── PaymentHistoryPage.tsx         # Payment records
│   ├── CheckoutPage.tsx               # Toss Payments checkout
│   ├── PaymentSuccessPage.tsx         # Payment confirmation
│   ├── PaymentFailPage.tsx            # Payment error handling
│   ├── NotFoundPage.tsx               # 404 page
│   ├── TermsPage.tsx                  # Terms of service
│   └── PrivacyPage.tsx                # Privacy policy
├── components/
│   ├── review/
│   │   ├── ReviewCard.tsx             # Review content card
│   │   ├── ReviewControls.tsx         # Review action buttons
│   │   ├── ReviewHeader.tsx           # Review page header
│   │   └── UpgradeModal.tsx           # Tier upgrade prompt
│   ├── subscription/
│   │   ├── TierCard.tsx               # Subscription tier cards
│   │   └── BillingToggle.tsx          # Monthly/yearly toggle
│   ├── dashboard/
│   │   ├── DashboardStats.tsx         # Statistics display
│   │   ├── QuickActions.tsx           # Quick action buttons
│   │   └── LearningTips.tsx           # Learning recommendations
│   ├── LoadingFallback.tsx            # Suspense loading component
│   ├── ProtectedRoute.tsx             # Auth route wrapper
│   └── ErrorBoundary.tsx              # Error boundary
└── types/
    ├── index.ts                       # TypeScript type definitions
    └── tosspayments.d.ts              # Toss Payments SDK types
```

#### Configuration
```
docker-compose.yml                     # Local development (runserver, npm start)
docker-compose.prod.yml                # Local production-like (gunicorn, nginx)
.env                                   # Development environment variables
.env.prod                              # Production environment variables (AWS ECS)
.env.example                           # Template for environment setup
backend/resee/celery.py                # Celery config (broker, beat scheduler)
frontend/package.json                  # Tree shaking (sideEffects), scripts
.github/workflows/                     # GitHub Actions (CI/CD for AWS ECS)
```

### Feature Development Checklist

When adding new features:
- [ ] Check subscription tier restrictions (`PermissionService`)
- [ ] Add rate limiting if needed (Django REST throttling)
- [ ] Update TypeScript types (`frontend/src/types/`)
- [ ] Invalidate React Query cache after mutations
- [ ] Use `select_related()`/`prefetch_related()` for queries
- [ ] Implement pagination (20 items/page)
- [ ] Add tests (70% coverage minimum)
- [ ] Run linting: `npm run lint` and `black .`
- [ ] Check AI service availability if using AI features

### Performance Guidelines

**Backend**:
- Use `select_related()` for ForeignKey
- Use `prefetch_related()` for ManyToMany
- Cache expensive operations with locmem cache (24h TTL)
- Single Gunicorn worker with 2 threads (configured)
- Monitor throttle cache usage (Redis)

**Frontend**:
- React Query for server state (retry: 1, refetchOnWindowFocus: false)
- Invalidate cache after mutations
- Bundle size: ~254 kB (main bundle, with 27 lazy-loaded chunks)
- All 21 pages use React.lazy() for code splitting
- Tree shaking enabled via sideEffects config

---

## System Architecture

### Backend Structure

**Django Apps**:
```
accounts/
├── auth/                    # JWT authentication, login/logout/refresh
├── subscription/            # Tier management, upgrade/downgrade, billing
│   ├── subscription_views.py    # Payment APIs (checkout, confirm, webhook)
│   ├── billing_service.py       # Automated billing schedules
│   ├── toss_service.py          # Toss Payments integration (httpx)
│   └── services.py              # SubscriptionService, PermissionService
├── legal/                   # GDPR compliance, privacy, terms
├── email/                   # Email verification, password reset
└── health/                  # Health checks (/api/health/, /api/health/detailed/)

content/                     # Learning material CRUD, AI validation
review/                      # Review system, scheduling, AI evaluation, backups
analytics/                   # Performance metrics, progress tracking
weekly_test/                 # AI-generated tests, question generation
utils/                       # Slack notifications, monitoring utilities
```

**Design Patterns**:
- RESTful API architecture
- Signal-based automation (content → ReviewSchedule)
- Decorator-based permission checks (`@has_subscription_permission`)
- Celery for async tasks (email, backups)
- Service layer pattern (SubscriptionService, PermissionService)
- Singleton pattern for AI services

### Frontend Structure

**Technology Stack**:
- React 18.2.0 + TypeScript 4.9.3
- React Query 4.16.1 for state management
- Tailwind CSS 3.2.4 for styling
- TipTap 3.0.7 for rich text editing
- Toss Payments Widget SDK 0.12.0

**Architecture**:
- Component-based with feature-based organization
- Lazy loading for all 21 pages
- Context API for global state (Auth, Theme)
- React Query for server state
- Modular API clients (`utils/api/`)

**State Management**:
- Server state: React Query (queries, mutations)
- Auth state: JWT tokens in memory (api.ts)
- Theme state: Context API with localStorage
- Local state: React hooks (useState, useReducer)

**PWA Features**:
- Service worker registration (`sw-registration.ts`)
- Install prompt management
- Network status tracking
- App update management
- Offline capability

### Integration Points

#### Authentication Flow
```
1. Login Request
   → POST /api/accounts/auth/login/
   → Backend validates credentials
   → Returns access + refresh JWT tokens

2. Token Storage
   → Store in memory (api.ts interceptor)
   → No localStorage (security)
   → Auto-add Authorization header

3. Token Refresh
   → Interceptor detects 401
   → Call /api/accounts/auth/refresh/
   → Update access token
   → Retry original request

4. Permission Check
   → @has_subscription_permission decorator
   → Check user tier per request
   → Return 403 if insufficient tier
```

**Implementation**:
- Frontend: `utils/api.ts` (JWT interceptor with auto-refresh)
- Backend: `accounts/auth/views.py` (login, logout, refresh, verify)
- Middleware: `accounts/auth/middleware.py` (token validation)
- Permission: `resee/permissions.py` (tier-based access control)

#### Review System Integration
```
Frontend (ReviewPage.tsx)
→ GET /api/review/today/
→ Display content with ReviewCard
→ User submits review
→ POST /api/review/{id}/submit/
→ Backend updates interval_index
→ calculate_next_review_date()
→ Create ReviewHistory record
→ Update analytics
→ Return next review date
```

**Key Files**:
- Frontend: `pages/ReviewPage.tsx`, `components/review/ReviewControls.tsx`
- Backend: `review/views.py`, `review/utils.py`, `review/services.py`
- Models: `review/models.py:ReviewSchedule`, `review/models.py:ReviewHistory`

#### Email Notifications
```
User Configuration
→ NotificationPreference model
→ daily_reminder_enabled, evening_reminder_enabled
→ Unsubscribe token (64 chars, unique)

Celery Beat Schedule
→ Daily task at configured times
→ Query users with reviews due + notifications enabled
→ Send personalized emails via Django email backend

Email Content
→ Review count, due items list
→ Unsubscribe link with token
→ Support for Gmail SMTP
```

**Implementation**:
- Model: `accounts/models.py:NotificationPreference`
- Task: `review/tasks.py:send_individual_review_reminder`
- API: `/api/accounts/notification-preferences/`
- Background: Celery Beat + Redis broker
- Scheduler: DatabaseScheduler (django-celery-beat)

#### Payment System Integration
```
Implementation (not activated - FREE tier only):
1. SubscriptionPage: User clicks "구독하기"
   → FREE tier: Password verification only
   → BASIC/PRO tier: Would redirect to /payment/checkout (disabled)

2. Payment Flow (implemented but inactive)
   → POST /api/accounts/payment/checkout/
   → Toss Payment Widget SDK integration
   → Confirm API (toss_service.py)
   → Webhook for payment events
```

**Key Files**:
- Backend:
  * `accounts/subscription/toss_service.py` (API integration, httpx client)
  * `accounts/subscription/subscription_views.py` (checkout, confirm, webhook)
  * `accounts/subscription/billing_service.py` (schedule automation)
- Frontend:
  * `pages/CheckoutPage.tsx` (Widget SDK integration)
  * `pages/PaymentSuccessPage.tsx` (Confirm & redirect)
  * `pages/PaymentFailPage.tsx` (Error handling)
- Routes: `/api/accounts/payment/{checkout,confirm,webhook}/`

**Current Status**: Toss Payments integration is code complete but not activated (FREE tier only strategy).

### Infrastructure

#### Development Infrastructure (Docker Compose)

**Docker Compose Services** (for local development):
- `backend`: Django + runserver (dev) / Gunicorn (prod)
- `frontend`: npm start (dev) / Nginx static (prod)
- `postgres`: PostgreSQL 15 with healthcheck
- `redis`: Redis 7-alpine for Celery + throttling
- `celery`: Background workers (email, AI tasks)
- `celery-beat`: Scheduled tasks with DatabaseScheduler
- `nginx`: Reverse proxy (port 80, production-like)

**Database & Cache** (local):
- PostgreSQL 15 (Docker)
  - Development: `resee_dev`
  - Healthcheck: pg_isready
- Redis (Docker, port 6379)
  - Database 0: Celery broker + rate limiting cache
  - Healthcheck: redis-cli ping

#### Production Infrastructure (AWS Cloud)

**AWS ECS (Elastic Container Service)**:
- **Cluster**: `resee-cluster`
- **Region**: ap-northeast-2 (Seoul)
- **Services**:
  - `resee-backend-service`: Django backend (Gunicorn, 2 workers, 2 threads)
  - `resee-celery-worker-service`: Background task workers
  - `resee-celery-beat-service`: Scheduled task manager
- **Task Type**: Fargate (serverless containers)
- **Deployment**: Rolling updates via GitHub Actions

**Application Load Balancer (ALB)**:
- **Name**: `resee-alb`
- **DNS**: resee-alb-64869428.ap-northeast-2.elb.amazonaws.com
- **Type**: Application Load Balancer
- **Scheme**: Internet-facing
- **Availability Zones**: ap-northeast-2a, ap-northeast-2c
- **Listener**: Port 80 (HTTP) → resee-backend-tg
- **Target Group**: resee-backend-tg (port 8000, IP targets)
- **Health Check**:
  - Path: `/api/health/`
  - Interval: 30 seconds
  - Timeout: 10 seconds
  - Healthy threshold: 2 consecutive successes
  - Unhealthy threshold: 3 consecutive failures

**Security Group** (resee-alb-sg):
- Inbound: Port 80 (HTTP) from 0.0.0.0/0
- Inbound: Port 443 (HTTPS) from 0.0.0.0/0

**Database** (AWS RDS):
- PostgreSQL 15 (managed)
- Production database: `resee_prod`
- Response time: ~290ms
- Automatic backups enabled

**Cache & Message Broker** (Upstash Redis):
- **Service**: Upstash Redis (managed)
- **Host**: calm-jaybird-34425.upstash.io:6379
- **Protocol**: rediss:// (TLS)
- **Usage**: Celery broker + rate limiting cache
- **Response time**: ~230ms

**Frontend** (Vercel):
- React application deployment
- Automatic deployments from Git
- Global CDN distribution
- HTTPS enabled

**Cache Configuration**:
- **Default cache**: locmem (5000 max entries, cull frequency 4)
- **Throttle cache**: Upstash Redis (50 max connections, 5s timeout)
- **Celery broker**: Upstash Redis

**Deployment Architecture**:
```
User → Vercel (Frontend)
     → AWS ALB → ECS Backend (Django + Gunicorn)
                → RDS PostgreSQL
                → Upstash Redis
     → ECS Celery Worker → Upstash Redis
     → ECS Celery Beat → Upstash Redis
```

---

## AI Services

### Overview

All AI features use **Anthropic Claude API** with different models optimized for specific tasks:

**Models Used**:
1. **Content Validation**: `claude-3-5-sonnet-20241022` (high accuracy)
2. **Answer Evaluation**: `claude-3-haiku-20240307` (cost-efficient)
3. **Question Generation**: `claude-3-haiku-20240307` (cost-efficient)

### 1. Content Validation

**File**: `backend/content/ai_validation.py`

**Model**: `claude-3-5-sonnet-20241022` (temperature: 0.3, max_tokens: 2000)

**Validation Checks**:
- **Factual Accuracy** (0-100): Objective correctness, misinformation detection
- **Logical Consistency** (0-100): Logical flow, contradiction detection
- **Title Relevance** (0-100): Title-content alignment

**Response Format**:
```python
{
  "is_valid": True/False,  # All scores ≥70
  "factual_accuracy": {
    "score": 0-100,
    "issues": ["issue1", "issue2"]
  },
  "logical_consistency": {
    "score": 0-100,
    "issues": []
  },
  "title_relevance": {
    "score": 0-100,
    "issues": []
  },
  "overall_feedback": "Summary feedback (2-3 sentences)"
}
```

**Usage**:
```python
from content.ai_validation import validate_content

result = validate_content(title="Python Basics", content="...")
if result["is_valid"]:
    # Proceed with content creation
```

### 2. Answer Evaluation

**File**: `backend/review/ai_evaluation.py`

**Model**: `claude-3-haiku-20240307` (temperature: 0.3, max_tokens: 500)

**Features**:
- **Invalid Answer Detection**: Spam, numbers-only, meaningless chars → 0 points
- **Scoring Criteria**:
  * 0: Invalid/spam answers
  * 1-49: Poor understanding, major gaps
  * 50-69: Fair understanding, important gaps
  * 70-89: Good understanding, minor gaps
  * 90-100: Excellent understanding, complete

**Response Format**:
```python
{
  "score": 0-100,
  "evaluation": "excellent|good|fair|poor",
  "feedback": "Detailed feedback in Korean",
  "auto_result": "remembered|forgot"  # 70+ = remembered
}
```

**Singleton Instance**:
```python
from review.ai_evaluation import ai_answer_evaluator

if ai_answer_evaluator.is_available():
    result = ai_answer_evaluator.evaluate_answer(
        content_title="Title",
        content_body="Content...",
        user_answer="User's answer..."
    )
```

### 3. Question Generation

**File**: `backend/weekly_test/ai_service.py`

**Model**: `claude-3-haiku-20240307` (temperature: 0.3, max_tokens: 1000)

**Question Types**:
- **Multiple Choice**: 4 options, one correct answer
- **True/False**: O/X format

**Response Format**:
```python
{
  "question_type": "multiple_choice|true_false",
  "question_text": "Clear question statement",
  "choices": ["Option 1", "Option 2", "Option 3", "Option 4"],  # or null for true/false
  "correct_answer": "Exact correct answer",
  "explanation": "Brief explanation"
}
```

**Validation**:
- Required fields: question_type, question_text, correct_answer, explanation
- Multiple choice: Must have 4 choices, answer in choices
- True/false: Answer normalized to O/X

**Singleton Instance**:
```python
from weekly_test.ai_service import ai_question_generator

if ai_question_generator.is_available():
    question = ai_question_generator.generate_question(content)

    # Batch generation
    questions = ai_question_generator.generate_batch_questions(content_list)
```

### AI Service Configuration

**Environment Variable**:
```bash
ANTHROPIC_API_KEY=sk-ant-api...  # Required
```

**API Key Validation**:
- Must start with `sk-ant-api`
- Minimum length: 20 characters
- Validated on initialization

**Error Handling**:
- AuthenticationError: Invalid API key
- RateLimitError: API quota exceeded
- APIConnectionError: Network issues
- APITimeoutError: Request timeout
- All errors logged with context

**Requirements**:
```python
anthropic==0.39.0
httpx==0.27.0  # For Toss Payments, compatible with Anthropic
```

---

## Reference

### Environment Variables

**Development (`.env`)**:
```bash
# Django Core
SECRET_KEY=your-secret-key
DEBUG=True
DJANGO_SETTINGS_MODULE=resee.settings.development
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database
DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/resee_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_DB=resee_dev

# Redis (set in docker-compose.yml)
# REDIS_URL=redis://redis:6379/0

# Email Verification
ENFORCE_EMAIL_VERIFICATION=True
EMAIL_VERIFICATION_TIMEOUT_DAYS=1

# Frontend
FRONTEND_URL=http://localhost
REACT_APP_API_URL=/api

# AI Services
ANTHROPIC_API_KEY=your-anthropic-api-key

# Optional
SLACK_WEBHOOK_URL=your-slack-webhook
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id
```

**Production (`.env.prod` - AWS ECS)**:
```bash
# Django Core
SECRET_KEY=your-production-secret-key
DEBUG=False
DJANGO_SETTINGS_MODULE=resee.settings.production
ALLOWED_HOSTS=resee-alb-64869428.ap-northeast-2.elb.amazonaws.com,yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com

# Database (AWS RDS)
DATABASE_URL=postgresql://username:password@rds-endpoint:5432/resee_prod

# Redis (Upstash Redis)
REDIS_URL=rediss://default:password@calm-jaybird-34425.upstash.io:6379

# Email Verification
ENFORCE_EMAIL_VERIFICATION=True

# AI Services (Required)
ANTHROPIC_API_KEY=your-anthropic-api-key

# Monitoring (Optional)
SLACK_WEBHOOK_URL=your-slack-webhook-url
SLACK_DEFAULT_CHANNEL=#alerts

# Toss Payments (not activated - FREE tier only)
# TOSS_CLIENT_KEY=test_gck_docs_... or live_gck_...
# TOSS_SECRET_KEY=test_gsk_docs_... or live_gsk_...
# TOSS_API_URL=https://api.tosspayments.com

# Email (Production)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Frontend URL (Vercel)
FRONTEND_URL=https://your-vercel-domain.vercel.app
```

**Frontend (docker-compose.yml)**:
```bash
REACT_APP_API_URL=/api  # Proxied through Nginx
REACT_APP_GOOGLE_CLIENT_ID=your-google-client-id (optional)
```

### API Endpoints

**Authentication**:
- `POST /api/accounts/auth/login/` - JWT login
- `POST /api/accounts/auth/logout/` - Logout (blacklist token)
- `POST /api/accounts/auth/refresh/` - Refresh access token
- `POST /api/accounts/auth/register/` - User registration
- `POST /api/accounts/auth/verify-token/` - Verify JWT token

**Content**:
- `GET /api/content/` - List user content (paginated)
- `POST /api/content/` - Create content (with AI validation)
- `GET /api/content/{id}/` - Retrieve content
- `PUT /api/content/{id}/` - Update content
- `DELETE /api/content/{id}/` - Delete content

**Review**:
- `GET /api/review/today/` - Get today's reviews
- `POST /api/review/{id}/submit/` - Submit review (with AI evaluation)
- `GET /api/review/history/` - Review history

**Subscription**:
- `GET /api/accounts/subscription/` - Current subscription
- `POST /api/accounts/subscription/upgrade/` - Upgrade tier
- `POST /api/accounts/subscription/cancel/` - Cancel subscription
- `GET /api/accounts/payment-history/` - Payment records

**Payment (Toss)**:
- `POST /api/accounts/payment/checkout/` - Create payment
- `POST /api/accounts/payment/confirm/` - Confirm payment
- `POST /api/accounts/payment/webhook/` - Payment webhook

**Health**:
- `GET /api/health/` - Basic health check
- `GET /api/health/detailed/` - Detailed system health (DB, Redis, Celery)

**Analytics**:
- `GET /api/analytics/stats/` - User learning stats
- `GET /api/analytics/progress/` - Progress over time

### Security Configuration

**Rate Limiting** (Redis-based DRF throttling):
- Anonymous: **100 requests/hour**
- Authenticated: **1000 requests/hour**
- Login: **5 requests/minute**
- Registration: **3 requests/minute**

**Throttle Classes**:
- `resee.throttling.RedisAnonRateThrottle`
- `resee.throttling.RedisUserRateThrottle`

**Security Headers**:
- XSS Protection: `X-XSS-Protection: 1; mode=block`
- HSTS: Enabled (max-age: 31536000)
- X-Frame-Options: `DENY`
- Content-Type-Options: `nosniff`
- CSP: Configured for scripts, styles

**Authentication Security**:
- Email verification token: SHA-256 hashed
- Token comparison: Constant-time (`secrets.compare_digest`)
- JWT tokens: Stored in memory (not localStorage)
- Password: Django's PBKDF2 hasher
- CSRF protection: Enabled for state-changing requests

**Session & Cookies**:
- CSRF cookie: HttpOnly, Secure (production)
- Session cookie: HttpOnly, Secure (production)
- SameSite: Lax

### Technical Stack

**Backend**:
- Django 4.2 (Python 3.11)
- Django REST Framework 3.14
- PostgreSQL 15
- Redis 7-alpine
- Celery 5.3 + django-celery-beat
- Gunicorn (2 workers, 2 threads)
- pytest (40/41 tests passing)
- Anthropic SDK 0.39.0

**Frontend**:
- React 18.2.0 + TypeScript 4.9.3
- TanStack React Query 4.16.1
- Tailwind CSS 3.2.4
- TipTap 3.0.7 (rich text editor)
- Toss Payments Widget SDK 0.12.0
- Bundle: 254 kB (main) + 27 lazy-loaded chunks
- 21 pages with React.lazy() code splitting

**Infrastructure**:
- **Development**: Docker Compose (local containers)
- **Production**:
  - AWS ECS Fargate (containerized backend)
  - AWS RDS PostgreSQL 15 (managed database)
  - AWS ALB (load balancer)
  - Upstash Redis (managed cache & broker)
  - Vercel (frontend hosting)
  - GitHub Actions CI/CD (automated deployment)

**Database Optimization**:
- **ReviewSchedule**: 3 indexes
  * `user + next_review_date + is_active`
  * `next_review_date`
  * `user + is_active`
- **ReviewHistory**: 4 indexes
- **Content**: 3 indexes
  * `author + created_at`
  * `category + created_at`
- **Cache**: Redis (throttle) + locmem (default, 5000 entries)

### Logging & Monitoring

**Structured Logging** (JSON format):
- **django.log**: General application logs (10MB, 5 backups)
- **celery.log**: Celery task logs
- **security.log**: Authentication, permission errors
- **error.log**: Error-level logs only

**Slack Alerts** (9+ triggers):
- Database connection failures
- Redis connection failures
- Disk space warnings (>80%)
- Celery worker failures
- Backup failures/successes
- Payment failures
- API performance issues (>2s response)
- High error rates (>10/min)
- Health check failures

**Monitoring Utilities**:
- `backend/utils/slack_notifications.py`: SlackNotifier class
- `backend/utils/monitoring.py`: MetricsMonitor class
- Celery Beat: Automated backups (daily 3am, pg_dump + gzip)

**Health Checks**:
- `/api/health/`: Basic (DB ping)
- `/api/health/detailed/`: Full (DB, Redis, Celery, Disk)
- Docker healthchecks: PostgreSQL, Redis, Backend

### Emoji Guidelines

**Rules**:
- Minimize usage for professional interface
- Use only for essential UX (review buttons: 😔/😊)
- Never in logs, errors, or documentation
- Avoid decorative emojis

**Benefits**:
- Professional appearance
- Better accessibility (screen readers)
- Improved code readability

---

## Recent Changes

### Production Deployment (2025-11-11)

**AWS Cloud Migration**:
- ✅ Backend deployed to AWS ECS Fargate (3 services)
- ✅ AWS Application Load Balancer configured
- ✅ RDS PostgreSQL 15 (managed database)
- ✅ Upstash Redis (managed cache & Celery broker)
- ✅ Frontend deployed to Vercel
- ✅ GitHub Actions CI/CD pipeline
- ✅ Health checks operational (/api/health/, /api/health/detailed/)

**Production Infrastructure**:
- ECS Cluster: resee-cluster (ap-northeast-2)
- ECS Services: backend, celery-worker, celery-beat (1 task each)
- ALB DNS: resee-alb-64869428.ap-northeast-2.elb.amazonaws.com
- Health Check: 30s interval, 10s timeout
- Availability Zones: ap-northeast-2a, ap-northeast-2c
- Security: ALB security group allows ports 80, 443

**Service Health Status**:
- ✅ Backend: healthy (200 OK, 0.16s response)
- ✅ Database: healthy (~290ms response time)
- ✅ Redis: healthy (~230ms response time)
- ✅ Celery: 1 active worker, 79h uptime
- ✅ Disk: 40% usage, 17.59GB free

### Latest Code Updates (2025-10-17)

**Performance Optimizations**:
- ✅ React.lazy code splitting: **21 pages** lazy-loaded on demand
- ✅ Tree shaking: sideEffects configuration in package.json
- ✅ Bundle optimization: 254 kB main bundle + 27 lazy-loaded chunks
- ✅ LoadingFallback component for smooth UX
- ✅ Rate limiting migrated to Redis
- ✅ source-map-explorer for bundle analysis

**UX Improvements**:
- Subjective review: Removed auto-advance, added user-controlled "Next" button
- ReviewCard layout: Answer-first display for better readability
- PWA features: Service worker, install prompt, offline support

**AI Enhancements**:
- Added invalid answer detection (spam → 0 points)
- Fixed AI service initialization (httpx compatibility)
- Improved weekly test question generation
- Documented AI models: claude-3-5-sonnet (validation), claude-3-haiku (evaluation, questions)

**Bug Fixes**:
- Fixed ReviewHistory null constraint
- Resolved Celery healthcheck issues
- Fixed AI service singleton initialization

**Infrastructure**:
- Added celery-beat with DatabaseScheduler
- Removed obsolete management commands
- Optimized frontend with component separation
- Improved logging structure (4 separate log files)
- Redis-based rate limiting with detailed configuration

**Documentation**:
- Comprehensive AI services section
- Detailed environment variable guide
- Complete API endpoint reference
- Security configuration details
- Corrected page count (21 pages, added EditContentPage)

### System Status

**All Core Systems Operational**:
- ✅ AI services (validation: claude-3-5-sonnet, evaluation/questions: claude-3-haiku)
- ✅ Celery background tasks (worker + beat)
- ✅ Review system (Ebbinghaus algorithm)
- ✅ Email notifications (Celery Beat scheduled)
- ✅ API endpoints (health checks, detailed monitoring)
- ✅ Subscription management (UI + backend logic)
- ✅ Payment history tracking
- ✅ Billing schedule automation
- ✅ Toss Payments integration (code complete, not activated - FREE tier only)

**Infrastructure Completed**:
- ✅ Security: Rate limiting using Redis (100/hr anon, 1000/hr user, 5/min login, 3/min registration)
- ✅ Security headers (XSS, HSTS, X-Frame-Options, Content-Type-Nosniff)
- ✅ CORS configuration
- ✅ Structured logging (RotatingFileHandler, 10MB, 5 backups)
- ✅ Database indexes (ReviewSchedule: 3, ReviewHistory: 4, Content: 3)
- ✅ Caching system (Redis: throttle + Celery, locmem: general cache, 5000 max)
- ✅ CI/CD pipeline (GitHub Actions: tests, linting, deployment)
- ✅ Session/CSRF cookie security
- ✅ Celery automated backup (pg_dump + gzip, daily 3am, Slack alerts)
- ✅ Slack alert system (health, backup, payment, API performance)
- ✅ Monitoring utilities (backend/utils/slack_notifications.py, monitoring.py)
- ✅ PWA features (service worker, install prompt, offline, updates)

**Configuration**:
- **Development**: Local PostgreSQL (resee_dev), Docker Compose
- **Production**:
  - AWS ECS Fargate: 3 services (backend, celery-worker, celery-beat)
  - AWS RDS PostgreSQL 15 (resee_prod)
  - Upstash Redis (Celery broker + rate limiting)
  - Vercel (frontend deployment)
- Gunicorn configuration: 2 workers, 2 threads (max-requests: 1000)
- Celery Beat with DatabaseScheduler for scheduled tasks
- Test coverage: 40/41 tests passing (1 security test failing: test_token_blacklisted_on_password_change)
- Frontend bundle: 254 kB main + 27 lazy-loaded chunks
- React performance: 21 pages with React.lazy code splitting

**Monitoring & Alerts**:
- Logging: 4 separate log files (django, celery, security, error)
- Slack alerts: ✅ **Active & Tested** - Database, Redis, Disk, Celery, Backup, Payment failures
- Celery backup: ✅ **Operational** - Daily 3am via Celery Beat, Slack notifications
- Health check: `/api/health/` (basic), `/api/health/detailed/` (full system)
- Metrics tracking: API performance, error rates, payment failures
- **Status**: Fully operational & tested (2025-10-17)

**Production Deployment Status** (2025-11-11):
- ✅ AWS ECS: 3 services running (backend, celery-worker, celery-beat)
- ✅ AWS ALB: Active, health checks passing
- ✅ RDS PostgreSQL: Healthy, ~290ms response
- ✅ Upstash Redis: Healthy, ~230ms response
- ✅ Vercel Frontend: Deployed
- ✅ Overall System: Operational
