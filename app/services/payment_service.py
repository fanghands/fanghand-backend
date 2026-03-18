import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activation import Activation, ActivationStatus
from app.models.hand import Hand
from app.models.payment import Payment, PaymentStatus, PaymentType, PaymentCurrencyType
from app.models.user import User
from app.services.activation_service import ActivationService


class PaymentService:
    """Handles Stripe checkout, portal, and webhook events."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_checkout_session(
        self,
        user: User,
        hand_id: uuid.UUID,
        price_id: str,
        success_url: str,
        cancel_url: str,
        config: dict | None = None,
        delivery: dict | None = None,
    ) -> dict:
        """Create a Stripe checkout session for a Hand subscription.

        Returns:
            Dict with session_id and url.
        """
        # TODO: real Stripe checkout session creation via stripe.checkout.Session.create
        mock_session_id = f"cs_mock_{uuid.uuid4().hex[:16]}"
        logger.info(
            "Stripe checkout (stub): user={} hand={} price={} -> session={}",
            user.id,
            hand_id,
            price_id,
            mock_session_id,
        )
        return {
            "session_id": mock_session_id,
            "url": f"https://checkout.stripe.com/mock/{mock_session_id}",
        }

    async def get_portal_url(self, user: User, return_url: str) -> str:
        """Get a Stripe customer portal URL for managing subscriptions.

        Returns:
            Portal URL string.
        """
        # TODO: real Stripe billing portal via stripe.billing_portal.Session.create
        mock_url = f"https://billing.stripe.com/mock/portal/{user.stripe_customer_id or 'new'}"
        logger.info("Stripe portal (stub): user={} -> url={}", user.id, mock_url)
        return mock_url

    async def handle_checkout_completed(self, session: dict) -> None:
        """Handle Stripe checkout.session.completed webhook event.

        Extracts metadata and creates an activation.
        """
        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")
        hand_id = metadata.get("hand_id")
        subscription_id = session.get("subscription")

        if not user_id or not hand_id:
            logger.warning(
                "checkout.session.completed missing metadata: session={}",
                session.get("id"),
            )
            return

        logger.info(
            "Checkout completed: user={} hand={} subscription={}",
            user_id,
            hand_id,
            subscription_id,
        )

        # Create activation
        activation_svc = ActivationService(self.db)
        activation_data = {
            "hand_id": uuid.UUID(hand_id),
            "config": metadata.get("config", {}),
            "delivery_channel": metadata.get("delivery_channel", "dashboard"),
            "delivery_target": metadata.get("delivery_target"),
            "payment_currency": "usd",
        }
        activation = await activation_svc.create(
            user_id=uuid.UUID(user_id),
            data=activation_data,
        )

        # Link Stripe subscription to activation
        if subscription_id:
            activation.stripe_subscription_id = subscription_id
            await self.db.flush()

        # Create payment record
        payment = Payment(
            user_id=uuid.UUID(user_id),
            type=PaymentType.subscription,
            status=PaymentStatus.confirmed,
            currency=PaymentCurrencyType.usd,
            amount_cents=session.get("amount_total"),
            hand_id=uuid.UUID(hand_id),
            activation_id=activation.id,
            stripe_payment_intent_id=session.get("payment_intent"),
            stripe_subscription_id=subscription_id,
            confirmed_at=datetime.now(timezone.utc),
        )
        self.db.add(payment)
        await self.db.flush()

        logger.info(
            "Payment recorded: payment_id={} activation_id={}",
            payment.id,
            activation.id,
        )

    async def handle_subscription_updated(self, sub: dict) -> None:
        """Handle Stripe customer.subscription.updated webhook event.

        Updates activation status and period dates.
        """
        subscription_id = sub.get("id")
        if not subscription_id:
            return

        result = await self.db.execute(
            select(Activation).where(
                Activation.stripe_subscription_id == subscription_id
            )
        )
        activation = result.scalar_one_or_none()
        if activation is None:
            logger.warning(
                "subscription.updated: no activation for subscription={}",
                subscription_id,
            )
            return

        # Update status based on Stripe subscription status
        stripe_status = sub.get("status", "")
        if stripe_status == "active":
            activation.status = ActivationStatus.active
        elif stripe_status in ("past_due", "unpaid"):
            activation.status = ActivationStatus.paused
            activation.paused_at = datetime.now(timezone.utc)

        # Update period dates
        period = sub.get("current_period_start")
        if period:
            activation.current_period_start = datetime.fromtimestamp(
                period, tz=timezone.utc
            )
        period_end = sub.get("current_period_end")
        if period_end:
            activation.current_period_end = datetime.fromtimestamp(
                period_end, tz=timezone.utc
            )

        await self.db.flush()
        logger.info(
            "Subscription updated: subscription={} activation={} status={}",
            subscription_id,
            activation.id,
            activation.status,
        )

    async def handle_subscription_deleted(self, sub: dict) -> None:
        """Handle Stripe customer.subscription.deleted webhook event.

        Cancels the associated activation.
        """
        subscription_id = sub.get("id")
        if not subscription_id:
            return

        result = await self.db.execute(
            select(Activation).where(
                Activation.stripe_subscription_id == subscription_id
            )
        )
        activation = result.scalar_one_or_none()
        if activation is None:
            logger.warning(
                "subscription.deleted: no activation for subscription={}",
                subscription_id,
            )
            return

        # Cancel the activation
        if activation.status != ActivationStatus.cancelled:
            from app.services.openfang_client import openfang_client

            if activation.openfang_agent_id:
                await openfang_client.delete_agent(activation.openfang_agent_id)

            activation.status = ActivationStatus.cancelled
            activation.cancelled_at = datetime.now(timezone.utc)
            await self.db.flush()

        logger.info(
            "Subscription deleted: subscription={} activation={} cancelled",
            subscription_id,
            activation.id,
        )
