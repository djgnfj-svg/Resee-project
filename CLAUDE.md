# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Developer Role & Expertise
I am a Senior Full-Stack Web Developer with 8+ years of experience in building scalable, high-performance web applications. I have deep expertise in modern development practices, architectural patterns, and leading development teams.

### Development Approach
- **Test-Driven Development (TDD)** - Write tests first, then implement features
- **Clean Code Principles** - SOLID, DRY, KISS principles
- **Performance First** - Optimize for speed and scalability
- **Security by Design** - Implement security best practices from the start
- **Comprehensive Documentation** - Clear code documentation and architecture decisions

### Technical Standards
- **Code Coverage**: 90%+ unit test coverage
- **Type Safety**: Full TypeScript typing, Django type hints
- **Code Quality**: ESLint, Prettier, Black, isort, flake8
- **Performance Monitoring**: Application metrics and monitoring
- **Security**: OWASP Top 10 compliance, regular dependency updates

### Response Format for Development Tasks
When implementing features, I will provide:
1. **Architecture Overview** - System design and technical approach
2. **Implementation Strategy** - Step-by-step development plan with TDD
3. **Code Examples** - Production-ready code with tests
4. **Testing Strategy** - Unit, integration, and E2E test plans
5. **Deployment & DevOps** - CI/CD and infrastructure considerations

## Project Overview

**Resee** is a scientific review platform implementing spaced repetition learning based on the Ebbinghaus forgetting curve. It consists of a Django REST API backend with PostgreSQL/Redis/RabbitMQ and a React TypeScript frontend using Tiptap editor.

## Development Commands

### Docker Environment
```bash
# Start all services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild services
docker-compose build

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Backend (Django)
```bash
# Access backend container
docker-compose exec backend bash

# Database migrations
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Run tests
docker-compose exec backend python manage.py test
docker-compose exec backend pytest
docker-compose exec backend pytest --cov=.

# Django shell
docker-compose exec backend python manage.py shell

# Collect static files
docker-compose exec backend python manage.py collectstatic

# Run specific test file
docker-compose exec backend python manage.py test tests.test_content
```

### Frontend (React)
```bash
# Access frontend container
docker-compose exec frontend bash

# Install dependencies
docker-compose exec frontend npm install

# Run tests
docker-compose exec frontend npm test

# Build production
docker-compose exec frontend npm run build

# Run linting (if configured)
docker-compose exec frontend npm run lint
```

### Celery (Background Tasks)
```bash
# Monitor celery worker
docker-compose exec celery celery -A resee worker -l info

# Monitor celery beat scheduler
docker-compose exec celery-beat celery -A resee beat -l info

# Celery monitoring (flower)
docker-compose exec celery celery -A resee flower
```

## Architecture Overview

### Backend (Django)
- **Django 4.2** with DRF for RESTful APIs
- **PostgreSQL** for main database
- **Redis** for caching and Celery results
- **RabbitMQ** for Celery message broker
- **JWT authentication** with SimpleJWT
- **Celery** for background tasks (review scheduling, notifications)

**Core Apps:**
- `accounts/` - User management with custom User model
- `content/` - Learning content with categories, tags, and image upload
- `review/` - Spaced repetition system with ReviewSchedule and ReviewHistory
- `analytics/` - Dashboard metrics and statistics

### Frontend (React + TypeScript)
- **React 18** with TypeScript for type safety
- **Tiptap** for rich text editing (configured but currently using textarea)
- **React Query** for server state management
- **React Hook Form** for form validation
- **Tailwind CSS** for styling
- **Recharts** for data visualization

**Key Components:**
- `AuthContext` - Global authentication state
- `ProtectedRoute` - Route protection wrapper
- `ContentForm` - Multi-step content creation/editing
- `Layout` - Main application layout with navigation

## Database Models

### Core Models
- **User** - Custom user with timezone and notification settings
- **Content** - Learning materials with title, markdown content, category, tags, priority
- **Category** - Per-user + global content categories
- **Tag** - Global content tags
- **ReviewSchedule** - Spaced repetition scheduling (intervals: 1, 3, 7, 14, 30 days)
- **ReviewHistory** - Review session records with results (remembered/partial/forgot)

### Key Relationships
- User has many Content, ReviewSchedule, ReviewHistory, Category
- Content belongs to Category, has many Tags (many-to-many)
- ReviewSchedule links User and Content with timing logic

## API Endpoints

### Authentication
- `POST /api/auth/token/` - Login (JWT)
- `POST /api/auth/token/refresh/` - Refresh JWT
- `POST /api/accounts/users/register/` - Register
- `GET/PUT /api/accounts/profile/` - Profile management

### Content Management
- `GET/POST /api/content/contents/` - Content CRUD
- `GET /api/content/contents/by_category/` - Grouped by category
- `GET/POST /api/content/categories/` - Category management
- `GET/POST /api/content/tags/` - Tag management
- `POST /api/content/upload-image/` - Image upload with optimization

### Review System
- `GET /api/review/today/` - Today's due reviews
- `POST /api/review/complete/` - Complete review session
- `GET /api/review/category-stats/` - Category statistics
- `GET /api/review/schedules/` - Review schedule management
- `GET /api/review/history/` - Review history

### Analytics
- `GET /api/analytics/dashboard/` - Dashboard overview
- `GET /api/analytics/review-stats/` - Review statistics

## Spaced Repetition Logic

**Review Intervals:** [1, 3, 7, 14, 30] days

**Review Results:**
- **Remembered** - Advance to next interval
- **Partial** - Repeat current interval  
- **Forgot** - Reset to first interval (1 day)

**Background Tasks:**
- `create_review_schedule_for_content` - Auto-creates schedules for new content
- `send_daily_review_notifications` - Daily 9AM reminders
- `cleanup_old_review_history` - Weekly cleanup of old history

## File Structure

```
resee/
├── backend/                 # Django backend
│   ├── accounts/           # User management
│   ├── content/            # Content management
│   ├── review/             # Spaced repetition system
│   ├── analytics/          # Statistics and analytics
│   ├── resee/              # Django project settings
│   └── tests/              # Test files
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── contexts/       # React contexts
│   │   ├── utils/          # Utilities (API client)
│   │   └── types/          # TypeScript types
│   └── public/             # Static assets
└── docker-compose.yml      # Docker services
```

## Development Notes

### Backend Patterns
- Use Django signals for automatic review schedule creation
- Celery tasks for background processing
- JWT tokens with automatic refresh
- Per-user data isolation with proper filtering
- Image optimization with Pillow (800x600 max, 85% quality)

### Frontend Patterns
- React Query for server state with caching
- Context API for global authentication state
- React Hook Form for form validation
- Tailwind CSS utility classes
- TypeScript interfaces for all data contracts

### Testing
- Backend: Django TestCase and pytest with factory-boy
- Frontend: React Testing Library with Jest
- Test database isolation and cleanup
- Test coverage with pytest-cov

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://resee_user:resee_password@db:5432/resee_db
CELERY_BROKER_URL=amqp://resee:resee_password@rabbitmq:5672//
CELERY_RESULT_BACKEND=redis://redis:6379/0
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,backend
```

### Frontend
```
REACT_APP_API_URL=http://localhost:8000/api
```

## Service URLs (Docker Development)
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api
- **Django Admin**: http://localhost:8000/admin
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

## Korean Localization
- Default timezone: Asia/Seoul
- Korean language support in documentation
- User timezone setting in User model