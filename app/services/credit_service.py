import uuid

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.solana_service import solana_service


class CreditWalletService:
    """Manages user credit wallet: deposits and charges."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def deposit(
        self,
        user: User,
        tx_signature: str,
        expected_lamports: int,
    ) -> dict:
        """Deposit SOL into the user's credit wallet.

        Args:
            user: The user making the deposit.
            tx_signature: Solana transaction signature.
            expected_lamports: Amount in lamports to credit.

        Returns:
            Dict with balance_lamports and deposited amount.

        Raises:
            HTTPException 409: If tx_signature was already used (double-spend).
            HTTPException 400: If on-chain verification fails.
        """
        # Check tx_signature not already used (prevent double-spend)
        # TODO: Query CreditTransaction model for existing tx_signature
        # once the model is available:
        #
        # from app.models.credit_transaction import CreditTransaction
        # from sqlalchemy import select
        # existing = await self.db.execute(
        #     select(CreditTransaction).where(
        #         CreditTransaction.tx_signature == tx_signature
        #     )
        # )
        # if existing.scalar_one_or_none() is not None:
        #     raise HTTPException(
        #         status_code=status.HTTP_409_CONFLICT,
        #         detail="Transaction signature already used.",
        #     )
        logger.debug(
            "Double-spend check (stub): tx={} - skipping until CreditTransaction model exists",
            tx_signature,
        )

        # TODO: verify on-chain via solana_service
        verified = await solana_service.verify_sol_transfer(
            tx_signature=tx_signature,
            expected_lamports=expected_lamports,
        )
        if not verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="On-chain verification failed for the provided transaction.",
            )

        # Credit user balance
        user.credit_balance_lamports = (
            user.credit_balance_lamports or 0
        ) + expected_lamports

        # TODO: Create CreditTransaction record once the model is available
        # credit_tx = CreditTransaction(
        #     user_id=user.id,
        #     type="deposit",
        #     amount_lamports=expected_lamports,
        #     tx_signature=tx_signature,
        #     description="SOL deposit",
        # )
        # self.db.add(credit_tx)

        await self.db.flush()
        await self.db.refresh(user)

        logger.info(
            "Credit deposit: user={} amount={} new_balance={}",
            user.id,
            expected_lamports,
            user.credit_balance_lamports,
        )
        return {
            "balance_lamports": user.credit_balance_lamports,
            "deposited": expected_lamports,
        }

    async def charge(
        self,
        user: User,
        lamports: int,
        run_id: uuid.UUID,
        description: str = "",
    ) -> None:
        """Charge lamports from the user's credit wallet.

        Args:
            user: The user to charge.
            lamports: Amount to deduct.
            run_id: Associated run ID.
            description: Human-readable description.

        Raises:
            HTTPException 402: If insufficient balance.
        """
        current_balance = user.credit_balance_lamports or 0
        if current_balance < lamports:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Insufficient credit balance. Have {current_balance}, need {lamports}.",
            )

        user.credit_balance_lamports = current_balance - lamports

        # TODO: Create CreditTransaction record once the model is available
        # credit_tx = CreditTransaction(
        #     user_id=user.id,
        #     type="charge",
        #     amount_lamports=-lamports,
        #     run_id=run_id,
        #     description=description,
        # )
        # self.db.add(credit_tx)

        await self.db.flush()

        logger.info(
            "Credit charge: user={} amount={} run={} new_balance={}",
            user.id,
            lamports,
            run_id,
            user.credit_balance_lamports,
        )
