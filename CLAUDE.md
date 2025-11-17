# CLAUDE.md

Context for Claude Code when working with this Django + React spaced repetition learning platform.

## Tech Stack

**Backend**
- Django 4.2 + DRF 3.14 (Python 3.11)
- PostgreSQL 15, Redis 7
- Celery 5.3 + django-celery-beat
- Gunicorn (2 workers, 2 threads)
- Anthropic SDK 0.39.0 (claude-3-7-sonnet for validation, claude-3-haiku for evaluation)

**Frontend**
- React 18.2.0 + TypeScript 4.9.3
- React Query 4.16.1, Tailwind CSS 3.2.4
- TipTap 3.0.7, Toss Payments Widget 0.12.0
- 21 pages with React.lazy() code splitting

**Infrastructure**
- Dev: Docker Compose
- **Prod (Current)**: Railway (Django + Celery), Supabase PostgreSQL, Upstash Redis, Vercel (frontend)
- **Prod (Legacy)**: AWS ECS Fargate (deprecated, migrated to Railway for 90% cost reduction)

---

## Quick Start

```bash
# Start dev environment
docker-compose up -d
docker-compose logs -f backend

# Access (Development)
http://localhost              # Nginx (production-like)
http://localhost:3000         # React dev server
http://localhost:8000/api     # Django API
http://localhost/api/docs/    # Swagger UI

# Access (Production)
https://reseeall.com                                    # Frontend (Vercel)
https://resee-project-production.up.railway.app/api    # Backend API (Railway)
https://resee-project-production.up.railway.app/api/docs/  # API Documentation

# Test accounts
interview@resee.com / interview2025!   # PRO tier
admin@resee.com / admin123!            # BASIC tier, staff
```

---

## Development Commands

### Backend
```bash
# Migrations
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate

# Tests & Coverage
docker-compose exec backend python -m pytest
docker-compose exec backend python -m pytest --cov=. --cov-report=html

# Shell & Formatting
docker-compose exec backend python manage.py shell_plus
docker-compose exec backend black .

# Health Check
docker-compose exec backend python manage.py health_check
```

### Frontend
```bash
# Tests
docker-compose exec frontend npm test -- --watchAll=false
docker-compose exec frontend npm run test:coverage

# Linting (REQUIRED before commit)
docker-compose exec frontend npm run lint
docker-compose exec frontend npm run typecheck

# Build & Bundle Analysis
docker-compose exec frontend npm run build
docker-compose exec frontend npm run analyze
```

### Production (AWS ECS)
```bash
# Cluster & Services
aws ecs list-clusters
aws ecs describe-services --cluster resee-cluster --services resee-backend-service

# Task Status
aws ecs list-tasks --cluster resee-cluster --service-name resee-backend-service
aws ecs describe-tasks --cluster resee-cluster --tasks <task-id>

# ALB Health
aws elbv2 describe-load-balancers --names resee-alb
curl http://resee-alb-64869428.ap-northeast-2.elb.amazonaws.com/api/health/
curl http://resee-alb-64869428.ap-northeast-2.elb.amazonaws.com/api/health/detailed/
```

---

## Code Style Guidelines

### Backend (Django)

**MUST Rules** (enforced by CI):
- Use Black for formatting: `black .`
- Run tests before commit: `pytest --cov=.`
- Use `select_related()` for ForeignKey, `prefetch_related()` for ManyToMany
- Check subscription tier with `@has_subscription_permission` decorator
- Validate AI service availability before use: `if service.is_available()`
- Add rate limiting for new endpoints (DRF throttling classes)

**Patterns**:
- Service layer: `SubscriptionService`, `PermissionService` in `accounts/subscription/services.py`
- Signal-based automation: `content/signals.py` auto-creates ReviewSchedule
- Async tasks: Use Celery for email, backups, AI operations
- Singleton pattern: All AI services in `backend/ai_services/`

**Performance**:
- Use locmem cache for expensive operations (24h TTL)
- Pagination: 20 items/page default
- Monitor Redis throttle cache usage

### Frontend (React + TypeScript)

**MUST Rules** (enforced by CI):
- Run linting: `npm run lint` and `npm run typecheck`
- Update TypeScript types in `frontend/src/types/`
- Invalidate React Query cache after mutations
- Use React.lazy() for new pages
- Test coverage: 70% minimum

**Patterns**:
- Server state: React Query (retry: 1, refetchOnWindowFocus: false)
- Auth: JWT in memory (`utils/api.ts` interceptor), NO localStorage
- Routing: All pages lazy-loaded, use `<ProtectedRoute>` for auth-required pages
- API clients: Modular pattern in `utils/api/`

**State Management**:
- Server state → React Query
- Auth → Context API (AuthContext.tsx)
- Theme → Context API (ThemeContext.tsx)
- Local → useState/useReducer

**Performance**:
- Tree shaking: `sideEffects` in package.json
- Bundle target: <300 kB main bundle
- All pages use code splitting

---

## Git Workflow

### Commit Message Format

Follow the conventional commits pattern with detailed body:

```
type(scope): Brief description (50 chars max)

**Section Title** (if multiple changes):
- Bullet point explaining what changed
- Why this change was needed
- Technical details if relevant

**Another Section** (optional):
- More changes grouped logically

**Test Results** (if applicable):
- Test coverage or validation results

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Add or update tests
- `refactor`: Code refactoring
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

**Scopes** (optional):
- `ci`, `exams`, `review`, `content`, `accounts`, `frontend`, etc.

**Examples**:
```bash
# Simple fix
fix(ci): Fix CI failures - frontend types and backend dependencies

# Feature with details
feat(exams): Implement async exam question generation with polling

**Backend**:
- Add polling endpoint for exam status
- Implement Celery task for async generation
- Add rate limiting (5 req/min per user)

**Frontend**:
- Add loading state with progress indicator
- Implement auto-refresh polling every 2s
```

---

## Testing Requirements

**CRITICAL: Always use MCP Playwright for end-to-end testing**

When testing features:
- ✅ Use MCP Playwright browser testing (navigate, click, fill, verify)
- ✅ Check browser console for errors
- ❌ DO NOT use curl for testing user-facing features
- ❌ DO NOT test APIs in isolation without UI verification

**Example Flow**:
```
1. Start: docker-compose up -d
2. MCP Playwright:
   - Navigate to page
   - Interact with UI
   - Verify changes visually
   - Check console errors
3. Use curl/shell only for backend debugging
```

---

## Project Structure

### Backend Critical Files
```
backend/
├── ai_services/           # Centralized AI (BaseAIService pattern)
│   ├── validators/        # Content validation (claude-3-7-sonnet)
│   ├── evaluators/        # Answer/title eval (claude-3-haiku)
│   └── generators/        # MC/question gen (LangChain + LangGraph)
├── accounts/
│   ├── auth/              # JWT login/logout/refresh
│   ├── subscription/      # Tier mgmt, Toss Payments, billing
│   └── email/             # Verification, password reset
├── content/               # Learning material CRUD, signals
├── review/                # Ebbinghaus algorithm, AI evaluation
├── exams/                 # AI-generated tests
├── resee/
│   ├── settings/          # base.py, development.py, production.py
│   ├── views.py           # health_check function
│   ├── celery.py          # Celery config
│   ├── throttling.py      # Redis rate limiting
│   └── permissions.py     # Tier-based access control
└── utils/
    └── slack_notifications.py  # SlackNotifier class
```

### Frontend Critical Files
```
frontend/src/
├── App.tsx                # Main app, lazy loading 21 pages
├── utils/
│   ├── api.ts             # JWT interceptor, auto-refresh
│   └── api/               # Modular API clients (auth, content, review, etc.)
├── contexts/              # AuthContext, ThemeContext
├── pages/                 # 21 lazy-loaded pages
├── components/            # Feature-based organization
└── types/                 # TypeScript definitions
```

### Configuration Files
```
docker-compose.yml         # Local dev (runserver, npm start)
docker-compose.prod.yml    # Local prod-like (gunicorn, nginx)
.env                       # Dev environment
.env.prod                  # Prod environment (AWS ECS)
.github/workflows/         # CI/CD (AWS ECS deployment)
```

---

## Railway Production Infrastructure (Current)

**Platform**: Railway (us-west1)
- URL: `https://resee-project-production.up.railway.app`
- Services: Django Backend + Celery (Worker + Beat)
- Deployment: Auto-deploy from GitHub `main` branch
- Cost: ~$5-10/month (90% cheaper than AWS ECS)

**Database**: Supabase PostgreSQL 15
- Host: `aws-1-ap-southeast-2.pooler.supabase.com:6543`
- Connection: Pooler (Transaction Mode)
- Response time: ~200ms
- Automatic backups: Daily

**Cache & Broker**: Upstash Redis
- Host: `calm-jaybird-34425.upstash.io:6379`
- Protocol: rediss:// (TLS)
- Usage: Celery broker + rate limiting + Django cache
- Response time: ~230ms

**Frontend**: Vercel
- Domain: `reseeall.com`
- React deployment, global CDN, HTTPS

**Architecture Flow**:
```
User → Vercel (reseeall.com)
     → Railway Backend (Django + Celery) → Supabase PostgreSQL
                                        → Upstash Redis
```

**Environment Variables** (Railway):
```bash
# Core
SECRET_KEY=<production-key>
DEBUG=False
DJANGO_SETTINGS_MODULE=resee.settings.production
ALLOWED_HOSTS=reseeall.com,www.reseeall.com,.up.railway.app,healthcheck.railway.app

# Database & Cache
DATABASE_URL=postgresql://postgres.xxx:password@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres
REDIS_URL=rediss://default:password@calm-jaybird-34425.upstash.io:6379

# Services
ANTHROPIC_API_KEY=sk-ant-api03-...
FRONTEND_URL=https://reseeall.com
```

**Deployment Files**:
- `Dockerfile` (root) - Railway build configuration
- `railway.toml` - Railway settings (healthcheck, restart policy)
- `.env.production` - Environment variables template

---

## AWS ECS Infrastructure (Legacy - Deprecated)

**ECS Cluster**: `resee-cluster` (ap-northeast-2)
- Services: `resee-backend-service`, `resee-celery-worker-service`, `resee-celery-beat-service`
- Task Type: Fargate (serverless)
- Deployment: Rolling updates via GitHub Actions

**Application Load Balancer**:
- Name: `resee-alb`
- DNS: `resee-alb-64869428.ap-northeast-2.elb.amazonaws.com`
- Listener: Port 80 → Target Group `resee-backend-tg` (port 8000)
- Health Check: `/api/health/` (30s interval, 10s timeout)
- Availability Zones: ap-northeast-2a, ap-northeast-2c

**Database**: AWS RDS PostgreSQL 15 (`resee_prod`)
- Response time: ~290ms
- Automatic backups enabled

**Cache & Broker**: Upstash Redis
- Host: `calm-jaybird-34425.upstash.io:6379`
- Protocol: rediss:// (TLS)
- Usage: Celery broker + rate limiting
- Response time: ~230ms

**Frontend**: Vercel
- React deployment, global CDN, HTTPS

**Architecture Flow**:
```
User → Vercel (Frontend)
     → AWS ALB → ECS Backend (Gunicorn) → RDS PostgreSQL
                                        → Upstash Redis
     → ECS Celery Worker/Beat → Upstash Redis
```

---

## Environment Variables

### Development (.env)
```bash
SECRET_KEY=your-secret-key
DEBUG=True
DJANGO_SETTINGS_MODULE=resee.settings.development
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/resee_dev
REDIS_URL=redis://redis:6379/0  # Set in docker-compose.yml

ANTHROPIC_API_KEY=sk-ant-api...  # Required for AI services
FRONTEND_URL=http://localhost

# Optional
SLACK_WEBHOOK_URL=your-webhook-url
```

### Production - Railway (Current)
```bash
# Railway Variables (set in Railway dashboard)
SECRET_KEY=<production-key>
DEBUG=False
DJANGO_SETTINGS_MODULE=resee.settings.production
TIME_ZONE=Asia/Seoul
ALLOWED_HOSTS=reseeall.com,www.reseeall.com,.up.railway.app,healthcheck.railway.app
CSRF_TRUSTED_ORIGINS=https://reseeall.com,https://www.reseeall.com,https://*.up.railway.app

# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql://postgres.xxx:password@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres

# Cache & Broker (Upstash Redis)
REDIS_URL=rediss://default:password@calm-jaybird-34425.upstash.io:6379

# AI & Frontend
ANTHROPIC_API_KEY=sk-ant-api03-...
FRONTEND_URL=https://reseeall.com

# Email (Gmail SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=reseeall2025@gmail.com
EMAIL_HOST_PASSWORD=<app-password>
DEFAULT_FROM_EMAIL=noreply@reseeall.com

# Monitoring (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_DEFAULT_CHANNEL=#alerts
```

### Production - AWS ECS (Legacy)
```bash
SECRET_KEY=your-production-key
DEBUG=False
DJANGO_SETTINGS_MODULE=resee.settings.production
ALLOWED_HOSTS=resee-alb-64869428.ap-northeast-2.elb.amazonaws.com,yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com

DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/resee_prod
REDIS_URL=rediss://default:pass@calm-jaybird-34425.upstash.io:6379

ANTHROPIC_API_KEY=sk-ant-api...  # Required
FRONTEND_URL=https://your-vercel-domain.vercel.app

# Email (Gmail SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Monitoring
SLACK_WEBHOOK_URL=your-webhook-url
SLACK_DEFAULT_CHANNEL=#alerts
```

---

## Feature Development Checklist

When adding new features:
- [ ] Check tier restrictions (`PermissionService`)
- [ ] Add rate limiting if needed
- [ ] Update TypeScript types
- [ ] Invalidate React Query cache after mutations
- [ ] Use `select_related()`/`prefetch_related()`
- [ ] Pagination (20 items/page)
- [ ] Tests (70% coverage minimum)
- [ ] Linting: `npm run lint`, `black .`
- [ ] Check AI service availability

---

## Security

**Rate Limiting** (Redis-based):
- Anonymous: 100 req/hour
- Authenticated: 1000 req/hour
- Login: 5 req/minute
- Registration: 3 req/minute

**Authentication**:
- JWT tokens in memory (NO localStorage)
- Email verification: SHA-256 hashed tokens
- Token comparison: constant-time (`secrets.compare_digest`)
- CSRF protection enabled

**Headers**:
- XSS Protection: `1; mode=block`
- HSTS: max-age 31536000
- X-Frame-Options: DENY
- Content-Type-Options: nosniff

---

## Key Files Reference

**Core Algorithm**: `backend/review/utils.py:calculate_next_review_date()`
**JWT Interceptor**: `frontend/src/utils/api.ts`
**Auth Flow**: `backend/accounts/auth/views.py`
**Permissions**: `backend/resee/permissions.py`
**AI Services**: `backend/ai_services/base.py` (BaseAIService)
**Signals**: `backend/content/signals.py` (ReviewSchedule auto-creation)
**Celery Config**: `backend/resee/celery.py`
**Rate Limiting**: `backend/resee/throttling.py`

---

## Monitoring

**Health Endpoints**:
- `/api/health/` - Basic (DB ping)
- `/api/health/detailed/` - Full system (DB, Redis, Celery, Disk)

**Logging** (JSON format):
- django.log (10MB, 5 backups)
- celery.log
- security.log
- error.log

**Slack Alerts** (9+ triggers):
- DB/Redis connection failures
- Disk >80%, Celery worker failures
- Backup failures, payment failures
- API >2s response, error rate >10/min

**Utils**:
- `backend/utils/slack_notifications.py` - SlackNotifier
- `backend/resee/views.py` - health_check function
