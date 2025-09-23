# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Resee is a smart review platform leveraging Ebbinghaus forgetting curve theory. Built with Django (backend) and React (frontend), managed via Docker Compose. Uses local PostgreSQL for development and Supabase for production with single Gunicorn worker configuration.

## 접속 방법 (Access URLs)

### 개발 환경 접속
```bash
# 1. Nginx를 통한 통합 접속 (권장)
http://localhost          # 또는 http://localhost:80
# → Frontend + Backend API 통합, 프로덕션과 동일한 구조

# 2. 개발 서버 직접 접속
http://localhost:3000     # React 개발 서버 (Hot reload 지원)
http://localhost:8000/api # Django API 서버 직접 접속

# 3. 관리자 페이지
http://localhost:8000/admin  # Django Admin
```

**중요**: Nginx 통합 접속(`http://localhost`)을 사용하면 프로덕션 환경과 동일한 구조로 테스트할 수 있습니다.

## Common Development Commands

### Development Environment
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx
```

### Backend Commands
```bash
# Django migrations
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate

# Run tests
docker-compose exec backend python -m pytest
docker-compose exec backend python -m pytest accounts/tests.py -v  # Single app
docker-compose exec backend python -m pytest --cov=. --cov-report=html

# Code quality
docker-compose exec backend black .
docker-compose exec backend flake8

# Django shell
docker-compose exec backend python manage.py shell_plus
```

### Frontend Commands
```bash
# Run tests
docker-compose exec frontend npm test -- --watchAll=false
docker-compose exec frontend npm run test:coverage

# Linting and type checking (MUST RUN before committing)
docker-compose exec frontend npm run lint
docker-compose exec frontend npm run typecheck

# Build
docker-compose exec frontend npm run build
docker-compose exec frontend npm run ci:quick  # Typecheck + build
```

## Architecture Overview

### Core Domain Flow
The review system implements Ebbinghaus forgetting curve theory through a synchronous signal-based architecture:

1. **Content Creation Flow**: User creates content → Django signal (`content/signals.py`) → ReviewSchedule created synchronously → Available for review next day
2. **Review Process**: User reviews content → Update `interval_index` based on performance → Calculate next review date using tier-specific intervals
3. **Subscription Tiers Control**: Review intervals (FREE: [1,3], BASIC: [1,3,7,14,30,60,90], PRO: [1,3,7,14,30,60,120,180]) and AI usage limits (FREE: 0/day, BASIC: 30/day, PRO: 200/day)

### Cross-Component Integrations

**Authentication & Authorization Flow**:
- Frontend `utils/api.ts` → JWT interceptor → Backend `accounts/authentication.py`
- Token refresh handled automatically via `refreshAuthToken()` in `api.ts`
- Subscription tier checked in views via `has_subscription_permission()` decorator

**AI Question Generation Pipeline**:
- Frontend triggers via `useAIFeatures` hook → Backend `ai_review/views.py` → `ai_review/services/` (Claude API or mock based on `AI_USE_MOCK_RESPONSES`)
- Rate limiting enforced at view level based on subscription tier
- Results cached in local memory for 24 hours

**Review Scheduling System**:
- `ReviewSchedule` model tracks progress with `interval_index` (0-7 based on tier)
- `review/utils.py:calculate_next_review_date()` implements the core algorithm
- Frontend `ReviewPage.tsx` fetches today's reviews via `/api/review/today/`
- Performance recorded in `ReviewHistory` for analytics

### Critical Environment Variables

**Development** (`.env`):
- `DJANGO_SETTINGS_MODULE`: `resee.settings.development`
- `DATABASE_URL`: `postgresql://postgres:postgres123@postgres:5432/resee_dev` (Local Docker PostgreSQL)
- `ANTHROPIC_API_KEY`: Optional for dev (uses mock when not set)
- `ENFORCE_EMAIL_VERIFICATION`: `False` to skip email verification
- `AI_USE_MOCK_RESPONSES`: `True` to avoid API costs

**Production** (`.env.prod`):
- `DJANGO_SETTINGS_MODULE`: `resee.settings.production`
- `DATABASE_URL`: Supabase PostgreSQL connection string
- `SUPABASE_URL`: Supabase project API URL
- `SUPABASE_ANON_KEY`: Supabase anonymous key for API access
- `ANTHROPIC_API_KEY`: Required for AI features
- `ENFORCE_EMAIL_VERIFICATION`: `True` for production
- `AI_USE_MOCK_RESPONSES`: `False` for real AI responses

**Frontend**:
- `REACT_APP_API_URL`: Must match backend URL (`http://localhost:8000/api` for dev)
- `REACT_APP_GOOGLE_CLIENT_ID`: Optional for Google OAuth

## Environment Setup

### Local Development
```bash
# Copy environment template
cp .env.example .env

# Start services (PostgreSQL, Backend, Frontend, Nginx)
docker-compose up -d

# Apply migrations
docker-compose exec backend python manage.py migrate

# Create superuser (optional)
docker-compose exec backend python manage.py createsuperuser
```

### Production Deployment
```bash
# Prepare production environment
cp .env.prod.example .env.prod
# Edit .env.prod with production values (Supabase credentials)

# Deploy with production compose file (optimized for single worker)
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Initial setup
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --noinput

# Health check
docker-compose exec backend python manage.py health_check
```

## Key File Locations

### Core Business Logic
- **Ebbinghaus Algorithm**: `backend/review/utils.py`
- **Review Schedule Signal**: `backend/content/signals.py`
- **Subscription Logic**: `backend/accounts/models.py:Subscription`
- **AI Services**: `backend/ai_review/services/`

### Frontend Architecture
- **API Client with JWT**: `frontend/src/utils/api.ts`
- **Review System UI**: `frontend/src/pages/ReviewPage.tsx`
- **Type Definitions**: `frontend/src/types/`
- **Auth Context**: `frontend/src/contexts/AuthContext.tsx`

### Configuration
- **Django Settings**: `backend/resee/settings/{base,development,production}.py`
- **Docker Compose**: `docker-compose.yml` (dev), `docker-compose.prod.yml` (prod, single worker)
- **Cache System**: Local memory cache (no Redis dependency)

## Development Guidelines

### Adding New Features
1. Check subscription tier restrictions in `backend/accounts/models.py`
2. Add rate limiting decorator if API endpoint
3. Update TypeScript types in `frontend/src/types/`
4. Invalidate React Query cache after mutations using `queryClient.invalidateQueries()`

### Performance Optimization
- Use `select_related()` and `prefetch_related()` for Django queries
- Implement pagination (default: 20 items per page)
- Cache expensive operations in local memory cache (24-hour TTL)
- Frontend uses React Query for server state management
- Single Gunicorn worker with 2 threads for production efficiency

### Testing Requirements
- Backend: 70% coverage minimum (`pytest --cov`)
- Frontend: 70% coverage minimum (`npm run test:coverage`)
- Run linting before commits: `npm run lint` and `black .`

## Test Accounts (Supabase Production)

### Admin Account
- **Email**: `superadmin@reseeall.com`
- **Password**: `Admin@123456`
- **Role**: Superuser with full admin access
- **Subscription**: PRO tier

### Portfolio Demo Account
- **Email**: `portfolio@reseeall.com`
- **Password**: `Portfolio@123`
- **Role**: Regular user with 6 months of learning history
- **Subscription**: PRO tier
- **Content**: 3 categories, 4 contents with review history

## Architecture Notes

### Production Optimizations (2025-09)
- **Database**: Migrated from local PostgreSQL to Supabase for production
- **Cache**: Removed Redis dependency, using Django local memory cache
- **Worker Configuration**: Single Gunicorn worker with 2 threads optimized for Supabase
- **Backup System**: Removed local backup scripts (Supabase handles backups)
- **Health Checks**: Updated to check local cache instead of Redis