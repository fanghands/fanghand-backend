from loguru import logger

from app.workers.celery_app import celery


@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def execute_fgh_burn(self, payment_id: str, fgh_amount: int, trigger_type: str):
    """Execute an FGH token burn on Solana."""
    logger.info(
        "execute_fgh_burn called",
        payment_id=payment_id,
        fgh_amount=fgh_amount,
        trigger_type=trigger_type,
        attempt=self.request.retries,
    )
    # TODO: Load platform burn keypair
    # TODO: Build and send Solana burn transaction
    # TODO: Record tx_signature in fgh_burns table
    logger.warning("execute_fgh_burn is a stub — no real burn executed")
    return {"status": "stub", "payment_id": payment_id, "fgh_amount": fgh_amount}


@celery.task(bind=True, max_retries=2, default_retry_delay=60)
def batch_burn(self):
    """Process all pending FGH burns in a single batch."""
    logger.info("batch_burn called", attempt=self.request.retries)
    # TODO: Query pending burns from DB
    # TODO: Aggregate and execute burns
    # TODO: Update burn records with tx signatures
    logger.warning("batch_burn is a stub — no pending burns processed")
    return {"status": "stub", "burned": 0}
