import pytest


@pytest.mark.asyncio
async def test_create_activation_requires_auth(async_client):
    response = await async_client.post("/api/v1/activations", json={})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_activations_requires_auth(async_client):
    response = await async_client.get("/api/v1/activations")
    assert response.status_code == 401
