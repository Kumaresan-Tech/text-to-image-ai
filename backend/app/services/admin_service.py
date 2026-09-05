import json
import logging
from typing import Optional, List, Tuple
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, and_, desc, cast, Date, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    User, Image, Job, UsageLog, CreditTransaction, AdminAuditLog, PromptHistory,
)

logger = logging.getLogger(__name__)


# ── Audit Logging ──────────────────────────────────
async def log_admin_action(
    db: AsyncSession,
    admin_id: str,
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    details: Optional[dict] = None,
) -> AdminAuditLog:
    log = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    db.add(log)
    await db.flush()
    return log


# ── User Management ────────────────────────────────
async def get_users(
    db: AsyncSession,
    q: Optional[str] = None,
    role: Optional[str] = None,
    is_banned: Optional[bool] = None,
    plan: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[User], int]:
    conditions = []

    if q:
        conditions.append(
            func.lower(User.email).contains(q.lower()) |
            func.lower(User.name).contains(q.lower())
        )
    if role:
        conditions.append(User.role == role)
    if is_banned is not None:
        conditions.append(User.is_banned == is_banned)
    if plan:
        conditions.append(User.plan == plan)

    where = and_(*conditions) if conditions else True

    count_q = select(func.count()).select_from(User).where(where)
    total = (await db.execute(count_q)).scalar() or 0

    order_col = {
        "created_at": User.created_at,
        "email": User.email,
        "credits": User.credits,
        "plan": User.plan,
    }.get(sort_by, User.created_at)

    order_fn = desc if sort_order == "desc" else func.asc

    q_stmt = (
        select(User)
        .where(where)
        .order_by(order_fn(order_col))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(q_stmt)
    return list(result.scalars().all()), total


async def get_user_detail(db: AsyncSession, user_id: str) -> Optional[dict]:
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        return None

    images_count = (await db.execute(
        select(func.count()).select_from(Image).where(Image.user_id == user_id)
    )).scalar() or 0

    jobs_count = (await db.execute(
        select(func.count()).select_from(Job).where(Job.user_id == user_id)
    )).scalar() or 0

    credits_used = (await db.execute(
        select(func.coalesce(func.sum(UsageLog.credits_used), 0))
        .where(UsageLog.user_id == user_id)
    )).scalar() or 0

    last_job = (await db.execute(
        select(Job.created_at)
        .where(Job.user_id == user_id)
        .order_by(desc(Job.created_at))
        .limit(1)
    )).scalar_one_or_none()

    return {
        "user": user,
        "images_count": images_count,
        "jobs_count": jobs_count,
        "credits_used": credits_used,
        "last_active": last_job,
    }


async def ban_user(db: AsyncSession, user_id: str, reason: Optional[str] = None) -> Optional[User]:
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user or user.role == "admin":
        return None
    user.is_banned = True
    user.ban_reason = reason
    user.is_active = False
    await db.flush()
    return user


async def unban_user(db: AsyncSession, user_id: str) -> Optional[User]:
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        return None
    user.is_banned = False
    user.ban_reason = None
    user.is_active = True
    await db.flush()
    return user


async def set_user_role(db: AsyncSession, user_id: str, role: str) -> Optional[User]:
    if role not in ("user", "admin"):
        return None
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        return None
    user.role = role
    await db.flush()
    return user


async def set_user_credits(db: AsyncSession, user_id: str, credits: int) -> Optional[User]:
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        return None
    user.credits = credits
    await db.flush()
    return user


# ── Image Management ───────────────────────────────
async def admin_list_images(
    db: AsyncSession,
    q: Optional[str] = None,
    user_id: Optional[str] = None,
    model: Optional[str] = None,
    is_public: Optional[bool] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[dict], int]:
    conditions = []
    if q:
        conditions.append(Image.prompt.ilike(f"%{q}%"))
    if user_id:
        conditions.append(Image.user_id == user_id)
    if model:
        conditions.append(Image.model == model)
    if is_public is not None:
        conditions.append(Image.is_public == is_public)

    where = and_(*conditions) if conditions else True

    count_q = select(func.count()).select_from(Image).where(where)
    total = (await db.execute(count_q)).scalar() or 0

    q_stmt = (
        select(Image, User.email, User.name)
        .join(User, Image.user_id == User.id)
        .where(where)
        .order_by(desc(Image.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(q_stmt)

    images = []
    for row in result.all():
        img, email, name = row
        images.append({
            "id": str(img.id),
            "prompt": img.prompt,
            "image_url": img.image_url,
            "model": img.model,
            "width": img.width,
            "height": img.height,
            "is_public": img.is_public,
            "likes_count": img.likes_count,
            "created_at": img.created_at.isoformat() if img.created_at else None,
            "user_id": str(img.user_id),
            "user_email": email,
            "user_name": name,
        })

    return images, total


# ── Platform Statistics ────────────────────────────
async def get_platform_stats(db: AsyncSession) -> dict:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start.replace(day=1)

    total_users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    new_users_today = (await db.execute(
        select(func.count()).select_from(User).where(User.created_at >= today_start)
    )).scalar() or 0
    new_users_week = (await db.execute(
        select(func.count()).select_from(User).where(User.created_at >= week_start)
    )).scalar() or 0
    banned_users = (await db.execute(
        select(func.count()).select_from(User).where(User.is_banned == True)
    )).scalar() or 0

    total_images = (await db.execute(select(func.count()).select_from(Image))).scalar() or 0
    images_today = (await db.execute(
        select(func.count()).select_from(Image).where(Image.created_at >= today_start)
    )).scalar() or 0
    images_week = (await db.execute(
        select(func.count()).select_from(Image).where(Image.created_at >= week_start)
    )).scalar() or 0
    public_images = (await db.execute(
        select(func.count()).select_from(Image).where(Image.is_public == True)
    )).scalar() or 0

    total_jobs = (await db.execute(select(func.count()).select_from(Job))).scalar() or 0
    jobs_today = (await db.execute(
        select(func.count()).select_from(Job).where(Job.created_at >= today_start)
    )).scalar() or 0
    failed_jobs = (await db.execute(
        select(func.count()).select_from(Job).where(Job.status == "FAILED")
    )).scalar() or 0
    active_jobs = (await db.execute(
        select(func.count()).select_from(Job).where(Job.status.in_(["PENDING", "PROCESSING"]))
    )).scalar() or 0

    total_credits_used = (await db.execute(
        select(func.coalesce(func.sum(UsageLog.credits_used), 0))
    )).scalar() or 0
    credits_used_today = (await db.execute(
        select(func.coalesce(func.sum(UsageLog.credits_used), 0))
        .where(UsageLog.created_at >= today_start)
    )).scalar() or 0

    models_q = (
        select(Image.model, func.count().label("count"))
        .group_by(Image.model)
        .order_by(desc("count"))
    )
    models_result = await db.execute(models_q)
    model_usage = [{"model": row[0], "count": row[1]} for row in models_result.all()]

    daily_users = (
        select(
            cast(User.created_at, Date).label("day"),
            func.count().label("count"),
        )
        .where(User.created_at >= week_start)
        .group_by(cast(User.created_at, Date))
        .order_by(desc("day"))
    )
    daily_users_result = await db.execute(daily_users)
    daily_new_users = [{"date": str(row[0]), "count": row[1]} for row in daily_users_result.all()]

    daily_images = (
        select(
            cast(Image.created_at, Date).label("day"),
            func.count().label("count"),
        )
        .where(Image.created_at >= week_start)
        .group_by(cast(Image.created_at, Date))
        .order_by(desc("day"))
    )
    daily_images_result = await db.execute(daily_images)
    daily_new_images = [{"date": str(row[0]), "count": row[1]} for row in daily_images_result.all()]

    return {
        "users": {
            "total": total_users,
            "new_today": new_users_today,
            "new_this_week": new_users_week,
            "banned": banned_users,
        },
        "images": {
            "total": total_images,
            "today": images_today,
            "this_week": images_week,
            "public": public_images,
        },
        "jobs": {
            "total": total_jobs,
            "today": jobs_today,
            "failed": failed_jobs,
            "active": active_jobs,
        },
        "credits": {
            "total_used": total_credits_used,
            "used_today": credits_used_today,
        },
        "model_usage": model_usage,
        "daily_new_users": daily_new_users,
        "daily_new_images": daily_new_images,
    }


# ── Prompt Analytics ───────────────────────────────
async def get_prompt_analytics(db: AsyncSession, days: int = 30) -> dict:
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)

    total_prompts = (await db.execute(
        select(func.count()).select_from(PromptHistory).where(PromptHistory.created_at >= since)
    )).scalar() or 0

    avg_length = (await db.execute(
        select(func.avg(func.length(PromptHistory.original_prompt)))
        .where(PromptHistory.created_at >= since)
    )).scalar() or 0

    actions_q = (
        select(PromptHistory.action, func.count().label("count"))
        .where(PromptHistory.created_at >= since)
        .group_by(PromptHistory.action)
        .order_by(desc("count"))
    )
    actions_result = await db.execute(actions_q)
    action_breakdown = [{"action": row[0], "count": row[1]} for row in actions_result.all()]

    models_q = (
        select(PromptHistory.model_target, func.count().label("count"))
        .where(and_(PromptHistory.created_at >= since, PromptHistory.model_target.isnot(None)))
        .group_by(PromptHistory.model_target)
        .order_by(desc("count"))
    )
    models_result = await db.execute(models_q)
    model_targets = [{"model": row[0], "count": row[1]} for row in models_result.all()]

    safety_flagged = (await db.execute(
        select(func.count()).select_from(PromptHistory)
        .where(and_(PromptHistory.created_at >= since, PromptHistory.is_safe == False))
    )).scalar() or 0

    daily_q = (
        select(
            cast(PromptHistory.created_at, Date).label("day"),
            func.count().label("count"),
        )
        .where(PromptHistory.created_at >= since)
        .group_by(cast(PromptHistory.created_at, Date))
        .order_by(desc("day"))
    )
    daily_result = await db.execute(daily_q)
    daily_prompts = [{"date": str(row[0]), "count": row[1]} for row in daily_result.all()]

    return {
        "total_prompts": total_prompts,
        "average_length": round(avg_length),
        "action_breakdown": action_breakdown,
        "model_targets": model_targets,
        "safety_flagged": safety_flagged,
        "daily_prompts": daily_prompts,
    }


# ── System Health ──────────────────────────────────
async def get_system_health(db: AsyncSession) -> dict:
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    recent_errors = (await db.execute(
        select(func.count()).select_from(Job)
        .where(and_(Job.status == "FAILED", Job.created_at >= datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)))
    )).scalar() or 0

    queue_pending = (await db.execute(
        select(func.count()).select_from(Job).where(Job.status == "PENDING")
    )).scalar() or 0

    queue_processing = (await db.execute(
        select(func.count()).select_from(Job).where(Job.status == "PROCESSING")
    )).scalar() or 0

    avg_job_time = (await db.execute(
        select(func.avg(
            func.extract("epoch", Job.completed_at) - func.extract("epoch", Job.created_at)
        ))
        .where(and_(Job.status == "COMPLETED", Job.completed_at.isnot(None)))
    )).scalar() or 0

    return {
        "database": db_status,
        "recent_errors_1h": recent_errors,
        "queue": {
            "pending": queue_pending,
            "processing": queue_processing,
            "total": queue_pending + queue_processing,
        },
        "avg_job_time_seconds": round(avg_job_time, 1) if avg_job_time else 0,
        "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
    }


# ── Audit Log Queries ──────────────────────────────
async def get_audit_logs(
    db: AsyncSession,
    admin_id: Optional[str] = None,
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
) -> Tuple[List[dict], int]:
    conditions = []
    if admin_id:
        conditions.append(AdminAuditLog.admin_id == admin_id)
    if action:
        conditions.append(AdminAuditLog.action == action)
    if target_type:
        conditions.append(AdminAuditLog.target_type == target_type)

    where = and_(*conditions) if conditions else True

    count_q = select(func.count()).select_from(AdminAuditLog).where(where)
    total = (await db.execute(count_q)).scalar() or 0

    q_stmt = (
        select(AdminAuditLog, User.email, User.name)
        .join(User, AdminAuditLog.admin_id == User.id)
        .where(where)
        .order_by(desc(AdminAuditLog.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(q_stmt)

    logs = []
    for row in result.all():
        log, email, name = row
        logs.append({
            "id": str(log.id),
            "admin_email": email,
            "admin_name": name,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "details": log.details,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })

    return logs, total
