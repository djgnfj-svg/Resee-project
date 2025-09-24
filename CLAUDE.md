# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Resee is a focused spaced repetition learning platform implementing the Ebbinghaus forgetting curve theory. Built with Django (backend) and React (frontend), managed via Docker Compose. Uses local PostgreSQL for development and Supabase for production with single Gunicorn worker configuration.

**Key Philosophy**: Pure learning effectiveness over engagement metrics. No streaks, achievements, or gamification - just scientifically-proven spaced repetition for optimal knowledge retention.

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
3. **Subscription Tiers Control**: Review intervals (FREE: [1,3], BASIC: [1,3,7,14,30,60,90], PRO: [1,3,7,14,30,60,120,180]) based on Ebbinghaus forgetting curve

### Cross-Component Integrations

**Authentication & Authorization Flow**:
- Frontend `utils/api.ts` → JWT interceptor → Backend `accounts/authentication.py`
- Token refresh handled automatically via `refreshAuthToken()` in `api.ts`
- Subscription tier checked in views via `has_subscription_permission()` decorator

**Review Scheduling System**:
- `ReviewSchedule` model tracks progress with `interval_index` (0-7 based on tier)
- `review/utils.py:calculate_next_review_date()` implements the core Ebbinghaus algorithm
- Frontend `ReviewPage.tsx` fetches today's reviews via `/api/review/today/`
- Performance recorded in `ReviewHistory` for analytics

**Simplified Analytics**:
- Basic dashboard metrics only: today's reviews, total content, 30-day success rate
- No gamification metrics (streaks, achievements, complex progress tracking)
- Focus on learning effectiveness rather than engagement statistics

### Critical Environment Variables

**Development** (`.env`):
- `DJANGO_SETTINGS_MODULE`: `resee.settings.development`
- `DATABASE_URL`: `postgresql://postgres:postgres123@postgres:5432/resee_dev` (Local Docker PostgreSQL)
- `ENFORCE_EMAIL_VERIFICATION`: `False` to skip email verification

**Production** (`.env.prod`):
- `DJANGO_SETTINGS_MODULE`: `resee.settings.production`
- `DATABASE_URL`: Supabase PostgreSQL connection string
- `SUPABASE_URL`: Supabase project API URL
- `SUPABASE_ANON_KEY`: Supabase anonymous key for API access
- `ENFORCE_EMAIL_VERIFICATION`: `True` for production

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
- **Simple Analytics**: `backend/analytics/views.py` (basic dashboard statistics only)

### Frontend Architecture
- **API Client with JWT**: `frontend/src/utils/api.ts`
- **Simple Dashboard**: `frontend/src/pages/SimpleDashboard.tsx` (focus on core metrics)
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
- **Gamification Removal**: Removed all streak tracking, achievement systems, and complex analytics (2025-09-25)
- **Bundle Size**: Reduced frontend bundle by 123.99 kB through analytics component cleanup

## End-to-End Testing Results (2025-09-24)

Comprehensive Playwright MCP testing performed covering user journeys, core functionality, responsive design, and performance.

### ✅ Verified Features

**Core Application Flow**:
- Homepage loads correctly at `http://localhost`
- Dashboard displays simplified user metrics (content count, pending reviews, success rate)
- Content management shows 12 programming topics, all scheduled for tomorrow review
- Review interface displays Ebbinghaus system with keyboard shortcut instructions

**Responsive Design**:
- Mobile (375px): Hamburger menu appears and functions correctly
- Tablet (768px): Layout adapts properly with navigation visible
- Desktop (1920px): Full navigation and optimal layout

**Authentication & Navigation**:
- User session maintained within single page
- Navigation between main sections (Dashboard, Content, Review) works
- Theme toggle (light/dark mode) functional

**Ebbinghaus Review System Core**:
- Review scheduling algorithm visible ("첫 번째 복습" status)
- Content display with difficulty levels (보통) and categories (경제)
- Keyboard shortcut instructions displayed (Space, 1, 2, 3)

### ❌ Known Issues

**Critical Review System Issues**:
- ReviewControls component not rendering (모름/애매함/기억함 buttons missing)
- Keyboard shortcuts (1, 2, 3) not triggering review completion
- Review state management issue preventing full review workflow

**Performance & Network Issues** (RESOLVED 2025-09-25):
- ✅ Removed 404 errors on analytics endpoints (advanced analytics removed)
- Authentication state not persistent across page navigation
- ✅ Bundle size optimized (reduced by 123.99 kB)

**Data Consistency**:
- Subscription tier enforcement needs verification for FREE tier limits
- Content limit validation should be implemented client-side

### 🔧 Recommendations

**High Priority**:
1. Fix ReviewControls rendering in `frontend/src/components/review/ReviewControls.tsx`
2. Debug review completion state management in `useReviewLogic.ts`
3. ✅ RESOLVED: Removed complex analytics endpoints, using simple dashboard only
4. Fix authentication persistence across navigation

**Medium Priority**:
1. Enforce subscription limits properly for FREE tier users
2. Add error handling for failed API requests
3. ✅ RESOLVED: Optimized React Query usage with simplified dashboard

**Testing Architecture**:
- Use Playwright MCP for systematic E2E testing
- Test mobile-first responsive design
- Verify keyboard shortcuts in review system
- Monitor network requests for performance bottlenecks

### Recent Major Changes (2025-09-25)

**✅ Gamification System Removal**:
- Removed all streak tracking (study_streak_days, current_streak, max_streak)
- Removed achievement statistics and perfect session tracking
- Removed learning efficiency and performance metrics
- Database migration applied: `analytics.0003_remove_gamification_fields`

**✅ Complex Analytics Cleanup**:
- Removed advanced analytics components: ProgressVisualization, LearningCalendar
- Removed chart components: PerformanceMetrics, WeeklyProgressChart, MonthlyTrendsChart, CategoryPieChart
- Removed unused utilities: chart-helpers.ts, WeeklyGoalEditor
- Simplified to basic dashboard with core metrics only

**✅ Frontend Optimization**:
- Removed recharts dependency (123.99 kB bundle reduction)
- Cleaned up unused imports and interfaces
- Simplified SimpleDashboard to focus on essential review metrics

**✅ AI Features Status (Previously Removed)**:
- AI question generation pipeline removed
- Anthropic Claude API integration removed
- AI-powered review suggestions removed
- Legacy environment variables remain but unused

**Current Focus**: Pure spaced repetition learning tool without distractions

## Current System State (2025-09-25)

### ✅ Core Features (Maintained)
- **Ebbinghaus Spaced Repetition**: Scientific review intervals based on subscription tier
- **Content Management**: Create, edit, and organize learning materials
- **Review System**: Structured review workflow with performance tracking
- **Subscription Tiers**: FREE (3-day max), BASIC (90-day), PRO (180-day) intervals
- **User Authentication**: Email-based auth with JWT token management
- **Responsive Design**: Mobile-first design with dark/light theme support

### 🚫 Removed Features (Simplified)
- Streak tracking and gamification elements
- Complex analytics and performance charts
- AI-powered question generation
- Advanced progress visualizations
- Achievement systems and badges
- Weekly goal setting and efficiency metrics

### 📊 Technical Metrics
- **Frontend Bundle**: 283.14 kB (optimized after removing recharts and complex analytics)
- **Code Reduction**: 3,627 lines removed, 243 lines added (massive simplification)
- **Database**: Clean analytics tables with migration applied successfully
- **API Endpoints**: Focused on essential `/api/analytics/dashboard/` only
- **Code Quality**: All ESLint warnings resolved (36 → 0), TypeScript compilation clean
- **Test Coverage**: Backend analytics tests passing (3/3), MCP functionality verified

### 🎯 Architecture Philosophy
**Focus on Learning Effectiveness**:
- Minimize cognitive load and distractions
- Prioritize scientifically-proven spaced repetition
- Simple, intuitive user interface
- Essential metrics only (reviews completed, success rate, content count)
- Fast performance with optimized bundle size