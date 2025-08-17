# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🏗️ Project Overview
Resee is a smart review platform leveraging Ebbinghaus forgetting curve theory. Built with Django (backend) and React (frontend), managed via Docker Compose.

### Core Services
- **Backend**: Django REST Framework + PostgreSQL + Celery
- **Frontend**: React + TypeScript + TailwindCSS  
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

# Create test data
docker-compose exec backend python manage.py create_test_users
docker-compose exec backend python manage.py create_sample_data
docker-compose exec backend python manage.py create_long_term_test_data --tier=pro
docker-compose exec backend python manage.py create_realistic_user_data

# Run tests
docker-compose exec backend pytest
docker-compose exec backend pytest -k "specific_test" -v
docker-compose exec backend pytest --pdb  # Debug on failure

# Django shell
docker-compose exec backend python manage.py shell_plus

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

# Linting and type checking
docker-compose exec frontend npm run lint
docker-compose exec frontend npm run lint:fix
docker-compose exec frontend npm run typecheck

# Build
docker-compose exec frontend npm run build
```

## 🏗️ Architecture Overview

### Backend Structure
```
backend/
├── accounts/      # User authentication, subscriptions
├── content/       # Learning content management
├── review/        # Review scheduling system
├── ai_review/     # AI question generation
├── analytics/     # Learning statistics
├── monitoring/    # System monitoring
├── payments/      # Stripe payment integration
├── legal/         # Terms, privacy policies
└── resee/         # Django settings
```

### Frontend Structure
```
frontend/src/
├── components/    # Reusable components
│   ├── ai/       # AI-related components
│   └── analytics/ # Analytics charts
├── pages/         # Page components
├── contexts/      # Global state (Auth, Theme)
├── hooks/         # Custom React hooks
├── utils/         # API client utilities
├── types/         # TypeScript definitions
└── styles/        # Global styles
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
   - Full intervals: [1, 3, 7, 14, 30, 60, 120, 180 days]
   - FREE: Max 7 days
   - BASIC: Max 30 days
   - PREMIUM: Max 60 days
   - PRO: Max 180 days

### API Authentication
- JWT (Access: 5 min, Refresh: 7 days)
- Email-based login
- Google OAuth 2.0 support

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
- `STRIPE_SECRET_KEY`: Stripe secret key (production)
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook secret

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

## 🧪 Test Accounts
- **Admin**: `admin@resee.com` / `admin123!`
- **Test User**: `test@resee.com` / `test123!`
- **Demo**: `demo@resee.com` / `demo123!`

## 🔍 Key Design Principles

1. **Overdue Review Handling**: Missed reviews don't disappear, shown on current date
2. **Subscription-based Limits**: Each tier has access to specific review ranges
3. **Ebbinghaus Optimization**: Scientifically-based forgetting curve intervals
4. **Real-time Adjustments**: Subscription changes auto-adjust existing schedules
5. **Performance**: React Query for server state caching with immediate invalidation on changes