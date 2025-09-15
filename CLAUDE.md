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

### Environment Files
- **`.env`**: Development environment (DEBUG=True, localhost URLs)
- **`.env.prod`**: Production environment (DEBUG=False, production URLs)

### Development Environment (`.env`)
```bash
# Core Settings
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DJANGO_SETTINGS_MODULE=resee.settings.development
FRONTEND_URL=http://localhost:3000
REACT_APP_API_URL=http://localhost:8000/api

# Email Settings (for testing)
ENFORCE_EMAIL_VERIFICATION=True  # Set to False to skip email verification
```

### Production Environment (`.env.prod`)
```bash
# Core Settings
DEBUG=False
ALLOWED_HOSTS=reseeall.com,www.reseeall.com
DJANGO_SETTINGS_MODULE=resee.settings.production
FRONTEND_URL=https://reseeall.com
REACT_APP_API_URL=https://reseeall.com/api

# Email Settings
ENFORCE_EMAIL_VERIFICATION=True  # Always True in production
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
```

### Required Backend Variables
- `SECRET_KEY`: Django secret key (generate 50+ char random string)
- `ANTHROPIC_API_KEY`: Claude API key
- `DATABASE_URL`: PostgreSQL connection
- `REDIS_URL`: Redis connection
- `FRONTEND_URL`: Frontend URL for email links
- `ENFORCE_EMAIL_VERIFICATION`: Enable/disable email verification

### Required Frontend Variables
- `REACT_APP_API_URL`: Backend API URL
- `REACT_APP_GOOGLE_CLIENT_ID`: Google OAuth client ID (optional)

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

### Development Deployment
```bash
# 1. 환경 설정 파일 준비
cp .env.example .env
# .env 파일을 편집하여 필요한 값들을 설정

# 2. 개발 환경 시작
docker-compose up -d

# 3. 초기 설정
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser

# 4. 헬스체크 확인
curl http://localhost:8000/api/health/
```

### Production Deployment
```bash
# 1. 환경 설정 파일 준비
cp .env.example .env.prod
# .env.prod 파일을 편집하여 프로덕션 값들을 설정

# 2. 보안 검사 실행
docker-compose exec backend python manage.py health_check --detailed

# 3. 프로덕션 빌드 및 시작
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# 4. 초기 설정
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --noinput

# 5. 최종 헬스체크
curl https://your-domain.com/api/health/detailed/
```

### 🔐 보안 체크리스트
- [ ] `.env` 파일의 모든 비밀번호와 키 변경
- [ ] `SECRET_KEY` 50자 이상 랜덤 문자열로 설정
- [ ] `DEBUG=False` (프로덕션)
- [ ] `ALLOWED_HOSTS` 정확한 도메인으로 설정
- [ ] HTTPS 인증서 설정
- [ ] 방화벽 설정 (필요한 포트만 오픈)

### Environment File Usage
- **Development**: `.env` 파일 사용 (템플릿: `.env.example`)
- **Production**: `.env.prod` 파일 사용
- **Email Verification**: `ENFORCE_EMAIL_VERIFICATION` 설정으로 제어
- **AI Services**: `AI_USE_MOCK_RESPONSES=True`로 개발 중 비용 절약

### Minimum Server Requirements
- **Development**: 2GB RAM, 10GB storage
- **Production**: 4GB RAM, 20GB storage, SSD 권장
- **OS**: Ubuntu 22.04 LTS 또는 최신 안정 버전
- **Docker**: Docker Engine 20.10+ & Docker Compose v2

## 🔄 Recent Architecture Changes

### Data Management System Simplification (Latest)
- **Over-engineering Cleanup**: Removed ~3,000 lines of excessive infrastructure
- **Backup System**: Simplified from 5 complex scripts to 1 basic PostgreSQL dump
- **Monitoring**: Removed real-time performance middleware (244 lines)
- **Management Commands**: Removed auto-repair and capacity systems (707 lines)
- **Result**: 90% code reduction while maintaining core performance gains

### Database Performance Optimization
- **Strategic Indexes**: Added to ReviewSchedule, ReviewHistory, Content models
- **N+1 Query Fixes**: 75-80% API response time improvement
- **Query Optimization**: select_related/prefetch_related implementation
- **Performance Gains**: TodayReviewView (200ms→50ms), CategoryStats (500ms→100ms)

### Security & Production Hardening (2025-09-15)
- **Environment Security**: Removed hardcoded secrets from docker-compose.yml
- **Django Security**: Enhanced CORS, CSP, session/cookie security settings
- **Docker Optimization**: Multi-stage builds, non-root users, health checks
- **Dependency Updates**: Updated to latest stable versions (Django 4.2.16, etc.)
- **Monitoring**: Added comprehensive health check endpoints
- **Production Ready**: Optimized configurations for production deployment

### Previous Changes
- **Celery & RabbitMQ Removal**: Async tasks → synchronous processing
- **Container Optimization**: 7 → 5 containers (30% reduction)
- **Memory Usage**: ~40% reduction through simplification

### Simplified Infrastructure
- **Email Service**: All email logic in `backend/accounts/email_service.py`
- **AI Features**: Complete implementation in `backend/ai_review/`
- **Backup**: Simple script at `scripts/backup_database.sh`
- **Removed**: Complex monitoring middleware, management commands, backup automation

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