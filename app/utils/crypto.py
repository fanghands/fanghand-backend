from loguru import logger


def verify_solana_signature(message: str, signature: str, wallet_address: str) -> bool:
    """Verify an ed25519 signature from a Solana wallet.

    Args:
        message: The original message that was signed.
        signature: The base58-encoded signature.
        wallet_address: The base58-encoded public key of the signer.

    Returns:
        True if the signature is valid, False otherwise.
    """
    # TODO: Implement real ed25519 verification using nacl / solders
    #   1. Decode wallet_address from base58 to get public key bytes
    #   2. Decode signature from base58
    #   3. Encode message to bytes
    #   4. Use nacl.signing.VerifyKey to verify
    logger.warning(
        "verify_solana_signature is a stub — returning True without real verification. "
        "wallet={wallet}, message_len={msg_len}",
        wallet=wallet_address,
        msg_len=len(message),
    )
    return True
