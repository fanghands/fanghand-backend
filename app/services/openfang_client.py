import asyncio
import uuid
from typing import AsyncGenerator

import httpx
from loguru import logger

from app.config import settings


class OpenFangClient:
    """REST + SSE client for the OpenFang daemon."""

    BASE = settings.OPENFANG_API_URL
    TIMEOUT = httpx.Timeout(30.0, connect=5.0)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {settings.OPENFANG_API_KEY}",
            "Content-Type": "application/json",
        }

    async def health_check(self) -> bool:
        """Check if OpenFang daemon is reachable."""
        # TODO: real health check via GET /v1/health
        logger.debug("OpenFang health_check (stub): returning True")
        return True

    async def spawn_hand(self, hand_slug: str, config: dict, delivery: dict) -> str:
        """Activate a Hand in OpenFang. Returns agent_id."""
        # TODO: POST to OpenFang /v1/hands/activate
        agent_id = f"agent-{uuid.uuid4().hex[:12]}"
        logger.info(
            "OpenFang spawn_hand (stub): slug={} -> agent_id={}",
            hand_slug,
            agent_id,
        )
        return agent_id

    async def pause_hand(self, agent_id: str) -> None:
        """Pause an active agent."""
        # TODO: POST /v1/agents/{agent_id}/pause
        logger.info("OpenFang pause_hand (stub): agent_id={}", agent_id)

    async def resume_hand(self, agent_id: str) -> None:
        """Resume a paused agent."""
        # TODO: POST /v1/agents/{agent_id}/resume
        logger.info("OpenFang resume_hand (stub): agent_id={}", agent_id)

    async def delete_agent(self, agent_id: str) -> None:
        """Delete/deactivate an agent."""
        # TODO: DELETE /v1/agents/{agent_id}
        logger.info("OpenFang delete_agent (stub): agent_id={}", agent_id)

    async def trigger_run(self, agent_id: str, tier: str, config: dict) -> str:
        """Trigger a manual run. Returns run_id."""
        # TODO: POST /v1/agents/{agent_id}/run
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        logger.info(
            "OpenFang trigger_run (stub): agent_id={}, tier={} -> run_id={}",
            agent_id,
            tier,
            run_id,
        )
        return run_id

    async def get_agent_status(self, agent_id: str) -> dict:
        """Get current agent status."""
        # TODO: GET /v1/agents/{agent_id}/status
        return {"status": "running", "uptime_seconds": 86400, "last_run": None}

    async def get_agent_metrics(self, agent_id: str) -> dict:
        """Get agent metrics for dashboard."""
        # TODO: GET /v1/agents/{agent_id}/metrics
        return {"total_runs": 0, "success_rate": 1.0, "avg_duration_ms": 5000}

    async def stream_run_output(self, run_id: str) -> AsyncGenerator[dict, None]:
        """SSE stream of run output from OpenFang."""
        # TODO: GET /v1/runs/{run_id}/stream with SSE
        mock_lines = [
            {"type": "output_chunk", "content": f"> initializing run {run_id}...\n"},
            {"type": "output_chunk", "content": "> processing data...\n"},
            {"type": "output_chunk", "content": "> generating output...\n"},
            {"type": "output_chunk", "content": "> analysis complete.\n"},
            {"type": "completed", "token_count": 1500, "duration_ms": 4200},
        ]
        for line in mock_lines:
            await asyncio.sleep(0.5)
            yield line

    async def stream_agent_status(self, agent_id: str) -> AsyncGenerator[dict, None]:
        """SSE stream of agent status events."""
        # TODO: GET /v1/agents/{agent_id}/status/stream with SSE
        while True:
            yield {
                "status": "running",
                "uptime_seconds": 86400,
                "timestamp": "2026-03-18T00:00:00Z",
            }
            await asyncio.sleep(5)


openfang_client = OpenFangClient()
