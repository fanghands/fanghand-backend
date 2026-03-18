from loguru import logger

from app.workers.celery_app import celery


@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def activate_hand(self, activation_id: str):
    """Ensure OpenFang agent is running for the given activation."""
    logger.info(
        "activate_hand called",
        activation_id=activation_id,
        attempt=self.request.retries,
    )
    # TODO: Call OpenFang API to start agent container
    # TODO: Update activation status in DB
    logger.warning("activate_hand is a stub — no real activation performed")
    return {"status": "stub", "activation_id": activation_id}


@celery.task(bind=True, max_retries=3, default_retry_delay=15)
def trigger_run(self, run_id: str):
    """Execute a pay-per-run invocation and update status."""
    logger.info(
        "trigger_run called",
        run_id=run_id,
        attempt=self.request.retries,
    )
    # TODO: Send run request to OpenFang agent
    # TODO: Deduct credits / record payment
    # TODO: Update run status (pending -> running -> completed/failed)
    logger.warning("trigger_run is a stub — no real run executed")
    return {"status": "stub", "run_id": run_id}
