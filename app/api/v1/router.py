"""V1 API router: aggregates all sub-routers."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.hands import router as hands_router
from app.api.v1.activations import router as activations_router
from app.api.v1.runs import router as runs_router
from app.api.v1.payments import router as payments_router
from app.api.v1.builders import router as builders_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.webhooks import router as webhooks_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(hands_router)
router.include_router(activations_router)
router.include_router(runs_router)
router.include_router(payments_router)
router.include_router(builders_router)
router.include_router(dashboard_router)
router.include_router(webhooks_router)
