import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class WalletConnectRequest(BaseModel):
    wallet_address: str = Field(..., min_length=32, max_length=44)
    signature: str
    message: str
    timestamp: int


class UserResponse(BaseModel):
    id: uuid.UUID
    username: Optional[str] = None
    display_name: Optional[str] = None
    wallet_address: str
    is_builder: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
