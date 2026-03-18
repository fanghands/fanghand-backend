import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activation import Activation, ActivationStatus
from app.models.hand import Hand, HandStatus
from app.services.openfang_client import openfang_client


class ActivationService:
    """Manages Hand activations: create, pause, resume, cancel."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: uuid.UUID, data: dict) -> Activation:
        """Create a new activation for a user.

        Args:
            user_id: The user activating the hand.
            data: Dict with keys: hand_id, config, delivery_channel,
                  delivery_target, payment_currency.

        Returns:
            The newly created Activation.

        Raises:
            HTTPException 409: If user already has an active activation for this hand.
            HTTPException 404: If the hand does not exist or is not live.
        """
        hand_id = data["hand_id"]

        # Check for duplicate active activation
        existing = await self.db.execute(
            select(Activation).where(
                Activation.user_id == user_id,
                Activation.hand_id == hand_id,
                Activation.status.in_([ActivationStatus.active, ActivationStatus.paused]),
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have an active activation for this Hand.",
            )

        # Verify hand exists and is live
        result = await self.db.execute(select(Hand).where(Hand.id == hand_id))
        hand = result.scalar_one_or_none()
        if hand is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hand not found.",
            )
        if hand.status != HandStatus.live:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hand is not currently live.",
            )

        # Spawn agent in OpenFang
        config = data.get("config", {})
        delivery = {
            "channel": data.get("delivery_channel", "dashboard"),
            "target": data.get("delivery_target"),
        }
        agent_id = await openfang_client.spawn_hand(
            hand_slug=hand.openfang_hand_slug or hand.slug,
            config=config,
            delivery=delivery,
        )

        # Create activation record
        activation = Activation(
            user_id=user_id,
            hand_id=hand_id,
            status=ActivationStatus.active,
            config=config,
            delivery_channel=delivery["channel"],
            delivery_target=delivery.get("target"),
            openfang_agent_id=agent_id,
            payment_currency=data.get("payment_currency", "usd"),
            activated_at=datetime.now(timezone.utc),
        )
        self.db.add(activation)

        # Update hand activation count
        hand.total_activations = (hand.total_activations or 0) + 1

        await self.db.flush()
        await self.db.refresh(activation)
        logger.info(
            "Activation created: id={} user={} hand={} agent={}",
            activation.id,
            user_id,
            hand_id,
            agent_id,
        )
        return activation

    async def pause(self, activation_id: uuid.UUID, user_id: uuid.UUID) -> Activation:
        """Pause an active activation.

        Raises:
            HTTPException 400: If activation is not in 'active' status.
        """
        activation = await self._get_owned(activation_id, user_id)
        if activation.status != ActivationStatus.active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Activation is not active; cannot pause.",
            )

        await openfang_client.pause_hand(activation.openfang_agent_id)

        activation.status = ActivationStatus.paused
        activation.paused_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(activation)
        logger.info("Activation paused: id={}", activation_id)
        return activation

    async def resume(self, activation_id: uuid.UUID, user_id: uuid.UUID) -> Activation:
        """Resume a paused activation.

        Raises:
            HTTPException 400: If activation is not in 'paused' status.
        """
        activation = await self._get_owned(activation_id, user_id)
        if activation.status != ActivationStatus.paused:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Activation is not paused; cannot resume.",
            )

        await openfang_client.resume_hand(activation.openfang_agent_id)

        activation.status = ActivationStatus.active
        activation.paused_at = None
        await self.db.flush()
        await self.db.refresh(activation)
        logger.info("Activation resumed: id={}", activation_id)
        return activation

    async def cancel(self, activation_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Cancel an activation and deactivate the agent.

        Raises:
            HTTPException 400: If activation is already cancelled.
        """
        activation = await self._get_owned(activation_id, user_id)
        if activation.status == ActivationStatus.cancelled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Activation is already cancelled.",
            )

        if activation.openfang_agent_id:
            await openfang_client.delete_agent(activation.openfang_agent_id)

        activation.status = ActivationStatus.cancelled
        activation.cancelled_at = datetime.now(timezone.utc)
        await self.db.flush()
        logger.info("Activation cancelled: id={}", activation_id)

    async def _get_owned(
        self, activation_id: uuid.UUID, user_id: uuid.UUID
    ) -> Activation:
        """Fetch an activation that belongs to the given user.

        Raises:
            HTTPException 404: If activation not found or not owned by user.
        """
        result = await self.db.execute(
            select(Activation).where(
                Activation.id == activation_id,
                Activation.user_id == user_id,
            )
        )
        activation = result.scalar_one_or_none()
        if activation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activation not found.",
            )
        return activation
