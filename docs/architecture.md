# Architecture

## System Overview

Text2Img is a multi-service application designed for real-time AI image generation. The architecture follows a microservices-inspired pattern where each service has a single responsibility, communicating via HTTP (REST), Redis (pub/sub for SSE), and a message queue (Celery for async job processing).

## High-Level Architecture

```
                        ┌─────────────────────────┐
                        │        Internet          │
                        └────────────┬────────────┘
                                     │
                        ┌────────────▼────────────┐
                        │    Nginx Reverse Proxy   │
                        │  • TLS termination       │
                        │  • Rate limiting         │
                        │  • Static file caching   │
                        │  • SSE pass-through      │
                        └───────┬─────────┬───────┘
                                │         │
               ┌────────────────▼─┐   ┌───▼────────────────┐
               │    Frontend       │   │     Backend         │
               │  Next.js 14       │   │  FastAPI + Uvicorn  │
               │  • SSR/SSG        │   │  • REST API         │
               │  • React 18       │   │  • SSE streaming    │
               │  • Zustand store  │   │  • JWT auth         │
               └──────────────────┘   │  • RBAC             │
                                      └──┬──────┬──────┬───┘
                                         │      │      │
                           ┌─────────────▼┐ ┌──▼───┐ ┌▼──────────┐
                           │  PostgreSQL   │ │Redis │ │   S3/R2    │
                           │  16 Alpine    │ │  7   │ │  Storage   │
                           │  • Users      │ │      │ │            │
                           │  • Images     │ │•Queue│ │•Images     │
                           │  • Jobs       │ │•Cache│ │•Thumbnails │
                           │  • Billing    │ │•SSE  │ │            │
                           └──────────────┘ └──────┘ └────────────┘
                                                      ┌───────────┐
                           ┌─────────────────────────►│  Celery    │
                           │  Redis (broker)          │  Worker    │
                           │                          │  • Image   │
                           │                          │    gen     │
                           │                          └─────┬─────┘
                           │                                │
                           │              ┌─────────────────▼─────────┐
                           │              │     AI Providers          │
                           │              │  • ComfyUI (local)        │
                           │              │  • HuggingFace Inference  │
                           │              │  • Replicate              │
                           │              └───────────────────────────┘
                           │
                           └──────────────────────────►LLM APIs
                                                       • OpenAI
                                                       • Anthropic
```

## Service Responsibilities

### Frontend (Next.js 14)
- **Rendering**: App Router with server components and client components
- **State**: Zustand stores (auth, generation, prompt, theme) with localStorage persistence
- **API Communication**: REST client (`lib/api.ts`) with JWT bearer tokens
- **Real-time**: EventSource (SSE) for generation progress with fallback polling
- **Auth**: Google Identity Services integration, JWT storage in localStorage

### Backend (FastAPI)
- **API Layer**: 50+ endpoints across 7 route modules (auth, generate, images, gallery, billing, prompt, admin)
- **Auth**: JWT access tokens, Google OAuth, password reset via email tokens
- **AI Abstraction**: `AIProvider` abstract base class with pluggable providers
- **Prompt Enhancement**: LLM-powered enhance/optimize/negative/suggest with safety filtering
- **Credit System**: Transaction ledger with deduction, addition, and usage logging
- **Admin**: RBAC with role-based access control and audit logging

### Celery Worker
- **Job Processing**: Receives generation requests, calls AI providers, stores results
- **Progress Reporting**: Publishes progress to Redis pub/sub for SSE streaming
- **Concurrency**: Configurable worker count with queue routing (default, high_priority)

### PostgreSQL
- **14 tables** covering users, images, jobs, billing, auth, and admin
- **Async access** via SQLAlchemy 2.0 + asyncpg
- **Migrations** via Alembic with versioned upgrade scripts

### Redis
- **Message Broker**: Celery task queue
- **Pub/Sub**: Real-time SSE progress streaming for generation jobs
- **Caching**: Session data, rate limiting counters
- **Persistence**: AOF for crash recovery, RDB for backups

## Data Flow: Image Generation

```
User clicks "Generate"
        │
        ▼
Frontend POST /api/generate
        │
        ▼
Backend: Deduct credits → Create Job (PENDING) → Enqueue Celery task
        │
        ▼
Worker: Pick up task → Call AI Provider → Store image → Update Job (COMPLETED)
        │                          │
        │                   Progress events
        │                          │
        │                          ▼
        │                   Redis Pub/Sub → SSE Stream → Frontend progress bar
        │
        ▼
Backend: Store image metadata in PostgreSQL → Return to frontend
        │
        ▼
Frontend: Display generated image in grid
```

## Authentication Flow

```
Register/Login
    │
    ├── Email/Password → bcrypt verify → JWT access token
    │
    └── Google OAuth → Google verifies credential → Find or create user → JWT token
    
Token stored in localStorage → Sent as Bearer header → Backend verifies JWT → get_current_user dependency
```

## Credit System

```
Plans define monthly_credit allocation
    │
    ▼
User starts with 50 free credits (default FREE plan)
    │
    ├── Generation costs 1 credit per image
    ├── Credits checked before job submission (require_credits dependency)
    ├── Deduction logged in credit_transactions table
    └── Usage logged in usage_logs table for analytics
```

## Security Model

| Layer | Measure |
|-------|---------|
| Transport | TLS via Nginx (production) |
| Authentication | JWT with configurable expiry (default 24h) |
| Password | bcrypt with per-user salt |
| Authorization | Role-based (user, admin) via `require_admin` dependency |
| Rate Limiting | Nginx zones: 30 req/s API, 5 req/s auth |
| Input Validation | Pydantic schemas on all endpoints |
| CORS | Configurable allowed origins |
| Secrets | Never in code — env vars / AWS Secrets Manager |
| SQL Injection | SQLAlchemy ORM (parameterized queries) |
| XSS | React auto-escaping + security headers |

## Scalability Path

| Scale | Architecture |
|-------|-------------|
| **0-1K users** | Single EC2 instance, Docker Compose |
| **1K-10K users** | ECS Fargate, managed RDS, ElastiCache |
| **10K+ users** | Load balancer, auto-scaling group, read replicas |
| **GPU workloads** | Separate GPU fleet (P4d instances) with job queue routing |
