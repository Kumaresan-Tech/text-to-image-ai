from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_admin
from app.models import User
from app.services import admin_service

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ── Request Schemas ─────────────────────────────────
class UserActionRequest(BaseModel):
    reason: Optional[str] = None


class RoleRequest(BaseModel):
    role: str = Field(..., pattern=r"^(user|admin)$")


class CreditsRequest(BaseModel):
    credits: int = Field(..., ge=0)


class MessageResponse(BaseModel):
    message: str


# ── Platform Stats ──────────────────────────────────
@router.get("/stats")
async def get_stats(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    stats = await admin_service.get_platform_stats(db)
    return stats


@router.get("/health")
async def get_health(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    health = await admin_service.get_system_health(db)
    return health


# ── User Management ─────────────────────────────────
@router.get("/users")
async def list_users(
    q: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_banned: Optional[bool] = Query(None),
    plan: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    users, total = await admin_service.get_users(
        db, q=q, role=role, is_banned=is_banned, plan=plan,
        sort_by=sort_by, sort_order=sort_order, page=page, per_page=per_page,
    )
    return {
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "name": u.name,
                "avatar_url": u.avatar_url,
                "credits": u.credits,
                "plan": u.plan,
                "role": u.role,
                "is_active": u.is_active,
                "is_banned": u.is_banned,
                "ban_reason": u.ban_reason,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.get("/users/{user_id}")
async def get_user(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    detail = await admin_service.get_user_detail(db, str(user_id))
    if not detail:
        raise HTTPException(status_code=404, detail="User not found")
    u = detail["user"]
    return {
        "id": str(u.id),
        "email": u.email,
        "name": u.name,
        "avatar_url": u.avatar_url,
        "credits": u.credits,
        "plan": u.plan,
        "role": u.role,
        "is_active": u.is_active,
        "is_banned": u.is_banned,
        "ban_reason": u.ban_reason,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "images_count": detail["images_count"],
        "jobs_count": detail["jobs_count"],
        "credits_used": detail["credits_used"],
        "last_active": detail["last_active"].isoformat() if detail["last_active"] else None,
    }


@router.post("/users/{user_id}/ban", response_model=MessageResponse)
async def ban_user(
    user_id: UUID,
    body: UserActionRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await admin_service.ban_user(db, str(user_id), reason=body.reason)
    if not user:
        raise HTTPException(status_code=400, detail="Cannot ban this user")
    await admin_service.log_admin_action(
        db, str(admin.id), "ban_user", "user", str(user_id),
        details={"reason": body.reason},
    )
    await db.commit()
    return MessageResponse(message="User banned successfully")


@router.post("/users/{user_id}/unban", response_model=MessageResponse)
async def unban_user(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await admin_service.unban_user(db, str(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await admin_service.log_admin_action(
        db, str(admin.id), "unban_user", "user", str(user_id),
    )
    await db.commit()
    return MessageResponse(message="User unbanned successfully")


@router.put("/users/{user_id}/role", response_model=MessageResponse)
async def set_role(
    user_id: UUID,
    body: RoleRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await admin_service.set_user_role(db, str(user_id), body.role)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid user or role")
    await admin_service.log_admin_action(
        db, str(admin.id), "set_role", "user", str(user_id),
        details={"role": body.role},
    )
    await db.commit()
    return MessageResponse(message=f"User role set to {body.role}")


@router.put("/users/{user_id}/credits", response_model=MessageResponse)
async def set_credits(
    user_id: UUID,
    body: CreditsRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await admin_service.set_user_credits(db, str(user_id), body.credits)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await admin_service.log_admin_action(
        db, str(admin.id), "set_credits", "user", str(user_id),
        details={"credits": body.credits},
    )
    await db.commit()
    return MessageResponse(message=f"Credits set to {body.credits}")


# ── Image Management ───────────────────────────────
@router.get("/images")
async def list_images(
    q: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    images, total = await admin_service.admin_list_images(
        db, q=q, user_id=user_id, model=model, is_public=is_public,
        page=page, per_page=per_page,
    )
    return {
        "images": images,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


# ── Prompt Analytics ───────────────────────────────
@router.get("/prompts/analytics")
async def prompt_analytics(
    days: int = Query(30, ge=1, le=365),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await admin_service.get_prompt_analytics(db, days=days)


# ── Audit Logs ─────────────────────────────────────
@router.get("/audit-logs")
async def list_audit_logs(
    admin_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    target_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    logs, total = await admin_service.get_audit_logs(
        db, admin_id=admin_id, action=action, target_type=target_type,
        page=page, per_page=per_page,
    )
    return {
        "logs": logs,
        "total": total,
        "page": page,
        "per_page": per_page,
    }
