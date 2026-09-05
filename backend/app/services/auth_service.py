import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import httpx
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import User, PasswordResetToken

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password Hashing ──────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


# ── JWT ───────────────────────────────────────────
def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return jwt.encode({"sub": user_id, "exp": expire, "type": "access"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload.get("sub")
    except JWTError:
        return None


# ── User CRUD ─────────────────────────────────────
async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == str(user_id)))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, password: str, name: Optional[str] = None) -> User:
    user = User(email=email, hashed_password=hash_password(password), name=name)
    db.add(user)
    await db.flush()
    return user


async def create_oauth_user(
    db: AsyncSession, email: str, provider: str, provider_id: str,
    name: Optional[str] = None, avatar_url: Optional[str] = None,
) -> User:
    user = User(
        email=email,
        provider=provider,
        provider_id=provider_id,
        name=name,
        avatar_url=avatar_url,
    )
    db.add(user)
    await db.flush()
    return user


async def update_user_profile(db: AsyncSession, user: User, name: Optional[str] = None, avatar_url: Optional[str] = None) -> User:
    if name is not None:
        user.name = name
    if avatar_url is not None:
        user.avatar_url = avatar_url
    await db.flush()
    return user


async def change_user_password(db: AsyncSession, user: User, new_password: str) -> User:
    user.hashed_password = hash_password(new_password)
    await db.flush()
    return user


# ── Credits ───────────────────────────────────────
async def deduct_credits(db: AsyncSession, user: User, amount: int = 1) -> bool:
    if user.credits < amount:
        return False
    user.credits -= amount
    await db.flush()
    return True


# ── Password Reset Tokens ─────────────────────────
async def create_password_reset_token(db: AsyncSession, user: User) -> str:
    raw_token = secrets.token_urlsafe(48)
    token_hashed = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)

    record = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hashed,
        expires_at=expires_at,
    )
    db.add(record)
    await db.flush()
    return raw_token


async def validate_password_reset_token(db: AsyncSession, raw_token: str) -> Optional[User]:
    token_hashed = hash_token(raw_token)
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hashed,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > now,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        return None

    record.used = True
    await db.flush()

    user = await get_user_by_id(db, UUID(record.user_id))
    return user


# ── Google OAuth ──────────────────────────────────
async def verify_google_token(credential: str) -> Optional[dict]:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {credential}"},
            )
            if resp.status_code == 200:
                return resp.json()

        resp = await httpx.AsyncClient().get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": credential},
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


async def find_or_create_google_user(db: AsyncSession, google_data: dict) -> User:
    email = google_data.get("email")
    if not email:
        return None

    user = await get_user_by_email(db, email)
    if user:
        if not user.avatar_url and google_data.get("picture"):
            user.avatar_url = google_data["picture"]
            await db.flush()
        return user

    return await create_oauth_user(
        db,
        email=email,
        provider="google",
        provider_id=google_data.get("sub", ""),
        name=google_data.get("name"),
        avatar_url=google_data.get("picture"),
    )
