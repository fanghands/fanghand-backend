from loguru import logger

from app.workers.celery_app import celery


@celery.task(name='sync_fgh_balances', bind=True, max_retries=2, default_retry_delay=60)
def sync_fgh_balances(self):
    """Sync on-chain FGH token balances for all users."""
    logger.info("sync_fgh_balances called", attempt=self.request.retries)
    # TODO: Fetch all users with wallet addresses
    # TODO: Query Solana RPC for FGH token account balances
    # TODO: Update cached balances in DB
    logger.warning("sync_fgh_balances is a stub — no balances synced")
    return {"status": "stub", "synced": 0}


@celery.task(name='monitor_agent_health', bind=True, max_retries=1, default_retry_delay=30)
def monitor_agent_health(self):
    """Check health of all active agents via OpenFang API."""
    logger.info("monitor_agent_health called", attempt=self.request.retries)
    # TODO: Query all active activations from DB
    # TODO: Ping OpenFang API for each agent's status
    # TODO: Mark unhealthy agents, trigger alerts
    logger.warning("monitor_agent_health is a stub — no agents checked")
    return {"status": "stub", "checked": 0}


@celery.task(name='broadcast_burn', bind=True, max_retries=2, default_retry_delay=15)
def broadcast_burn(self, tx_signature: str, amount: int):
    """Announce a burn event (websocket / SSE broadcast)."""
    logger.info(
        "broadcast_burn called",
        tx_signature=tx_signature,
        amount=amount,
        attempt=self.request.retries,
    )
    # TODO: Push burn event to connected SSE/WebSocket clients
    # TODO: Update burn stats cache
    logger.warning("broadcast_burn is a stub — no broadcast sent")
    return {"status": "stub", "tx_signature": tx_signature, "amount": amount}
