# Resee AWS 아키텍처

## 전체 인프라 구조

```mermaid
graph TB
    subgraph "Internet"
        Users[👤 Users]
    end

    subgraph "CloudFlare CDN"
        CF[CloudFlare<br/>HTTPS/CDN<br/>reseeall.com]
    end

    subgraph "AWS EC2 Instance"
        subgraph "Docker Compose"
            Nginx[Nginx<br/>:80<br/>Reverse Proxy]
            Frontend[React Frontend<br/>SPA]
            Backend[Django Backend<br/>Gunicorn<br/>:8000]

            subgraph "Data Layer"
                Postgres[(PostgreSQL<br/>:5432<br/>resee_prod)]
                Redis[(Redis<br/>:6379<br/>Cache/Queue)]
            end

            subgraph "Background Jobs"
                Celery[Celery Worker<br/>Email/Backup]
                CeleryBeat[Celery Beat<br/>Scheduler]
            end
        end

        subgraph "Docker Volumes"
            PGData[postgres_data]
            RedisData[redis_data]
            StaticFiles[frontend_build]
        end
    end

    subgraph "CI/CD"
        GitHub[GitHub Actions]
        CI[CI Pipeline<br/>TypeScript/ESLint<br/>pytest/black]
        CD[CD Pipeline<br/>SSH Deploy]
    end

    subgraph "External Services"
        Anthropic[Anthropic API<br/>Claude AI]
        Gmail[Gmail SMTP<br/>Email Service]
        Slack[Slack Webhook<br/>Alerts]
    end

    Users -->|HTTPS| CF
    CF -->|Port 80| Nginx
    Nginx -->|/api| Backend
    Nginx -->|/| Frontend
    Backend --> Postgres
    Backend --> Redis
    Celery --> Redis
    Celery --> Postgres
    CeleryBeat --> Redis

    Postgres -.->|Volume| PGData
    Redis -.->|Volume| RedisData
    Frontend -.->|Volume| StaticFiles

    GitHub --> CI
    CI -->|Tests Pass| CD
    CD -->|SSH| Backend

    Backend -.->|AI Evaluation| Anthropic
    Celery -.->|Send Email| Gmail
    Celery -.->|Send Alert| Slack

    style CF fill:#f96,stroke:#333,stroke-width:2px
    style Nginx fill:#9f6,stroke:#333,stroke-width:2px
    style Backend fill:#69f,stroke:#333,stroke-width:2px
    style Postgres fill:#f9f,stroke:#333,stroke-width:2px
    style Redis fill:#ff9,stroke:#333,stroke-width:2px
    style Celery fill:#6ff,stroke:#333,stroke-width:2px
```

## 상세 네트워크 플로우

```mermaid
sequenceDiagram
    participant User
    participant CloudFlare
    participant Nginx
    participant Frontend
    participant Backend
    participant Redis
    participant Postgres
    participant Celery

    User->>CloudFlare: HTTPS Request (reseeall.com)
    CloudFlare->>Nginx: Forward to EC2:80

    alt Static Files Request
        Nginx->>Frontend: Serve React SPA
        Frontend-->>User: HTML/JS/CSS
    else API Request
        Nginx->>Backend: Proxy to Django:8000
        Backend->>Redis: Check Cache
        alt Cache Hit
            Redis-->>Backend: Cached Data
        else Cache Miss
            Backend->>Postgres: Query Database
            Postgres-->>Backend: Data
            Backend->>Redis: Store Cache
        end
        Backend-->>User: JSON Response
    end

    alt Background Task
        Backend->>Redis: Enqueue Task
        Celery->>Redis: Dequeue Task
        Celery->>Postgres: Process Task
        Celery->>Gmail: Send Email
    end
```

## Docker 컨테이너 구성

```mermaid
graph LR
    subgraph "Port 80"
        Nginx[nginx:alpine<br/>Reverse Proxy]
    end

    subgraph "Frontend"
        React[node:18<br/>React Build]
    end

    subgraph "Backend"
        Django[python:3.11<br/>Django + Gunicorn<br/>1 worker, 2 threads]
    end

    subgraph "Database"
        PG[postgres:15<br/>5GB Storage]
    end

    subgraph "Cache/Queue"
        RD[redis:7-alpine<br/>AOF Persistence]
    end

    subgraph "Workers"
        CW[Celery Worker<br/>Concurrency: 4]
        CB[Celery Beat<br/>DatabaseScheduler]
    end

    Nginx -->|/| React
    Nginx -->|/api| Django
    Django --> PG
    Django --> RD
    CW --> RD
    CW --> PG
    CB --> RD

    style Nginx fill:#90EE90
    style Django fill:#87CEEB
    style PG fill:#FFB6C1
    style RD fill:#FFD700
    style CW fill:#DDA0DD
```

## CI/CD 파이프라인

```mermaid
graph TD
    Start[git push main] --> GH[GitHub Actions Trigger]

    subgraph "CI Stage"
        GH --> FE[Frontend Tests]
        GH --> BE[Backend Tests]

        FE --> TS[TypeScript Check]
        FE --> ES[ESLint]
        FE --> FB[npm run build]

        BE --> PT[pytest]
        BE --> BL[black --check]
        BE --> FL[flake8]
    end

    FB --> Check{All Tests<br/>Passed?}
    FL --> Check

    Check -->|Yes| CD[CD Stage]
    Check -->|No| Fail[❌ Deployment Blocked]

    subgraph "CD Stage"
        CD --> SSH[SSH to EC2]
        SSH --> Pull[git pull]
        Pull --> Deploy[./deploy.sh]

        Deploy --> Env[Validate .env.prod]
        Env --> Down[docker-compose down]
        Down --> Build[Sequential Build]
        Build --> Migrate[DB Migration]
        Migrate --> Collect[collectstatic]
        Collect --> Up[Start Services]
        Up --> Health[Health Check]
    end

    Health -->|Success| Done[✅ Deployment Complete]
    Health -->|Fail| Rollback[❌ Rollback]

    style Check fill:#FFD700
    style Done fill:#90EE90
    style Fail fill:#FF6B6B
    style Rollback fill:#FF6B6B
```

## 데이터 흐름

```mermaid
graph LR
    subgraph "User Actions"
        Login[Login]
        Review[Submit Review]
        Create[Create Content]
    end

    subgraph "API Layer"
        Auth[JWT Auth]
        Rate[Rate Limiting<br/>Redis]
        Cache[Cache Layer<br/>Redis]
    end

    subgraph "Business Logic"
        Django[Django Views]
        AI[Claude API<br/>AI Evaluation]
    end

    subgraph "Data Storage"
        DB[(PostgreSQL)]
        RedisQ[Redis Queue]
    end

    subgraph "Background"
        Worker[Celery Worker]
        Email[Gmail SMTP]
        Backup[pg_dump]
    end

    Login --> Auth
    Review --> Auth
    Create --> Auth

    Auth --> Rate
    Rate --> Cache
    Cache -->|Cache Miss| Django
    Django --> DB
    Django -.->|Async| AI

    Django --> RedisQ
    RedisQ --> Worker
    Worker --> Email
    Worker --> Backup

    style Auth fill:#87CEEB
    style Rate fill:#FFD700
    style Cache fill:#FFD700
    style AI fill:#DDA0DD
```

## 보안 구조

```mermaid
graph TB
    subgraph "External"
        Internet[Internet Users]
    end

    subgraph "Edge Security"
        CF[CloudFlare<br/>DDoS Protection<br/>HTTPS/SSL]
    end

    subgraph "Application Security"
        Rate[Rate Limiting<br/>5/min login<br/>100/hour anon]
        JWT[JWT Auth<br/>Access + Refresh]
        CORS[CORS Policy]
        CSRF[CSRF Protection]
    end

    subgraph "Data Security"
        Hash[SHA-256 Hashing<br/>Email Tokens]
        Const[Constant-time Compare<br/>Timing Attack Prevention]
        Encrypt[Database Encryption<br/>at Rest]
    end

    subgraph "Network Security"
        Private[Private Docker Network<br/>No External Ports]
        Nginx[Nginx Reverse Proxy<br/>Only Port 80]
    end

    Internet -->|Attack| CF
    CF -->|Filtered| Rate
    Rate --> JWT
    JWT --> CORS
    CORS --> CSRF
    CSRF --> Hash
    Hash --> Const
    Const --> Encrypt
    Encrypt --> Private
    Private --> Nginx

    style CF fill:#FF6B6B
    style Rate fill:#FFD700
    style JWT fill:#87CEEB
    style Hash fill:#90EE90
    style Private fill:#DDA0DD
```

---

## 주요 특징

### 1. 단일 EC2 구성
- **비용 효율성**: 모든 서비스를 하나의 EC2 인스턴스에서 Docker Compose로 관리
- **로컬 PostgreSQL**: RDS 대신 Docker 볼륨으로 데이터 영구 저장
- **Swap 메모리**: 2GB Swap으로 메모리 부족 방지

### 2. CloudFlare CDN
- HTTPS/SSL 자동 관리
- DDoS 보호
- 전역 캐싱

### 3. Docker 네트워크
- 모든 컨테이너는 private network에서만 통신
- Nginx만 외부 포트 80 노출
- PostgreSQL, Redis는 외부 접근 불가

### 4. CI/CD 자동화
- main 브랜치 푸시 시 자동 테스트
- 테스트 통과 시 자동 배포 (5분)
- 배포 실패율 0%

### 5. 모니터링
- Health check endpoint: `/api/health/`
- Celery 작업 모니터링
- Slack 알림 (백업, 에러)

---

**작성일**: 2025-10-22
**도메인**: https://reseeall.com
**인프라**: AWS EC2 + CloudFlare + Docker Compose
