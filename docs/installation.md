# Installation Guide

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Docker | 24+ | Container runtime |
| Docker Compose | 2.20+ | Service orchestration |
| Git | 2.40+ | Version control |
| Node.js | 20+ | Frontend (if running locally) |
| Python | 3.12+ | Backend (if running locally) |

## Quick Setup (Docker)

```bash
# 1. Clone
git clone https://github.com/yourusername/text2img.git
cd text2img

# 2. Create environment file
cp .env.example .env

# 3. Edit .env — minimum required values:
#    POSTGRES_PASSWORD=<any strong password>
#    REDIS_PASSWORD=<any strong password>
#    BACKEND_SECRET_KEY=<64-char random string>

# 4. Generate a secret key
make generate-secret
# Copy the output into BACKEND_SECRET_KEY in .env

# 5. Start all services
docker compose up -d

# 6. Verify
make health
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/api/docs

## Local Development Setup

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set up database (requires PostgreSQL running)
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/text2img"
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start dev server
npm run dev
```

## Optional: AI Provider Setup

### Replicate (Recommended)
1. Sign up at https://replicate.com
2. Get API token from https://replicate.com/account/api-tokens
3. Add to `.env`: `REPLICATE_API_TOKEN=r8_xxxx`

### HuggingFace
1. Sign up at https://huggingface.co
2. Create access token at https://huggingface.co/settings/tokens
3. Add to `.env`: `HUGGINGFACE_API_KEY=hf_xxxx`

### ComfyUI (Local GPU)
1. Install ComfyUI: https://github.com/comfyanonymous/ComfyUI
2. Start ComfyUI server on port 8188
3. Add to `.env`: `AI_PROVIDER=comfyui`

## Optional: LLM Prompt Enhancement

### OpenAI
1. Get API key from https://platform.openai.com/api-keys
2. Add to `.env`: `OPENAI_API_KEY=sk-xxxx`

### Anthropic
1. Get API key from https://console.anthropic.com
2. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-xxxx`

## Optional: Stripe Billing

1. Create account at https://stripe.com
2. Get keys from https://dashboard.stripe.com/apikeys
3. Add to `.env`:
   ```
   STRIPE_SECRET_KEY=sk_live_xxxx
   STRIPE_WEBHOOK_SECRET=whsec_xxxx
   ```

## Optional: Google OAuth

1. Create project at https://console.cloud.google.com
2. Enable Google Identity Services
3. Create OAuth 2.0 credentials
4. Add to `.env`:
   ```
   GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
   NEXT_PUBLIC_GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
   ```

## Troubleshooting

### Services won't start
```bash
# Check logs
docker compose logs backend
docker compose logs worker

# Common fix: ensure .env exists and has required values
cat .env | grep POSTGRES_PASSWORD
```

### Database connection refused
```bash
# Ensure PostgreSQL is running
docker compose ps postgres

# Reset database
docker compose down -v postgres
docker compose up -d postgres
docker compose exec backend alembic upgrade head
```

### Frontend can't reach backend
```bash
# Check CORS origins in .env
grep CORS .env
# Should include: ["http://localhost:3000"]

# Check backend is running
curl http://localhost:8000/api/health
```
