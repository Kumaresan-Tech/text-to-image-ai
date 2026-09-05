import json
import logging
from typing import Optional
from datetime import datetime

import stripe
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import User, Plan, Subscription
from app.services.credit_service import add_credits

logger = logging.getLogger(__name__)

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


async def create_checkout_session(
    db: AsyncSession,
    user: User,
    plan: Plan,
    success_url: str,
    cancel_url: str,
) -> dict:
    if not settings.STRIPE_SECRET_KEY:
        session_id = f"demo_session_{user.id}_{plan.id}"
        return {
            "checkout_url": f"{cancel_url}?demo=true&plan={plan.id}",
            "session_id": session_id,
        }

    customer_id = await get_or_create_stripe_customer(user)

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{
            "price": plan.stripe_price_id,
            "quantity": 1,
        }],
        mode="subscription",
        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=cancel_url,
        metadata={
            "user_id": str(user.id),
            "plan_id": plan.id,
        },
        subscription_data={
            "metadata": {
                "user_id": str(user.id),
                "plan_id": plan.id,
            },
        },
    )

    return {
        "checkout_url": session.url,
        "session_id": session.id,
    }


async def get_or_create_stripe_customer(user: User) -> str:
    existing_sub = (
        await db.execute(
            select(Subscription).where(
                Subscription.user_id == user.id,
                Subscription.stripe_customer_id.isnot(None),
            )
        )
    ).scalar_one_or_none()

    if existing_sub and existing_sub.stripe_customer_id:
        return existing_sub.stripe_customer_id

    customer = stripe.Customer.create(
        email=user.email,
        name=user.name or "",
        metadata={"user_id": str(user.id)},
    )
    return customer.id


async def handle_webhook(db: AsyncSession, payload: bytes, sig_header: str) -> bool:
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_WEBHOOK_SECRET:
        logger.warning("Stripe webhook received but Stripe is not configured")
        return False

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        logger.error(f"Webhook signature verification failed: {e}")
        return False

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(db, data)
    elif event_type == "invoice.paid":
        await _handle_invoice_paid(db, data)
    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(db, data)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(db, data)
    else:
        logger.info(f"Unhandled webhook event type: {event_type}")

    return True


async def _handle_checkout_completed(db: AsyncSession, data: dict) -> None:
    user_id = data.get("metadata", {}).get("user_id")
    plan_id = data.get("metadata", {}).get("plan_id")
    subscription_id = data.get("subscription")

    if not user_id or not plan_id:
        logger.error("Checkout completed missing metadata")
        return

    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    plan = (await db.execute(select(Plan).where(Plan.id == plan_id))).scalar_one_or_none()
    if not user or not plan:
        return

    sub = Subscription(
        user_id=user_id,
        plan_id=plan_id,
        stripe_subscription_id=subscription_id,
        stripe_customer_id=data.get("customer"),
        status="active",
        current_period_start=datetime.fromtimestamp(data.get("subscription_details", {}).get("current_period_start", 0)) if data.get("subscription_details") else None,
        current_period_end=datetime.fromtimestamp(data.get("subscription_details", {}).get("current_period_end", 0)) if data.get("subscription_details") else None,
    )
    db.add(sub)

    user.plan = plan_id
    await add_credits(db, user_id, plan.credits, type="subscription", description=f"Welcome credits from {plan.name} plan")
    await db.flush()
    logger.info(f"Subscription created for user {user_id}, plan {plan_id}")


async def _handle_invoice_paid(db: AsyncSession, data: dict) -> None:
    subscription_id = data.get("subscription")
    if not subscription_id:
        return

    sub = (await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
    )).scalar_one_or_none()
    if not sub:
        return

    plan = (await db.execute(select(Plan).where(Plan.id == sub.plan_id))).scalar_one_or_none()
    if plan:
        await add_credits(
            db, sub.user_id, plan.credits,
            type="subscription_renewal",
            description=f"Monthly credits from {plan.name} plan",
            reference_id=subscription_id,
        )
        logger.info(f"Credits renewed for user {sub.user_id}, plan {sub.plan_id}")


async def _handle_subscription_updated(db: AsyncSession, data: dict) -> None:
    subscription_id = data.get("id")
    status = data.get("status")

    sub = (await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
    )).scalar_one_or_none()
    if not sub:
        return

    sub.status = status
    sub.cancel_at_period_end = data.get("cancel_at_period_end", False)

    period = data.get("current_period", {})
    if period:
        sub.current_period_start = datetime.fromtimestamp(period.get("start", 0))
        sub.current_period_end = datetime.fromtimestamp(period.get("end", 0))

    await db.flush()


async def _handle_subscription_deleted(db: AsyncSession, data: dict) -> None:
    subscription_id = data.get("id")

    sub = (await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
    )).scalar_one_or_none()
    if not sub:
        return

    sub.status = "canceled"
    user = (await db.execute(select(User).where(User.id == sub.user_id))).scalar_one_or_none()
    if user:
        user.plan = "FREE"
    await db.flush()
    logger.info(f"Subscription canceled for user {sub.user_id}")


async def cancel_subscription(db: AsyncSession, user: User) -> bool:
    sub = (await db.execute(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.status == "active",
        )
    )).scalar_one_or_none()

    if not sub:
        return False

    if not settings.STRIPE_SECRET_KEY:
        sub.status = "canceled"
        user.plan = "FREE"
        await db.flush()
        return True

    try:
        stripe.Subscription.modify(
            sub.stripe_subscription_id,
            cancel_at_period_end=True,
        )
        sub.cancel_at_period_end = True
        await db.flush()
        return True
    except stripe.error.StripeError as e:
        logger.error(f"Failed to cancel Stripe subscription: {e}")
        return False


async def get_user_subscription(db: AsyncSession, user_id: str) -> Optional[Subscription]:
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status.in_(["active", "trialing"]),
        ).order_by(desc(Subscription.created_at))
    )
    return result.scalar_one_or_none()


async def get_upcoming_invoice(db: AsyncSession, user_id: str) -> Optional[dict]:
    sub = await get_user_subscription(db, user_id)
    if not sub or not sub.stripe_subscription_id or not settings.STRIPE_SECRET_KEY:
        return None

    try:
        invoice = stripe.Invoice.upcoming(
            subscription=sub.stripe_subscription_id,
        )
        return {
            "amount_due": invoice.amount_due / 100,
            "currency": invoice.currency,
            "period_start": datetime.fromtimestamp(invoice.period_start),
            "period_end": datetime.fromtimestamp(inventory.period_end) if hasattr(invoice, "period_end") else None,
        }
    except stripe.error.StripeError:
        return None
