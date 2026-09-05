# Deploying Text2Img to Render

This repository includes full support for deploying on **[Render](https://render.com)** using **Render Blueprints** (`render.yaml`) or manual web service creation.

---

## Method 1: 1-Click Blueprint Deployment (Recommended)

1. **Push your code to GitHub / GitLab**.
2. Log in to [Render Dashboard](https://dashboard.render.com).
3. Click **New +** in the top right and select **Blueprint**.
4. Select your repository `text-to-image-generator-ai`.
5. Render will automatically read [`render.yaml`](../../render.yaml) and configure:
   - **PostgreSQL Database** (`text2img-db`)
   - **FastAPI Backend Web Service** (`text2img-backend`)
   - **Next.js Frontend Web Service** (`text2img-frontend`)
6. Fill in the required secret environment variables prompted by Render:
   - `HF_TOKEN`: Your Hugging Face user access token (e.g. `hf_...`)
   - `HUGGINGFACE_API_KEY`: Same Hugging Face token
   - `GEMINI_API_KEY`: Your Google Gemini API key
7. Click **Apply**.
8. Once the build finishes:
   - Your frontend will be live at `https://text2img-frontend.onrender.com`
   - Your backend API docs will be at `https://text2img-backend.onrender.com/api/docs`

---

## Method 2: Deploying Services Manually on Render

If you prefer to configure services manually in the Render UI:

### Step 1: Create PostgreSQL Database
1. Click **New +** → **PostgreSQL**.
2. Name: `text2img-db`.
3. Plan: **Free** (or Starter).
4. Click **Create Database**.
5. Copy the **Internal Database URL** once created.

### Step 2: Create Backend Web Service
1. Click **New +** → **Web Service**.
2. Connect your repository.
3. Configure settings:
   - **Name**: `text2img-backend`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/api/health`
4. Add **Environment Variables**:
   - `DATABASE_URL`: Paste your database Internal Database URL.
   - `DATABASE_URL_SYNC`: Paste your database Internal Database URL.
   - `SECRET_KEY`: A secure random 64-character string.
   - `AI_PROVIDER`: `huggingface`
   - `HF_TOKEN`: Your Hugging Face token.
   - `HUGGINGFACE_API_KEY`: Your Hugging Face token.
   - `HUGGINGFACE_MODEL`: `black-forest-labs/FLUX.1-schnell`
   - `LLM_PROVIDER`: `gemini`
   - `GEMINI_API_KEY`: Your Google Gemini API key.
   - `GEMINI_MODEL`: `gemini-3.6-flash`
   - `CORS_ORIGINS`: `["*"]`
   - `STORAGE_BACKEND`: `local`
5. Click **Create Web Service**.

### Step 3: Create Frontend Web Service
1. Click **New +** → **Web Service**.
2. Connect your repository.
3. Configure settings:
   - **Name**: `text2img-frontend`
   - **Root Directory**: `frontend`
   - **Runtime**: `Node`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm run start`
4. Add **Environment Variables**:
   - `NEXT_PUBLIC_API_URL`: Your backend URL (e.g. `https://text2img-backend.onrender.com`).
5. Click **Create Web Service**.

---

## Verification

Once deployed:
1. Open your frontend URL (`https://text2img-frontend.onrender.com`).
2. Log in or create an account.
3. Enter any prompt (e.g. `"A majestic dragon perched on a crystal mountain, volumetric lighting, 8k"`).
4. Generation will use `black-forest-labs/FLUX.1-schnell` via Hugging Face and deliver an ultra-high-definition 1024x1024 artwork!
