from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routes import auth, generate, images, gallery, billing, prompt, admin

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if settings.SENTRY_DSN:
        sentry_sdk.init(dsn=settings.SENTRY_DSN, integrations=[FastApiIntegration()])
    yield
    # Shutdown


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# ── CORS ───────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────
app.include_router(auth.router)
app.include_router(generate.router)
app.include_router(images.router)
app.include_router(gallery.router)
app.include_router(billing.router)
app.include_router(prompt.router)
app.include_router(admin.router)


# ── Docs Redirects ─────────────────────────────────
@app.get("/docs", include_in_schema=False)
async def redirect_docs():
    return RedirectResponse(url="/api/docs")


@app.get("/redoc", include_in_schema=False)
async def redirect_redoc():
    return RedirectResponse(url="/api/redoc")


# ── Health Check ───────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}


# ── Local Storage Static Files ─────────────────────
if settings.STORAGE_BACKEND == "local":
    from pathlib import Path

    storage_path = Path(settings.LOCAL_STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)
    app.mount("/storage", StaticFiles(directory=str(storage_path)), name="storage")
