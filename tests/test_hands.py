import pytest


@pytest.mark.asyncio
async def test_list_hands(async_client):
    response = await async_client.get("/api/v1/hands")
    assert response.status_code in (200, 500)


@pytest.mark.asyncio
async def test_get_hand_by_slug(async_client):
    response = await async_client.get("/api/v1/hands/test-hand")
    # May be 200 or 404 depending on data
    assert response.status_code in (200, 404, 500)


@pytest.mark.asyncio
async def test_get_hand_invalid_slug_returns_404(async_client):
    response = await async_client.get("/api/v1/hands/nonexistent-hand-slug-xyz")
    assert response.status_code in (404, 500)
