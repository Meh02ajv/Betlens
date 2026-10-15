from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from app.core.config import settings
from app.core.deps import CurrentUserId, DbSession
from app.db.models import Subscription, User

router = APIRouter()


@router.post("/checkout", response_model=dict)
async def create_checkout(user_id: CurrentUserId, db: DbSession) -> dict:
    """Create a Stripe Checkout session for Pro plan."""
    if not settings.stripe_secret_key:
        return {
            "url": None,
            "message": "Stripe not configured. Set STRIPE_SECRET_KEY to enable billing.",
            "mock": True,
        }

    import stripe
    stripe.api_key = settings.stripe_secret_key

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    session = stripe.checkout.Session.create(
        customer_email=user.email,
        payment_method_types=["card"],
        line_items=[{"price": settings.stripe_pro_price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{settings.frontend_url}/settings?upgraded=true",
        cancel_url=f"{settings.frontend_url}/settings",
        metadata={"user_id": str(user_id)},
    )
    return {"url": session.url}


@router.post("/portal", response_model=dict)
async def create_portal(user_id: CurrentUserId, db: DbSession) -> dict:
    """Create a Stripe Customer Portal session."""
    if not settings.stripe_secret_key:
        return {"url": None, "message": "Stripe not configured.", "mock": True}

    import stripe
    stripe.api_key = settings.stripe_secret_key

    sub = await db.scalar(select(Subscription).where(Subscription.user_id == user_id))
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No active subscription found")

    session = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=f"{settings.frontend_url}/settings",
    )
    return {"url": session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: DbSession) -> dict:
    """Handle Stripe webhook events."""
    if not settings.stripe_secret_key:
        return {"received": True}

    import stripe
    stripe.api_key = settings.stripe_secret_key

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        raise HTTPException(status_code=400, detail="Invalid webhook signature") from e

    if event["type"] == "checkout.session.completed":
        session_data = event["data"]["object"]
        user_id = session_data["metadata"].get("user_id")
        if user_id:
            user = await db.get(User, user_id)
            if user:
                user.plan = "pro"
                sub = await db.scalar(select(Subscription).where(Subscription.user_id == user.id))
                if sub:
                    sub.plan = "pro"
                    sub.stripe_customer_id = session_data.get("customer")
                    sub.stripe_subscription_id = session_data.get("subscription")
                    sub.status = "active"
                await db.flush()

    elif event["type"] == "customer.subscription.deleted":
        sub_data = event["data"]["object"]
        sub = await db.scalar(
            select(Subscription).where(Subscription.stripe_subscription_id == sub_data["id"])
        )
        if sub:
            sub.status = "cancelled"
            user = await db.get(User, sub.user_id)
            if user:
                user.plan = "free"
            await db.flush()

    return {"received": True}