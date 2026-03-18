import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt

from app.config import settings


@pytest.fixture
def mock_user():
    """A fake user object for testing."""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.wallet_address = "FakeWa11etAddress111111111111111111111111111"
    user.username = "testuser"
    user.role = "user"
    return user


@pytest.fixture
def mock_builder(mock_user):
    """A fake builder object for testing."""
    builder = MagicMock()
    builder.id = uuid.uuid4()
    builder.user_id = mock_user.id
    builder.display_name = "Test Builder"
    builder.verified = True
    builder.role = "builder"
    return builder


@pytest.fixture
def auth_token(mock_user):
    """Generate a valid JWT for the mock user."""
    payload = {
        "sub": str(mock_user.id),
        "wallet": mock_user.wallet_address,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


@pytest.fixture
def auth_headers(auth_token):
    """Authorization headers with a valid Bearer token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest_asyncio.fixture
async def async_client():
    """HTTPX async client wired to the FastAPI app."""
    # Lazy import so tests can patch before app loads
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_db():
    """A mock async database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    return session
