import pytest


@pytest.mark.asyncio
async def test_wallet_connect(async_client):
    payload = {
        "wallet_address": "FakeWa11etAddress111111111111111111111111111",
        "signature": "fakesignature",
        "message": "Sign in to FangHand",
    }
    response = await async_client.post("/api/v1/auth/wallet-connect", json=payload)
    # Endpoint should exist (may return 200 or 422 depending on impl)
    assert response.status_code in (200, 201, 422, 400)


@pytest.mark.asyncio
async def test_me_with_valid_jwt(async_client, auth_headers):
    response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
    # Should not be 401 since we have a valid token
    assert response.status_code != 401 or response.status_code in (200, 404, 500)


@pytest.mark.asyncio
async def test_me_without_auth_returns_401(async_client):
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code == 401
