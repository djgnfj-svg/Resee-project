# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview
Resee is a focused spaced repetition learning platform implementing the Ebbinghaus forgetting curve theory. Built with Django (backend) and React (frontend), managed via Docker Compose. Uses local PostgreSQL for both development and production.

**Key Philosophy**: Pure learning effectiveness over engagement metrics. No streaks, achievements, or gamification - just scientifically-proven spaced repetition for optimal knowledge retention.

## Access URLs

```bash
# Nginx (Recommended - production-like)
http://localhost

# Development servers
http://localhost:3000     # React dev server
http://localhost:8000/api # Django API

# Admin
http://localhost:8000/admin
```

## Common Development Commands

### Start Services
```bash
docker-compose up -d
docker-compose logs -f backend
```

### Backend
```bash
# Migrations
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate

# Tests
docker-compose exec backend python -m pytest
docker-compose exec backend python -m pytest --cov=. --cov-report=html

# Shell
docker-compose exec backend python manage.py shell_plus
```

### Frontend
```bash
# Tests
docker-compose exec frontend npm test -- --watchAll=false
docker-compose exec frontend npm run test:coverage

# Linting (MUST RUN before committing)
docker-compose exec frontend npm run lint
docker-compose exec frontend npm run typecheck

# Build
docker-compose exec frontend npm run build
```

## Architecture Overview

### Core Domain Flow
1. **Content Creation**: User creates content → Django signal → ReviewSchedule created → Available for review next day
2. **Review Process**: User reviews → Update `interval_index` → Calculate next review date
3. **Subscription Tiers**: Review intervals based on Ebbinghaus curve
   - FREE: [1,3]
   - BASIC: [1,3,7,14,30,60,90]
   - PRO: [1,3,7,14,30,60,120,180]

### Key Integrations

**Authentication**:
- JWT interceptor in `utils/api.ts`
- Token refresh via `refreshAuthToken()`
- Subscription tier checked via `has_subscription_permission()` decorator

**Review System**:
- `ReviewSchedule` model with `interval_index`
- Core algorithm: `review/utils.py:calculate_next_review_date()`
- Frontend: `ReviewPage.tsx` → `/api/review/today/`

**Email Notifications**:
- `NotificationPreference` model
- Celery + Redis for background tasks
- `/api/accounts/notification-preferences/` endpoints
- Daily reminders: `review/tasks.py:send_individual_review_reminder`

**Analytics**:
- Basic metrics: today's reviews, total content, 30-day success rate
- No gamification tracking

### Environment Variables

**Development** (`.env`):
```
DJANGO_SETTINGS_MODULE=resee.settings.development
DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/resee_dev
ENFORCE_EMAIL_VERIFICATION=True

# Note: REDIS_URL is set in docker-compose.yml
# REDIS_URL=redis://redis:6379/0
```

**Production** (`.env.prod`):
```
DJANGO_SETTINGS_MODULE=resee.settings.production
DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/resee_prod
REDIS_URL=redis://redis:6379/0
ENFORCE_EMAIL_VERIFICATION=True
```

**Frontend** (set in `docker-compose.yml`):
```
REACT_APP_API_URL=/api  # Proxied through Nginx
REACT_APP_GOOGLE_CLIENT_ID=<optional>
```

## Key File Locations

### Backend
- **Ebbinghaus Algorithm**: `backend/review/utils.py`
- **Review Schedule Signal**: `backend/content/signals.py`
- **Subscription Logic**: `backend/accounts/models.py:Subscription`
- **Email Tasks**: `backend/review/tasks.py`
- **AI Validation**: `backend/content/ai_validation.py`
- **AI Evaluation**: `backend/review/ai_evaluation.py`
- **AI Questions**: `backend/weekly_test/ai_service.py`

### Frontend
- **API Client**: `frontend/src/utils/api.ts`
- **Dashboard**: `frontend/src/pages/DashboardPage.tsx`
- **Review UI**: `frontend/src/pages/ReviewPage.tsx`
- **Review Controls**: `frontend/src/components/review/ReviewControls.tsx`
- **Settings**: `frontend/src/pages/SettingsPage.tsx`
- **Types**: `frontend/src/types/`

### Configuration
- **Django Settings**: `backend/resee/settings/{base,development,production}.py`
- **Docker Compose**: `docker-compose.yml` (dev), `docker-compose.prod.yml` (prod)
- **Celery**: `backend/resee/celery.py`

## Development Guidelines

### Adding Features
1. Check subscription tier restrictions
2. Add rate limiting if needed
3. Update TypeScript types
4. Invalidate React Query cache after mutations

### Performance
- Use `select_related()` and `prefetch_related()`
- Implement pagination (20 items/page)
- Cache expensive operations (24h TTL)
- Single Gunicorn worker with 2 threads

### Testing
- Backend: 70% coverage minimum
- Frontend: 70% coverage minimum
- Lint before commits: `npm run lint` and `black .`

## Test Accounts

### Production
- **Admin**: `superadmin@reseeall.com` / `Admin@123456` (PRO tier)
- **Portfolio**: `portfolio@reseeall.com` / `Portfolio@123` (PRO tier)

### Development
- **Admin**: `admin@resee.com` / `admin123!` (PRO tier, 180-day intervals)
- **Email Test**: `djgnfj8923@naver.com` / `testpassword123` (BASIC tier, 90-day intervals)
- **MCP Test**: `mcptest@example.com` / `mcptest123!` (FREE tier, 3-day intervals)

## System Architecture

### Backend (Django)
- Modular accounts app:
  - `accounts/auth/` - Authentication
  - `accounts/subscription/` - Subscriptions
  - `accounts/legal/` - GDPR compliance
  - `accounts/email/` - Email services
  - `accounts/health/` - Health checks
- RESTful API design
- Signal-based review schedule creation

### Frontend (React + TypeScript)
- React Query for state management
- Responsive CSS with Tailwind
- Component-based architecture

### Infrastructure
- Docker Compose orchestration
- Nginx reverse proxy
- PostgreSQL database
- Redis for Celery

## Core Features

### Implemented
- Ebbinghaus spaced repetition
- Content management
- Review system with performance tracking
- Subscription tiers (FREE/BASIC/PRO)
- Email authentication with JWT
- Responsive design
- AI content validation
- AI answer evaluation
- AI question generation
- Email notifications (Celery)

### Removed (Simplified)
- Streak tracking
- Gamification
- Complex analytics charts
- Achievement systems
- Weekly goal setting

## AI Features (Active)

All AI features use Anthropic Claude API:
- **Content Validation**: Factual accuracy, logical consistency, title relevance
- **Answer Evaluation**: Subjective answer scoring with feedback
- **Question Generation**: Auto-generate test questions

**Requirements**:
- `ANTHROPIC_API_KEY` in environment
- `anthropic==0.39.0`
- `httpx==0.27.0`

## Technical Metrics

- **Frontend Bundle**: 283.14 kB
- **Database**: PostgreSQL (local Docker)
- **Cache**: Redis (Celery only)
- **Worker Config**: Single Gunicorn worker, 2 threads
- **Test Coverage**: 95.7% (88/92 tests passing)

## System State

**Production Optimizations**:
- Local PostgreSQL for dev and prod
- Single worker configuration
- Simplified Docker networking
- Standard PostgreSQL backups
- Celery healthcheck disabled (non-web workers)

**Latest Code Updates**:
- Subjective review UX improvement: Removed auto-advance, added user-controlled "Next" button
- AI evaluation enhancement: Added invalid answer detection (number/character spam → 0 points)
- ReviewCard layout optimization: Answer-first display for better readability
- Fixed AI service initialization (httpx version compatibility)
- Improved weekly test question generation
- Fixed ReviewHistory null constraint

**All Core Systems Operational**:
✅ AI services (validation, evaluation, questions)
✅ Celery background tasks
✅ Review system (Ebbinghaus algorithm)
✅ Email notifications
✅ API endpoints

## Emoji Guidelines

### Rules
- Minimize emoji usage for professional interface
- Use only when essential for UX (review buttons: 😔/😊)
- Never in logs, errors, or documentation
- Avoid decorative emojis

### Benefits
- Professional appearance
- Better accessibility
- Improved code readability
