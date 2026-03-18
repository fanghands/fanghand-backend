"""Shared API dependencies: auth, rate limiting, role guards."""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db as _get_db
from app.models.builder import Builder
from app.models.user import User

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database session dependency."""
    async for session in _get_db():
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode JWT and return the authenticated user."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )
    token = credentials.credentials
    try:
        import jwt as pyjwt

        payload = pyjwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if user_id is None or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


async def require_builder(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Builder:
    """Ensure the current user is a registered builder."""
    if not user.is_builder:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Builder account required",
        )
    result = await db.execute(
        select(Builder).where(Builder.id == user.id)
    )
    builder = result.scalar_one_or_none()
    if builder is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Builder profile not found",
        )
    return builder


async def rate_limit(request: Request) -> None:
    """Redis-based rate limiting. Gracefully skips if Redis is unavailable."""
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}:{request.url.path}"
        current = await client.incr(key)
        if current == 1:
            await client.expire(key, 60)
        if current > 100:
            await client.close()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later.",
            )
        await client.close()
    except ImportError:
        logger.debug("redis package not installed, skipping rate limit")
    except HTTPException:
        raise
    except Exception:
        logger.debug("Redis unavailable, skipping rate limit")
