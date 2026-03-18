import uuid

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment


class BurnService:
    """Handles FGH token burns (50% of FGH payments)."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def execute_burn(
        self,
        payment_id: uuid.UUID,
        fgh_amount: int,
        trigger_type: str = "payment",
    ) -> str:
        """Execute a 50% FGH burn for a payment.

        Args:
            payment_id: The associated payment record ID.
            fgh_amount: Total FGH amount (in smallest unit) from the payment.
            trigger_type: What triggered the burn (e.g. 'payment').

        Returns:
            The burn transaction signature (mock).
        """
        burn_amount = fgh_amount // 2  # 50% burn

        # TODO: real SPL token burn on-chain
        # 1. Build burn instruction for FGH mint
        # 2. Sign with platform burn keypair
        # 3. Send and confirm transaction
        mock_tx_sig = f"burn_{uuid.uuid4().hex[:16]}"

        logger.warning(
            "FGH burn (stub): payment={} total={} burn_amount={} tx={}",
            payment_id,
            fgh_amount,
            burn_amount,
            mock_tx_sig,
        )

        # TODO: Create FghBurn record once the model is available
        # The FghBurn model should track:
        #   - id, payment_id, fgh_amount, burn_amount, trigger_type,
        #   - tx_signature, confirmed_at, created_at
        #
        # Example:
        # from app.models.fgh_burn import FghBurn
        # burn_record = FghBurn(
        #     payment_id=payment_id,
        #     fgh_amount=fgh_amount,
        #     burn_amount=burn_amount,
        #     trigger_type=trigger_type,
        #     tx_signature=mock_tx_sig,
        # )
        # self.db.add(burn_record)
        # await self.db.flush()

        # Update the payment record with burn info
        from sqlalchemy import select

        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if payment:
            payment.fgh_burned_amount = burn_amount
            payment.burn_tx_signature = mock_tx_sig
            await self.db.flush()

        logger.info(
            "Burn executed: payment={} burned={} tx={}",
            payment_id,
            burn_amount,
            mock_tx_sig,
        )
        return mock_tx_sig
