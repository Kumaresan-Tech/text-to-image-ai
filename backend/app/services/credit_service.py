from typing import Optional, List, Tuple
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, and_, desc, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, CreditTransaction, UsageLog, Plan


CREDIT_COSTS = {
    "generate": 1,
    "enhance": 0,
    "optimize": 0,
}


async def get_user_plan(db: AsyncSession, plan_id: str) -> Optional[Plan]:
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    return result.scalar_one_or_none()


async def deduct_credits(
    db: AsyncSession,
    user_id: str,
    amount: int,
    action: str = "generate",
    description: Optional[str] = None,
    reference_id: Optional[str] = None,
    model: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> CreditTransaction:
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
    if user.credits < amount:
        raise ValueError(f"Insufficient credits: {user.credits} available, {amount} required")

    user.credits -= amount
    await db.flush()

    tx = CreditTransaction(
        user_id=user_id,
        amount=-amount,
        balance_after=user.credits,
        type="debit",
        description=description or f"Used {amount} credit(s) for {action}",
        reference_id=reference_id,
    )
    db.add(tx)

    log = UsageLog(
        user_id=user_id,
        action=action,
        credits_used=amount,
        model=model,
        details=metadata,
    )
    db.add(log)
    await db.flush()

    return tx


async def add_credits(
    db: AsyncSession,
    user_id: str,
    amount: int,
    type: str = "purchase",
    description: Optional[str] = None,
    reference_id: Optional[str] = None,
) -> CreditTransaction:
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
    user.credits += amount
    await db.flush()

    tx = CreditTransaction(
        user_id=user_id,
        amount=amount,
        balance_after=user.credits,
        type=type,
        description=description or f"Added {amount} credit(s)",
        reference_id=reference_id,
    )
    db.add(tx)
    await db.flush()

    return tx


async def get_credit_transactions(
    db: AsyncSession,
    user_id: str,
    tx_type: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[CreditTransaction], int]:
    conditions = [CreditTransaction.user_id == user_id]
    if tx_type:
        conditions.append(CreditTransaction.type == tx_type)

    where = and_(*conditions)
    count_q = select(func.count()).select_from(CreditTransaction).where(where)
    total = (await db.execute(count_q)).scalar() or 0

    q = (
        select(CreditTransaction)
        .where(where)
        .order_by(desc(CreditTransaction.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_usage_stats(db: AsyncSession, user_id: str) -> dict:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today_start.replace(day=1)

    total_q = select(
        func.count(),
        func.coalesce(func.sum(UsageLog.credits_used), 0),
    ).where(UsageLog.user_id == user_id)
    total_result = (await db.execute(total_q)).first()
    total_generations = total_result[0]
    total_credits = total_result[1]

    today_q = select(
        func.count(),
        func.coalesce(func.sum(UsageLog.credits_used), 0),
    ).where(
        and_(UsageLog.user_id == user_id, UsageLog.created_at >= today_start)
    )
    today_result = (await db.execute(today_q)).first()
    gen_today = today_result[0]
    credits_today = today_result[1]

    month_q = select(
        func.count(),
        func.coalesce(func.sum(UsageLog.credits_used), 0),
    ).where(
        and_(UsageLog.user_id == user_id, UsageLog.created_at >= month_start)
    )
    month_result = (await db.execute(month_q)).first()
    gen_month = month_result[0]
    credits_month = month_result[1]

    models_q = (
        select(UsageLog.model, func.count().label("count"))
        .where(
            and_(UsageLog.user_id == user_id, UsageLog.model.isnot(None))
        )
        .group_by(UsageLog.model)
        .order_by(desc("count"))
        .limit(5)
    )
    models_result = await db.execute(models_q)
    top_models = [{"model": row[0], "count": row[1]} for row in models_result.all()]

    daily_q = (
        select(
            cast(UsageLog.created_at, Date).label("day"),
            func.count().label("generations"),
            func.coalesce(func.sum(UsageLog.credits_used), 0).label("credits"),
        )
        .where(
            and_(UsageLog.user_id == user_id, UsageLog.created_at >= month_start)
        )
        .group_by(cast(UsageLog.created_at, Date))
        .order_by(desc("day"))
        .limit(30)
    )
    daily_result = await db.execute(daily_q)
    daily_usage = [
        {"date": str(row[0]), "generations": row[1], "credits": row[2]}
        for row in daily_result.all()
    ]

    return {
        "total_generations": total_generations,
        "total_credits_used": total_credits,
        "generations_today": gen_today,
        "credits_used_today": credits_today,
        "generations_this_month": gen_month,
        "credits_used_this_month": credits_month,
        "top_models": top_models,
        "daily_usage": daily_usage,
    }


async def seed_plans(db: AsyncSession) -> None:
    existing = (await db.execute(select(Plan))).scalars().all()
    if existing:
        return

    plans = [
        Plan(
            id="FREE",
            name="Free",
            credits=50,
            price_monthly=0,
            features=["50 generations/month", "SDXL 1.0", "Standard quality", "Private images"],
        ),
        Plan(
            id="STARTER",
            name="Starter",
            credits=500,
            price_monthly=9.99,
            features=["500 generations/month", "All models", "HD quality", "Priority queue", "Private images"],
            stripe_price_id="price_starter_monthly",
        ),
        Plan(
            id="PRO",
            name="Pro",
            credits=2000,
            price_monthly=29.99,
            features=["2,000 generations/month", "All models", "Ultra quality", "Priority queue", "API access", "Private images"],
            stripe_price_id="price_pro_monthly",
        ),
        Plan(
            id="ENTERPRISE",
            name="Enterprise",
            credits=10000,
            price_monthly=99.99,
            features=["10,000 generations/month", "All models", "Ultra quality", "Dedicated GPU", "API access", "Custom models", "SLA support"],
            stripe_price_id="price_enterprise_monthly",
        ),
    ]
    for plan in plans:
        db.add(plan)
    await db.flush()
