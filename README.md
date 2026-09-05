# Text2Img — AI Text-to-Image Generator

A production-ready, real-time AI text-to-image generation platform with a FastAPI backend, Next.js frontend, Celery worker pipeline, and multi-provider AI integration.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Kumaresan-Tech/text-to-image-ai)

## Features

- **Real-time generation** with Server-Sent Events (SSE) progress streaming
- **Multiple AI providers**: ComfyUI (local), HuggingFace Inference API, Replicate
- **Prompt enhancement** via OpenAI/Anthropic LLMs with safety filtering
- **Image management**: gallery, favorites, share links, download, search/filter
- **Credit-based billing** with Stripe integration, plans, and transaction ledger
- **Admin panel**: user management, platform stats, audit logs, prompt analytics
- **Dark/light mode** with system preference detection
- **JWT authentication** with Google OAuth, password reset, and account management
- **Docker deployment** with Nginx reverse proxy, health checks, and rate limiting
- **CI/CD** via GitHub Actions with automated testing, linting, and deployment

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS, Zustand, Framer Motion |
| Backend | FastAPI, Python 3.12, SQLAlchemy 2.0 (async), Celery, Redis |
| Database | PostgreSQL 16, Redis 7 |
| Auth | JWT, Google OAuth 2.0, bcrypt |
| Billing | Stripe (with demo mode fallback) |
| AI Providers | ComfyUI, HuggingFace, Replicate |
| Deployment | Docker, Docker Compose, Nginx, GitHub Actions |
| Cloud | AWS (EC2, ECS Fargate, S3, Secrets Manager), Vercel |

## Quick Start (Instant Local Running)

### Option 1: One-Click Launcher (Windows)
Double-click `start.bat` in the project root to start both the Studio Engine and the Web App Frontend.

### Option 2: Run from Terminal
```powershell
# 1. Start the High-Quality AI Studio (Port 7860)
python dashboard.py

# 2. In another terminal, start the Next.js Web App (Port 3001)
npm run dev
```

- **Next.js Web App**: [http://localhost:3001](http://localhost:3001)
- **Embedded AI Studio**: [http://localhost:3001/studio](http://localhost:3001/studio)
- **Standalone Studio Dashboard**: [http://localhost:7860](http://localhost:7860)

---

## Full Docker Stack (Optional Production Mode)

# 3. Start with Docker
docker compose up -d

# 4. Run database migrations
docker compose exec backend alembic upgrade head

# 5. Open
# Frontend:  http://localhost:3000
# API Docs:  http://localhost:8000/api/docs
```

## Project Structure

```
text2img/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI app setup & routes
│   │   ├── config.py       # Pydantic Settings
│   │   ├── database.py     # SQLAlchemy async engine
│   │   ├── models/         # ORM models (14 tables)
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── routes/         # API route modules
│   │   ├── services/       # Business logic layer
│   │   ├── workers/        # Celery task definitions
│   │   └── dependencies.py # FastAPI dependency injection
│   ├── alembic/            # Database migrations (6 versions)
│   ├── tests/              # Pytest test suite
│   ├── conftest.py         # Test fixtures
│   ├── requirements.txt    # Python dependencies
│   ├── pyproject.toml      # Ruff, mypy, pytest config
│   └── Dockerfile          # Multi-stage production build
├── frontend/               # Next.js 14 application
│   ├── app/                # App Router pages
│   │   ├── (dashboard)/    # Authenticated routes
│   │   │   ├── dashboard/  # Main dashboard
│   │   │   ├── generate/   # Image generation page
│   │   │   ├── images/     # Image history
│   │   │   ├── gallery/    # Public gallery
│   │   │   ├── billing/    # Billing & plans
│   │   │   ├── profile/    # User profile
│   │   │   └── admin/      # Admin panel
│   │   └── auth/           # Login / register
│   ├── components/         # React components
│   ├── stores/             # Zustand state stores
│   ├── hooks/              # Custom React hooks
│   ├── lib/                # API client & utilities
│   └── Dockerfile          # Multi-stage production build
├── nginx/                  # Reverse proxy config
├── deploy/                 # Deployment scripts & configs
│   ├── aws/                # ECS & EC2 deployment
│   ├── vercel/             # Vercel frontend deployment
│   ├── postgres/           # PostgreSQL production config
│   ├── redis/              # Redis production config
│   └── scripts/            # Backup, restore, health check
├── docs/                   # Project documentation
├── docker-compose.yml      # Production orchestration
├── docker-compose.override.yml  # Local dev overrides
├── Makefile                # Unified task runner
└── .github/workflows/      # CI/CD pipelines
```

## Available Commands

```bash
make help          # Show all available commands
make dev           # Start all services (dev mode)
make down          # Stop all services
make build         # Build all Docker images
make migrate       # Run database migrations
make test-backend  # Run backend tests
make health        # Run health checks
make backup        # Backup PostgreSQL
make lint          # Run linting
```

## API Documentation

- **Interactive docs**: http://localhost:8000/api/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/api/docs (ReDoc)
- **OpenAPI schema**: http://localhost:8000/api/openapi.json

## Documentation

| Document | Description |
|----------|-------------|
| [Installation Guide](docs/installation.md) | Step-by-step setup instructions |
| [Architecture](docs/architecture.md) | System design & data flow |
| [API Reference](docs/api.md) | Complete API endpoint reference |
| [ER Diagram](docs/er-diagram.md) | Database entity-relationship diagram |
| [Deployment Guide](docs/deployment.md) | AWS, Vercel, and Docker deployment |

## Environment Variables

See [`.env.example`](.env.example) for all required and optional environment variables.

| Variable | Required | Description |
|----------|----------|-------------|
| `POSTGRES_PASSWORD` | Yes | Database password |
| `REDIS_PASSWORD` | Yes | Redis password |
| `BACKEND_SECRET_KEY` | Yes | JWT signing key (64+ chars) |
| `REPLICATE_API_TOKEN` | No | Replicate API token |
| `OPENAI_API_KEY` | No | OpenAI key for prompt enhancement |
| `STRIPE_SECRET_KEY` | No | Stripe billing key |
| `GOOGLE_CLIENT_ID` | No | Google OAuth client ID |

## Testing

```bash
# Run all backend tests
make test-backend

# Run with coverage
cd backend && pytest --cov=app --cov-report=html

# Run specific test file
cd backend && pytest tests/test_auth.py -v

# Run only fast tests (skip slow ones)
cd backend && pytest -m "not slow"
```

## License

MIT
