from loguru import logger

from app.config import settings


class SolanaService:
    """Solana on-chain verification and balance queries."""

    def __init__(self) -> None:
        self.rpc_url = settings.SOLANA_RPC_URL
        self.platform_wallet = settings.PLATFORM_WALLET_PUBKEY
        self.fgh_mint = settings.FGH_TOKEN_MINT

    async def verify_sol_transfer(
        self,
        tx_signature: str,
        expected_lamports: int,
        max_age_slots: int = 150,
    ) -> bool:
        """Verify a SOL transfer on-chain.

        Args:
            tx_signature: The Solana transaction signature.
            expected_lamports: Expected amount transferred in lamports.
            max_age_slots: Maximum age of the transaction in slots.

        Returns:
            True if the transfer is verified.
        """
        # TODO: real Solana verification using solana-py
        # 1. Fetch transaction via RPC getTransaction
        # 2. Confirm recipient is platform_wallet
        # 3. Confirm amount >= expected_lamports
        # 4. Confirm finalized and within max_age_slots
        logger.warning(
            "solana verify_sol_transfer (stub): tx={} lamports={} -> returning True",
            tx_signature,
            expected_lamports,
        )
        return True

    async def verify_spl_transfer(
        self,
        tx_signature: str,
        mint: str,
        expected_amount: int,
    ) -> bool:
        """Verify an SPL token transfer on-chain.

        Args:
            tx_signature: The Solana transaction signature.
            mint: The SPL token mint address.
            expected_amount: Expected token amount (in smallest unit).

        Returns:
            True if the transfer is verified.
        """
        # TODO: real SPL token verification using solana-py
        # 1. Parse transaction for token transfer instructions
        # 2. Confirm mint, recipient, and amount
        logger.warning(
            "solana verify_spl_transfer (stub): tx={} mint={} amount={} -> returning True",
            tx_signature,
            mint,
            expected_amount,
        )
        return True

    async def get_fgh_balance(self, wallet_address: str) -> int:
        """Get FGH token balance for a wallet.

        Args:
            wallet_address: Solana wallet public key.

        Returns:
            Balance in smallest FGH unit.
        """
        # TODO: real FGH balance check via getTokenAccountsByOwner RPC
        mock_balance = 15_000_000_000  # Mock 15k FGH
        logger.warning(
            "solana get_fgh_balance (stub): wallet={} -> returning {}",
            wallet_address,
            mock_balance,
        )
        return mock_balance


solana_service = SolanaService()
