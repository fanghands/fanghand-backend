import pytest


@pytest.mark.asyncio
async def test_create_run_requires_auth(async_client):
    response = await async_client.post("/api/v1/runs", json={})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_run_history_requires_auth(async_client):
    response = await async_client.get("/api/v1/runs/history")
    assert response.status_code == 401
