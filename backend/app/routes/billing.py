from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.config import settings
from app.models import User, Plan
from app.schemas import (
    PlanResponse,
    CreditsResponse,
    CheckoutRequest,
    CheckoutResponse,
    SubscriptionResponse,
    CancelSubscriptionRequest,
    CreditTransactionResponse,
    CreditTransactionListResponse,
    UsageStatsResponse,
    AddCreditsRequest,
)
from app.dependencies import get_current_user
from app.services.credit_service import (
    get_user_plan,
    get_credit_transactions,
    get_usage_stats,
    add_credits,
    seed_plans,
)
from app.services.stripe_service import (
    create_checkout_session,
    handle_webhook,
    cancel_subscription as stripe_cancel,
    get_user_subscription,
)

router = APIRouter(prefix="/api/billing", tags=["billing"])


# ── Plans ──────────────────────────────────────────
@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(db: AsyncSession = Depends(get_db)):
    await seed_plans(db)
    result = await db.execute(select(Plan).order_by(Plan.price_monthly))
    plans = result.scalars().all()
    return [PlanResponse.model_validate(p) for p in plans]


@router.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    plan = await get_user_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return PlanResponse.model_validate(plan)


# ── Credits ────────────────────────────────────────
@router.get("/credits", response_model=CreditsResponse)
async def get_credits(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    sub = await get_user_subscription(db, str(user.id))
    return CreditsResponse(
        credits=user.credits,
        plan=user.plan,
        subscription_status=sub.status if sub else None,
    )


@router.post("/credits/add", response_model=CreditTransactionResponse)
async def add_credits_endpoint(
    body: AddCreditsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tx = await add_credits(
        db, str(user.id), body.amount,
        type="manual",
        description=body.description or f"Added {body.amount} credits",
    )
    return CreditTransactionResponse.model_validate(tx)


# ── Checkout ───────────────────────────────────────
@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan = await get_user_plan(db, body.plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    result = await create_checkout_session(
        db, user, plan, body.success_url, body.cancel_url
    )
    return CheckoutResponse(**result)


# ── Subscription ───────────────────────────────────
@router.get("/subscription", response_model=Optional[SubscriptionResponse])
async def get_subscription(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await get_user_subscription(db, str(user.id))
    if not sub:
        return None

    plan = await get_user_plan(db, sub.plan_id)
    usage = await get_usage_stats(db, str(user.id))

    return SubscriptionResponse(
        id=str(sub.id),
        plan_id=sub.plan_id,
        plan_name=plan.name if plan else sub.plan_id,
        status=sub.status,
        current_period_start=sub.current_period_start,
        current_period_end=sub.current_period_end,
        cancel_at_period_end=sub.cancel_at_period_end,
        credits=user.credits,
        credits_used_this_period=usage["credits_used_this_month"],
    )


@router.post("/subscription/cancel")
async def cancel_user_subscription(
    body: CancelSubscriptionRequest = CancelSubscriptionRequest(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ok = await stripe_cancel(db, user)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to cancel subscription")
    return {"message": "Subscription will cancel at end of billing period"}


# ── Credit History ─────────────────────────────────
@router.get("/transactions", response_model=CreditTransactionListResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    type: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    txs, total = await get_credit_transactions(db, str(user.id), tx_type=type, page=page, per_page=per_page)
    return CreditTransactionListResponse(
        transactions=[CreditTransactionResponse.model_validate(tx) for tx in txs],
        total=total,
        page=page,
        per_page=per_page,
        has_next=(page * per_page) < total,
    )


# ── Usage Stats ────────────────────────────────────
@router.get("/usage", response_model=UsageStatsResponse)
async def usage_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await get_usage_stats(db, str(user.id))
    return UsageStatsResponse(**stats)


# ── Webhook ────────────────────────────────────────
@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    success = await handle_webhook(db, payload, sig_header)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook processing failed")

    return {"status": "ok"}
