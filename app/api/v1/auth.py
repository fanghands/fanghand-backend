"""Authentication routes: wallet connect (SIWS), JWT refresh, profile."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.api.deps import get_current_user, get_db, rate_limit
from app.models.user import User
from app.schemas.auth import (
    TokenResponse,
    UserResponse,
    UserUpdate,
    WalletConnectRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# Extra request schema (not in shared schemas)
# ---------------------------------------------------------------------------


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

ACCESS_TOKEN_TTL = timedelta(hours=1)
REFRESH_TOKEN_TTL = timedelta(days=30)


def _create_token(user_id: str, token_type: str, ttl: timedelta) -> str:
    import jwt as pyjwt

    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": token_type,
        "iat": now,
        "exp": now + ttl,
    }
    return pyjwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _issue_tokens(user: User) -> TokenResponse:
    uid = str(user.id)
    return TokenResponse(
        access_token=_create_token(uid, "access", ACCESS_TOKEN_TTL),
        refresh_token=_create_token(uid, "refresh", REFRESH_TOKEN_TTL),
        user=UserResponse.model_validate(user),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/wallet-connect",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit)],
)
async def wallet_connect(
    body: WalletConnectRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate via Sign-In With Solana (SIWS)."""
    now_ts = int(datetime.now(timezone.utc).timestamp())
    if abs(now_ts - body.timestamp) > 60:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Timestamp expired or too far in the future",
        )

    # TODO: implement real ed25519 signature verification
    # from nacl.signing import VerifyKey
    # import base58
    # vk = VerifyKey(bytes(base58.b58decode(body.wallet_address)))
    # vk.verify(body.message.encode(), base58.b58decode(body.signature))

    result = await db.execute(
        select(User).where(User.wallet_address == body.wallet_address)
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            id=uuid.uuid4(),
            wallet_address=body.wallet_address,
        )
        db.add(user)
        await db.flush()

    return _issue_tokens(user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit)],
)
async def refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Exchange a valid refresh token for a new access token."""
    import jwt as pyjwt

    try:
        payload = pyjwt.decode(
            body.refresh_token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )
    except pyjwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
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
    return _issue_tokens(user)


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    """Return the current authenticated user profile."""
    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update the current user's profile fields."""
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No fields to update",
        )

    # Check username uniqueness
    if "username" in update_data and update_data["username"] is not None:
        existing = await db.execute(
            select(User).where(
                User.username == update_data["username"],
                User.id != user.id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )

    for field, value in update_data.items():
        setattr(user, field, value)
    await db.flush()
    await db.refresh(user)
    return UserResponse.model_validate(user)
