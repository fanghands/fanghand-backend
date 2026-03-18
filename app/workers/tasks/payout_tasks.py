from loguru import logger

from app.workers.celery_app import celery


@celery.task(bind=True, max_retries=2, default_retry_delay=120)
def process_monthly_payouts(self):
    """Calculate and dispatch monthly builder payouts."""
    logger.info("process_monthly_payouts called", attempt=self.request.retries)
    # TODO: Query all builders with pending revenue shares
    # TODO: Calculate payout amounts (BUILDER_SHARE_PCT of revenue)
    # TODO: Dispatch individual send_builder_payout tasks
    logger.warning("process_monthly_payouts is a stub — no payouts processed")
    return {"status": "stub", "payouts_dispatched": 0}


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def send_builder_payout(self, builder_id: str, amount_cents: int):
    """Send payout to an individual builder via Stripe Connect or Solana."""
    logger.info(
        "send_builder_payout called",
        builder_id=builder_id,
        amount_cents=amount_cents,
        attempt=self.request.retries,
    )
    # TODO: Determine payout method (Stripe Connect / SOL / USDC)
    # TODO: Execute transfer
    # TODO: Record payout in DB
    logger.warning("send_builder_payout is a stub — no payout sent")
    return {"status": "stub", "builder_id": builder_id, "amount_cents": amount_cents}
