import pytest


@pytest.mark.asyncio
async def test_register_builder_requires_auth(async_client):
    response = await async_client.post("/api/v1/builders/register", json={})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_builder_me_requires_auth(async_client):
    response = await async_client.get("/api/v1/builders/me")
    assert response.status_code == 401
