"""Webhook routes: Stripe events, Solana (Helius) transaction confirmations."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Header, Request, status

from app.config import settings

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stripe webhook
# ---------------------------------------------------------------------------


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(None, alias="Stripe-Signature"),
) -> dict[str, bool]:
    """Handle incoming Stripe webhook events."""
    body = await request.body()

    # Verify signature if webhook secret is configured
    if settings.STRIPE_WEBHOOK_SECRET:
        if not stripe_signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe-Signature header",
            )
        # TODO: implement real Stripe signature verification
        # import stripe
        # try:
        #     event = stripe.Webhook.construct_event(
        #         body, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        #     )
        # except stripe.error.SignatureVerificationError:
        #     raise HTTPException(status_code=400, detail="Invalid signature")
    else:
        logger.warning(
            "STRIPE_WEBHOOK_SECRET not configured; skipping signature verification"
        )

    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    event_type = event.get("type", "unknown")
    event_id = event.get("id", "unknown")
    logger.info("Received Stripe event: type=%s id=%s", event_type, event_id)

    handler = _STRIPE_HANDLERS.get(event_type)
    if handler:
        await handler(event)
    else:
        logger.info("Unhandled Stripe event type: %s", event_type)

    return {"received": True}


async def _handle_checkout_completed(event: dict[str, Any]) -> None:
    """Handle checkout.session.completed event."""
    session = event.get("data", {}).get("object", {})
    logger.info(
        "Checkout completed: session_id=%s customer=%s",
        session.get("id"),
        session.get("customer"),
    )
    # TODO: implement real handler
    # - Look up user by metadata.user_id or customer
    # - Create/activate subscription or activation record
    # - Update user.stripe_customer_id if not set


async def _handle_subscription_updated(event: dict[str, Any]) -> None:
    """Handle customer.subscription.updated event."""
    subscription = event.get("data", {}).get("object", {})
    logger.info(
        "Subscription updated: sub_id=%s status=%s",
        subscription.get("id"),
        subscription.get("status"),
    )
    # TODO: implement real handler
    # - Update activation status based on subscription status


async def _handle_subscription_deleted(event: dict[str, Any]) -> None:
    """Handle customer.subscription.deleted event."""
    subscription = event.get("data", {}).get("object", {})
    logger.info("Subscription deleted: sub_id=%s", subscription.get("id"))
    # TODO: implement real handler
    # - Cancel related activation
    # - Update user subscription state


async def _handle_invoice_payment_succeeded(event: dict[str, Any]) -> None:
    """Handle invoice.payment_succeeded event."""
    invoice = event.get("data", {}).get("object", {})
    logger.info(
        "Invoice payment succeeded: invoice_id=%s amount=%s",
        invoice.get("id"),
        invoice.get("amount_paid"),
    )
    # TODO: implement real handler
    # - Record payment in payments table
    # - Extend activation period if applicable


async def _handle_invoice_payment_failed(event: dict[str, Any]) -> None:
    """Handle invoice.payment_failed event."""
    invoice = event.get("data", {}).get("object", {})
    logger.info("Invoice payment failed: invoice_id=%s", invoice.get("id"))
    # TODO: implement real handler
    # - Send notification to user
    # - Grace period logic
    # - Eventually pause/cancel activation


_STRIPE_HANDLERS: dict[str, Any] = {
    "checkout.session.completed": _handle_checkout_completed,
    "customer.subscription.updated": _handle_subscription_updated,
    "customer.subscription.deleted": _handle_subscription_deleted,
    "invoice.payment_succeeded": _handle_invoice_payment_succeeded,
    "invoice.payment_failed": _handle_invoice_payment_failed,
}


# ---------------------------------------------------------------------------
# Solana (Helius) webhook
# ---------------------------------------------------------------------------


@router.post("/solana")
async def solana_webhook(request: Request) -> dict[str, bool]:
    """Handle incoming Helius webhook for on-chain transaction confirmations."""
    body = await request.body()

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    # TODO: implement real Helius webhook verification and handling
    # - Verify webhook signature/auth
    # - Parse transaction details
    # - Match to pending deposits/payments
    # - Update credit balances or confirm activation payments

    if isinstance(payload, list):
        for tx in payload:
            logger.info(
                "Solana tx confirmed: signature=%s type=%s",
                tx.get("signature", "unknown"),
                tx.get("type", "unknown"),
            )
    else:
        logger.info("Solana webhook payload received: %s", type(payload).__name__)

    return {"received": True}
