from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # ── App ────────────────────────────────────────
    APP_NAME: str = "Text2Img API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me"

    # ── Database ───────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/text2img"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/text2img"

    # ── Redis ──────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Auth ───────────────────────────────────────
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    FRONTEND_URL: str = "http://localhost:3000"
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30

    # ── CORS ───────────────────────────────────────
    CORS_ORIGINS: str = '["http://localhost:3000"]'

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    BACKEND_URL: str = "http://localhost:8000"

    # ── AI Provider ────────────────────────────────
    AI_PROVIDER: str = "huggingface"
    COMFYUI_URL: str = "http://localhost:8188"
    COMFYUI_TIMEOUT: int = 180
    HUGGINGFACE_API_KEY: str = ""
    HF_TOKEN: str = ""
    HUGGINGFACE_MODEL: str = "black-forest-labs/FLUX.1-schnell"
    REPLICATE_API_TOKEN: str = ""
    REPLICATE_MODEL: str = "black-forest-labs/flux-1.1-pro"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"

    # ── LLM (Prompt Enhancement) ───────────────────
    LLM_PROVIDER: str = "gemini"
    GEMINI_LLM_MODEL: str = "gemini-3.6-flash"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-haiku-20240307"

    # ── Storage ────────────────────────────────────
    STORAGE_BACKEND: str = "local"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = "text2img-dev"
    AWS_REGION: str = "us-east-1"
    LOCAL_STORAGE_PATH: str = "./storage"

    # ── Stripe ─────────────────────────────────────
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # ── Sentry ─────────────────────────────────────
    SENTRY_DSN: str = ""


settings = Settings()
