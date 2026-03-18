import pytest


@pytest.mark.asyncio
async def test_burns_is_public(async_client):
    response = await async_client.get("/api/v1/payments/burns")
    # Public endpoint, should not return 401
    assert response.status_code != 401


@pytest.mark.asyncio
async def test_burn_stats_is_public(async_client):
    response = await async_client.get("/api/v1/payments/burns/stats")
    assert response.status_code != 401


@pytest.mark.asyncio
async def test_credit_balance_requires_auth(async_client):
    response = await async_client.get("/api/v1/payments/credit/balance")
    assert response.status_code == 401
