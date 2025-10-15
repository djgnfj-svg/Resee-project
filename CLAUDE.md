# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Table of Contents
1. [Quick Start](#quick-start) - Get started in 5 minutes
2. [Core Concepts](#core-concepts) - Understand the domain
3. [Development Workflow](#development-workflow) - Daily commands and tasks
4. [System Architecture](#system-architecture) - Technical structure
5. [Reference](#reference) - Detailed specifications
6. [Recent Changes](#recent-changes) - Latest updates

---

## Quick Start

### Project Overview
Resee is a focused spaced repetition learning platform implementing the Ebbinghaus forgetting curve theory. Built with Django (backend) and React (frontend), managed via Docker Compose.

**Key Philosophy**: Pure learning effectiveness over engagement metrics. No streaks, achievements, or gamification - just scientifically-proven spaced repetition for optimal knowledge retention.

### Access URLs
```bash
# Nginx (Recommended - production-like)
http://localhost

# Development servers
http://localhost:3000     # React dev server
http://localhost:8000/api # Django API
http://localhost:8000/admin
```

### Test Accounts

**Production**:

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

- **Content**: User-created learning material
- **ReviewSchedule**: Tracks next review date, interval_index
- **ReviewHistory**: Performance records
- **Subscription**: User tier (FREE/BASIC/PRO), billing cycles, auto-renewal
- **PaymentHistory**: Payment records (upgrade/downgrade/cancellation)
- **BillingSchedule**: Automated billing schedules for renewals
- **NotificationPreference**: Email notification settings

---

## Development Workflow

### Common Commands

#### Start/Stop Services
```bash
docker-compose up -d
docker-compose down
docker-compose logs -f backend
docker-compose logs -f frontend
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

# Build
docker-compose exec frontend npm run build
```

### Key File Locations

#### Backend Critical Files
```
backend/
├── review/utils.py                    # Ebbinghaus algorithm
├── content/signals.py                 # ReviewSchedule auto-creation
├── accounts/models.py                 # Subscription model
├── review/tasks.py                    # Email reminder tasks
├── content/ai_validation.py           # AI content validation
├── review/ai_evaluation.py            # AI answer evaluation
├── weekly_test/ai_service.py          # AI question generation
└── resee/settings/
    ├── base.py
    ├── development.py
    └── production.py
```

#### Frontend Critical Files
```
frontend/src/
├── utils/api.ts                       # JWT interceptor, API client
├── pages/
│   ├── DashboardPage.tsx              # Main dashboard
│   ├── ReviewPage.tsx                 # Review interface
│   ├── SubscriptionPage.tsx           # Subscription tiers, pricing
│   ├── PaymentHistoryPage.tsx         # Payment records
│   └── SettingsPage.tsx               # User settings
├── components/
│   ├── review/ReviewControls.tsx      # Review buttons
│   └── subscription/TierCard.tsx      # Subscription tier cards
└── types/                             # TypeScript definitions
```

#### Configuration
```
docker-compose.yml                     # Development
docker-compose.prod.yml                # Production
.env                                   # Development vars
.env.prod                              # Production vars
backend/resee/celery.py                # Celery config
```

### Feature Development Checklist

When adding new features:
- [ ] Check subscription tier restrictions
- [ ] Add rate limiting if needed (Django REST throttling)
- [ ] Update TypeScript types (`frontend/src/types/`)
- [ ] Invalidate React Query cache after mutations
- [ ] Use `select_related()`/`prefetch_related()` for queries
- [ ] Implement pagination (20 items/page)
- [ ] Add tests (70% coverage minimum)
- [ ] Run linting: `npm run lint` and `black .`

### Performance Guidelines

**Backend**:
- Use `select_related()` for ForeignKey
- Use `prefetch_related()` for ManyToMany
- Cache expensive operations (24h TTL)
- Single Gunicorn worker with 2 threads

**Frontend**:
- React Query for server state
- Invalidate cache after mutations
- Bundle size: ~283 kB

---

## System Architecture

### Backend Structure

**Django Apps**:
```
accounts/
├── auth/                    # JWT authentication, login/logout
├── subscription/            # Tier management, upgrade/downgrade
│   ├── subscription_views.py    # Upgrade, cancel, payment history
│   ├── billing_service.py       # Automated billing schedules
│   └── services.py             # Subscription logic
├── legal/                   # GDPR compliance, privacy
├── email/                   # Email verification
└── health/                  # Health checks

content/                     # Learning material CRUD
review/                      # Review system, scheduling
analytics/                   # Performance metrics
weekly_test/                 # AI-generated tests
```

**Design Patterns**:
- RESTful API architecture
- Signal-based automation (content → ReviewSchedule)
- Decorator-based permission checks (`@has_subscription_permission`)
- Celery for async tasks

### Frontend Structure

**Technology Stack**:
- React 18 + TypeScript
- React Query for state management
- Tailwind CSS for styling
- Component-based architecture

**State Management**:
- Server state: React Query
- Auth state: JWT tokens in memory
- Local state: React hooks

### Integration Points

#### Authentication Flow
```
Login → JWT tokens (access + refresh)
→ Store in memory (api.ts)
→ Interceptor adds Authorization header
→ Auto-refresh on 401
→ Subscription tier checked per request
```

**Implementation**:
- Frontend: `utils/api.ts` JWT interceptor
- Backend: `accounts/auth/` views
- Token refresh: `refreshAuthToken()`
- Permission check: `has_subscription_permission()` decorator

#### Review System Integration
```
Frontend (ReviewPage.tsx)
→ GET /api/review/today/
→ Display content
→ User submits review
→ POST /api/review/{id}/submit/
→ Backend updates interval_index
→ calculate_next_review_date()
→ Return next review date
```

**Key Files**:
- Frontend: `pages/ReviewPage.tsx`, `components/review/ReviewControls.tsx`
- Backend: `review/views.py`, `review/utils.py`
- Model: `review/models.py:ReviewSchedule`

#### Email Notifications
```
User enables notifications (NotificationPreference)
→ Celery periodic task runs daily
→ Query users with reviews due + notifications enabled
→ Send email via Django email backend
```

**Implementation**:
- Model: `accounts/models.py:NotificationPreference`
- Task: `review/tasks.py:send_individual_review_reminder`
- API: `/api/accounts/notification-preferences/`
- Background: Celery + Redis

#### AI Services
```
Content Creation
→ Validate via Claude API (ai_validation.py)
→ Check factual accuracy, relevance

Review Submission
→ Evaluate answer via Claude API (ai_evaluation.py)
→ Score 0-100, provide feedback

Weekly Test
→ Generate questions via Claude API (ai_service.py)
→ Multiple choice from content
```

### Infrastructure

**Docker Compose Services**:
- `backend`: Django + Gunicorn
- `frontend`: React dev server (dev) / Nginx static (prod)
- `postgres`: PostgreSQL 15
- `redis`: Celery broker
- `celery`: Background workers
- `nginx`: Reverse proxy (production-like)

**Database**:
- PostgreSQL 15 (local Docker)
- Development: `resee_dev`
- Production: `resee_prod`

---

## Reference

### Environment Variables

**Development (`.env`)**:
```bash
DJANGO_SETTINGS_MODULE=resee.settings.development
DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/resee_dev
ENFORCE_EMAIL_VERIFICATION=True
# REDIS_URL set in docker-compose.yml
```

**Production (`.env.prod`)**:
```bash
DJANGO_SETTINGS_MODULE=resee.settings.production
DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/resee_prod
REDIS_URL=redis://redis:6379/0
ENFORCE_EMAIL_VERIFICATION=True
ANTHROPIC_API_KEY=<required>
```

**Frontend (docker-compose.yml)**:
```bash
REACT_APP_API_URL=/api  # Proxied through Nginx
REACT_APP_GOOGLE_CLIENT_ID=<optional>
```

### AI Features

All AI features use **Anthropic Claude API**:

**1. Content Validation** (`content/ai_validation.py`):
- Factual accuracy check
- Logical consistency
- Title relevance validation

**2. Answer Evaluation** (`review/ai_evaluation.py`):
- Subjective answer scoring (0-100)
- Detailed feedback generation
- Invalid answer detection (spam → 0 points)

**3. Question Generation** (`weekly_test/ai_service.py`):
- Auto-generate multiple choice questions
- Based on user's content library

**Requirements**:
```python
anthropic==0.39.0
httpx==0.27.0
```

**Environment**: `ANTHROPIC_API_KEY` required

### Technical Stack

**Backend**:
- Django 4.2
- Django REST Framework
- PostgreSQL 15
- Celery + Redis
- Gunicorn (1 worker, 2 threads)
- pytest (95.7% coverage)
- Stripe SDK (installed, not integrated)

**Frontend**:
- React 18 + TypeScript
- React Query
- Tailwind CSS
- Bundle size: 283.14 kB
- Performance: 25+ React optimization hooks

**Infrastructure**:
- Docker Compose
- Nginx (reverse proxy)
- PostgreSQL (local Docker)
- Redis (Celery broker)
- GitHub Actions CI/CD

**Database Optimization**:
- ReviewSchedule: 3 indexes (user+date+active, date, user+active)
- ReviewHistory: 4 indexes
- Content: 3 indexes (author+created, category+created)
- Caching: locmem (5000 max entries)

**Security**:
- Rate limiting configured (REST Framework throttling)
- Security headers (XSS, HSTS, X-Frame-Options, CSP)
- CORS policy enforced
- HTTPS via CloudFlare
- Session/CSRF cookie security

### Emoji Guidelines

**Rules**:
- Minimize usage for professional interface
- Use only for essential UX (review buttons: 😔/😊)
- Never in logs, errors, or documentation
- Avoid decorative emojis

**Benefits**:
- Professional appearance
- Better accessibility
- Improved code readability

---

## Recent Changes

### Latest Code Updates (2025-01)

**UX Improvements**:
- Subjective review: Removed auto-advance, added user-controlled "Next" button
- ReviewCard layout: Answer-first display for better readability

**AI Enhancements**:
- Added invalid answer detection (spam → 0 points)
- Fixed AI service initialization (httpx compatibility)
- Improved weekly test question generation

**Bug Fixes**:
- Fixed ReviewHistory null constraint
- Resolved Celery healthcheck issues

**Optimizations**:
- Removed obsolete management commands
- Optimized frontend with component separation
- Improved logging structure

### System Status

**All Core Systems Operational**:
- ✅ AI services (validation, evaluation, questions)
- ✅ Celery background tasks
- ✅ Review system (Ebbinghaus algorithm)
- ✅ Email notifications
- ✅ API endpoints
- ✅ Subscription management (UI + backend logic)
- ✅ Payment history tracking
- ✅ Billing schedule automation

**Infrastructure Completed**:
- ✅ Security: Rate limiting (100/hr anon, 1000/hr user, 5/min login)
- ✅ Security headers (XSS, HSTS, X-Frame-Options, Content-Type-Nosniff)
- ✅ CORS configuration
- ✅ Structured logging (RotatingFileHandler, 10MB, 5 backups)
- ✅ Database indexes (ReviewSchedule: 3, ReviewHistory: 4, Content: 3)
- ✅ Caching system (locmem, 5000 max entries)
- ✅ CI/CD pipeline (GitHub Actions: tests, linting, deployment)
- ✅ Session/CSRF cookie security

**Partially Implemented**:
- ⚠️ Payment system: UI + logic complete, real gateway integration needed
- ⚠️ Monitoring: Health check exists, Sentry integration needed
- ⚠️ Logging: Structured logs exist, JSON formatter needed
- ⚠️ Frontend optimization: Some React.memo usage, code splitting needed

**Configuration**:
- Local PostgreSQL for dev and prod
- Single worker configuration (Gunicorn: 1 worker, 2 threads)
- Simplified Docker networking
- Standard PostgreSQL backups
- Test coverage: 95.7% (88/92 tests passing)
- Frontend bundle: 283.14 kB
- React performance hooks: 25+ usages (useMemo/useCallback/React.memo)
