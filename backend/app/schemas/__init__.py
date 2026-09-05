from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


# ── Enums ──────────────────────────────────────────
class JobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PlanTier(str, Enum):
    FREE = "FREE"
    STARTER = "STARTER"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


# ── Auth ───────────────────────────────────────────
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    credits: int
    plan: str
    role: str
    is_active: bool
    is_banned: bool
    created_at: datetime


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=32)
    new_password: str = Field(..., min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=500)


class GoogleOAuthRequest(BaseModel):
    credential: str


# ── Generation ─────────────────────────────────────
SAMPLERS_LIST = [
    "DPM++ 2M Karras",
    "DPM++ 2M SDE Karras",
    "DPM++ SDE Karras",
    "Euler a",
    "Euler",
    "DDIM",
    "Heun",
    "DPM++ 3M SDE Karras",
    "UniPC",
]

MODELS_LIST = [
    "sdxl-1.0",
    "sd-3.5-large",
    "flux-dev",
    "flux-schnell",
    "hf-sdxl",
    "hf-flux",
    "replicate-flux",
    "demo",
]


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    negative_prompt: Optional[str] = Field(None, max_length=2000)
    width: int = Field(1024, ge=256, le=2048, multiple_of=64)
    height: int = Field(1024, ge=256, le=2048, multiple_of=64)
    steps: int = Field(30, ge=1, le=100)
    cfg_scale: float = Field(7.5, ge=1.0, le=30.0)
    sampler: str = Field("DPM++ 2M Karras")
    seed: int = Field(-1, ge=-1)
    model: str = Field("sdxl-1.0")
    num_images: int = Field(1, ge=1, le=4)
    is_public: bool = Field(False)


class GenerateResponse(BaseModel):
    job_id: UUID
    status: JobStatus
    estimated_time: int
    credits_deducted: int
    credits_remaining: int


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: JobStatus
    prompt: str
    params: Optional[Any]
    image_id: Optional[UUID]
    image_url: Optional[str] = None
    error_message: Optional[str]
    progress: Optional[int] = None
    progress_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime]


class SSEProgressEvent(BaseModel):
    status: str
    progress: int
    message: str = ""
    timestamp: str = ""
    image_id: Optional[str] = None
    image_url: Optional[str] = None


class ModelInfo(BaseModel):
    id: str
    name: str
    default_steps: int
    default_cfg: float
    default_width: int
    default_height: int
    max_steps: int


# ── Images ─────────────────────────────────────────
class ImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    prompt: str
    negative_prompt: Optional[str]
    image_url: str
    thumbnail_url: Optional[str]
    width: int
    height: int
    steps: int
    cfg_scale: float
    sampler: str
    seed: Optional[int]
    model: str
    is_public: bool
    likes_count: int
    created_at: datetime
    is_favorited: bool = False
    tags: List[str] = []


class ImageListResponse(BaseModel):
    images: List[ImageResponse]
    total: int
    page: int
    per_page: int
    has_next: bool


class ImageSearchRequest(BaseModel):
    q: Optional[str] = None
    model: Optional[str] = None
    sampler: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    is_favorited: Optional[bool] = None
    is_public: Optional[bool] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class ImageUpdateRequest(BaseModel):
    is_public: Optional[bool] = None


class ImageShareResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    image_id: UUID
    share_token: str
    is_active: bool
    view_count: int
    created_at: datetime
    share_url: str = ""


class SharedImageView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    prompt: str
    negative_prompt: Optional[str]
    image_url: str
    thumbnail_url: Optional[str]
    width: int
    height: int
    steps: int
    cfg_scale: float
    sampler: str
    seed: Optional[int]
    model: str
    likes_count: int
    created_at: datetime
    shared_by: Optional[str] = None


class FavoriteToggleResponse(BaseModel):
    is_favorited: bool
    favorites_count: int


# ── Billing ────────────────────────────────────────
class CreditsResponse(BaseModel):
    credits: int
    plan: str
    subscription_status: Optional[str] = None


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    credits: int
    price_monthly: float
    features: Optional[Any]
    stripe_price_id: Optional[str] = None


class CheckoutRequest(BaseModel):
    plan_id: str
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    plan_id: str
    plan_name: str
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool
    credits: int
    credits_used_this_period: int


class CancelSubscriptionRequest(BaseModel):
    reason: Optional[str] = None


class CreditTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    amount: int
    balance_after: int
    type: str
    description: Optional[str]
    reference_id: Optional[str]
    created_at: datetime


class CreditTransactionListResponse(BaseModel):
    transactions: List[CreditTransactionResponse]
    total: int
    page: int
    per_page: int
    has_next: bool


class UsageLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    action: str
    credits_used: int
    model: Optional[str]
    created_at: datetime


class UsageStatsResponse(BaseModel):
    total_generations: int
    total_credits_used: int
    generations_today: int
    credits_used_today: int
    generations_this_month: int
    credits_used_this_month: int
    top_models: List[dict]
    daily_usage: List[dict]


class AddCreditsRequest(BaseModel):
    amount: int = Field(..., ge=1, le=10000)
    description: Optional[str] = None


# ── Pagination ─────────────────────────────────────
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


# ── Prompt Enhancement ──────────────────────────
PROMPT_ACTIONS = ["enhance", "optimize", "negative", "suggest", "safety_check"]


class PromptEnhanceRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    prompt: str = Field(..., min_length=1, max_length=2000)
    action: str = Field("enhance")
    model_target: str = Field("sdxl-1.0")


class PromptEnhanceResponse(BaseModel):
    original: str
    enhanced: str
    negative: str = ""
    tips: List[str] = []
    suggestions: Optional[List[str]] = None
    is_safe: bool = True
    safety_flags: List[str] = []


class PromptHistoryItem(BaseModel):
    model_config = {"protected_namespaces": ()}

    id: str
    original_prompt: str
    enhanced_prompt: Optional[str]
    negative_prompt: Optional[str]
    action: str
    model_target: Optional[str]
    is_safe: bool
    used: bool
    created_at: Optional[str]


class PromptHistoryResponse(BaseModel):
    items: List[PromptHistoryItem]
    total: int
