from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.models import User
from app.schemas import (
    UserRegister, UserLogin, Token, UserResponse,
    ForgotPasswordRequest, ResetPasswordRequest,
    ChangePasswordRequest, UpdateProfileRequest, GoogleOAuthRequest,
)
from app.services.auth_service import (
    create_user, get_user_by_email, verify_password, create_access_token,
    create_password_reset_token, validate_password_reset_token,
    change_user_password, update_user_profile,
    verify_google_token, find_or_create_google_user,
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Email + Password ──────────────────────────────
@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(body: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = await create_user(db, body.email, body.password, body.name)
    token = create_access_token(str(user.id))
    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=Token)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, body.email)
    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if user.is_banned:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account has been suspended")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    token = create_access_token(str(user.id))
    return Token(access_token=token, user=UserResponse.model_validate(user))


# ── Google OAuth ──────────────────────────────────
@router.post("/google", response_model=Token)
async def google_login(body: GoogleOAuthRequest, db: AsyncSession = Depends(get_db)):
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Google OAuth not configured")

    google_data = await verify_google_token(body.credential)
    if not google_data or not google_data.get("email"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google credential")

    user = await find_or_create_google_user(db, google_data)
    if not user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process Google auth")
    if user.is_banned:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account has been suspended")

    token = create_access_token(str(user.id))
    return Token(access_token=token, user=UserResponse.model_validate(user))


# ── Password Reset ────────────────────────────────
@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, body.email)
    if not user or not user.hashed_password:
        return {"message": "If an account exists, a reset email has been sent."}

    raw_token = await create_password_reset_token(db, user)

    reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={raw_token}"
    print(f"[PASSWORD RESET] {user.email}: {reset_url}")

    return {"message": "If an account exists, a reset email has been sent.", "reset_url": reset_url}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    user = await validate_password_reset_token(db, body.token)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    await change_user_password(db, user, body.new_password)
    return {"message": "Password has been reset successfully"}


# ── Profile (Protected) ──────────────────────────
@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
async def update_me(body: UpdateProfileRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    updated = await update_user_profile(db, user, name=body.name, avatar_url=body.avatar_url)
    return UserResponse.model_validate(updated)


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(body: ChangePasswordRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not user.hashed_password or not verify_password(body.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    await change_user_password(db, user, body.new_password)
    return {"message": "Password changed successfully"}
