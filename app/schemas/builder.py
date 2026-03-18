import uuid
from typing import List, Optional

from pydantic import BaseModel, Field


class BuilderRegister(BaseModel):
    bio: Optional[str] = Field(None, max_length=500)
    twitter_handle: Optional[str] = Field(None, max_length=50)
    github_handle: Optional[str] = Field(None, max_length=50)
    payout_usdc_address: Optional[str] = Field(None, max_length=44)


class HandSubmit(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=10)
    category: str
    price_monthly_cents: Optional[int] = None
    hand_toml: str
    skill_md: Optional[str] = None
    system_prompt: Optional[str] = None
    icon_emoji: Optional[str] = None


class BuilderResponse(BaseModel):
    id: uuid.UUID
    bio: Optional[str] = None
    tier: str
    is_verified: bool = False
    total_hands: int = 0
    total_activations: int = 0
    total_revenue_cents: int = 0
    revenue_share_pct: int = 80

    model_config = {"from_attributes": True}


class MonthlyEarning(BaseModel):
    month: str
    amount_cents: int


class EarningsResponse(BaseModel):
    total_cents: int
    pending_cents: int
    paid_cents: int
    monthly: List[MonthlyEarning] = []
