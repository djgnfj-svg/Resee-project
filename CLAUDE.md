# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🏗️ Project Overview
Resee is a smart review platform leveraging Ebbinghaus forgetting curve theory. Built with Django (backend) and React (frontend), managed via Docker Compose.

### Core Services (5 containers after optimization)
- **Backend**: Django REST Framework + PostgreSQL
- **Frontend**: React + TypeScript + TailwindCSS + TipTap Editor
- **Cache**: Redis (cache + sessions)
- **Reverse Proxy**: Nginx
- **AI Service**: Claude API (Anthropic)

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
```

### Backend Commands
```bash
# Run migrations
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Django shell
docker-compose exec backend python manage.py shell_plus

# Run tests
docker-compose exec backend python -m pytest
docker-compose exec backend python -m pytest accounts/tests.py -v
docker-compose exec backend python -m pytest --cov=. --cov-report=html

# Code quality
docker-compose exec backend black .
docker-compose exec backend flake8
```

### Frontend Commands
```bash
# Run tests
docker-compose exec frontend npm test -- --watchAll=false
docker-compose exec frontend npm run test:coverage
docker-compose exec frontend npm run test:ci

# Linting and type checking
docker-compose exec frontend npm run lint
docker-compose exec frontend npm run lint:fix
docker-compose exec frontend npm run typecheck

# Build
docker-compose exec frontend npm run build
docker-compose exec frontend npm run ci:quick  # Typecheck + build
```

## 🏗️ Architecture Overview

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
   - Reviews are created synchronously on content creation (via Django signals)

2. **Review Intervals by Subscription Tier**:
   - FREE: [1, 3] days
   - BASIC: [1, 3, 7, 14, 30, 60, 90] days
   - PRO: [1, 3, 7, 14, 30, 60, 120, 180] days

3. **Review Process**: remembered → next interval | partial → same interval | forgot → reset to day 1

### API Authentication
- JWT (Access: 60 min, Refresh: 7 days with rotation)
- Email-based login with optional verification
- Google OAuth 2.0 support
- Rate limiting by tier (FREE: 500/hr, BASIC: 1000/hr, PRO: 2000/hr)

## 🌐 Environment Variables

### Required Backend
- `SECRET_KEY`: Django secret key (generate 50+ char random string)
- `ANTHROPIC_API_KEY`: Claude API key
- `DATABASE_URL`: PostgreSQL connection
- `REDIS_URL`: Redis connection

### Required Frontend
- `REACT_APP_API_URL`: Backend API URL
- `REACT_APP_GOOGLE_CLIENT_ID`: Google OAuth client ID (optional)

### Production Settings
- `DEBUG=False`
- `ALLOWED_HOSTS`: Comma-separated domains/IPs
- `CSRF_TRUSTED_ORIGINS`: Comma-separated URLs
- `ENFORCE_EMAIL_VERIFICATION`: Enable for production

## 📋 Core Workflows

### Content Creation Flow
```
User creates content → 
Django signal (content/signals.py) → 
ReviewSchedule created synchronously → 
Available for review next day
```

### AI Features (3 core features)
1. **Weekly Tests**: `/api/ai-review/weekly-test/`
2. **Content Quality Check**: `/api/ai-review/content-check/`
3. **Explanation Evaluation**: `/api/ai-review/explanation-evaluation/`

AI Usage Limits: FREE (0/day), BASIC (30/day), PRO (200/day)

## 🔧 Common Issues & Solutions

### Database Issues
```bash
# Check connection
docker-compose exec backend python manage.py dbshell

# Reset migrations
docker-compose exec backend python manage.py migrate app_name zero
docker-compose exec backend python manage.py migrate app_name
```

### React Query Cache
```typescript
// Force invalidation
queryClient.invalidateQueries(['contents']);
```

### Container Health Issues
```bash
# Restart specific service
docker-compose restart backend

# Rebuild after dependency changes
docker-compose build frontend
docker-compose up -d
```

## 🚀 Deployment

### Quick Production Setup
```bash
# Copy and configure environment
cp .env.example .env.prod
# Edit .env.prod with production values

# For production deployment
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

### Minimum Server Requirements
- 2GB RAM (t3.small or equivalent)
- 20GB storage
- Ubuntu 22.04 LTS
- Docker & Docker Compose installed

## 🔄 Recent Architecture Changes

### Celery & RabbitMQ Removal (Latest)
- All async tasks converted to synchronous processing
- Email sending now uses synchronous EmailService class
- Review schedules created immediately via Django signals
- Reduced containers from 7 to 5 (30% reduction)
- Memory usage reduced by ~40%

### Consolidated Systems
- **Email Service**: All email logic in `backend/accounts/email_service.py`
- **AI Features**: Complete implementation in `backend/ai_review/`
- **Removed Apps**: payments, monitoring apps completely removed

## 📍 Key File Locations

### Core Business Logic
- **Ebbinghaus Algorithm**: `backend/review/utils.py`
- **Email Service**: `backend/accounts/email_service.py`
- **AI Services**: `backend/ai_review/services/`
- **Review Schedule Signal**: `backend/content/signals.py`

### Frontend Key Components  
- **Review Page**: `frontend/src/pages/ReviewPage.tsx` (dual-mode: card/explanation)
- **Content Editor**: `frontend/src/components/TipTapEditor.tsx`
- **Dashboard**: `frontend/src/pages/SimpleDashboard.tsx`
- **API Client**: `frontend/src/utils/api.ts`

### Configuration
- **Django Settings**: `backend/resee/settings/base.py`
- **Docker Compose**: `docker-compose.yml` (dev), `docker-compose.prod.yml` (prod)
- **Frontend Config**: `frontend/package.json`, `frontend/tailwind.config.js`

## 🔍 Development Tips

### When Adding New Features
1. Check subscription tier restrictions in `backend/accounts/models.py`
2. Add appropriate rate limiting in views
3. Update TypeScript types in `frontend/src/types/`
4. Invalidate React Query cache after mutations

### Testing Checklist
- Backend: Run pytest with coverage
- Frontend: Run npm test with coverage (70% threshold)
- Check Docker logs for errors
- Test with different subscription tiers

### Performance Considerations
- Use `select_related()` and `prefetch_related()` for Django queries
- Implement pagination for list views (default: 20 items)
- Use React Query for server state management
- Redis caching for frequently accessed data