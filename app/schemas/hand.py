import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.auth import UserResponse


class HandListItem(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str
    type: str
    category: str
    icon_emoji: Optional[str] = None
    price_monthly_cents: Optional[int] = None
    price_quick_lamports: Optional[int] = None
    price_deep_lamports: Optional[int] = None
    total_activations: int = 0
    avg_rating: float = 0
    review_count: int = 0
    version: str = "0.1.0"
    author: UserResponse

    model_config = {"from_attributes": True}


class HandDetail(HandListItem):
    long_description: Optional[str] = None
    tags: List[str] = []
    features: List[str] = []
    hand_toml_url: Optional[str] = None
    skill_md_url: Optional[str] = None
    system_prompt_url: Optional[str] = None
    changelog: List[Dict[str, Any]] = []
    published_at: Optional[datetime] = None


class HandFilter(BaseModel):
    type: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    sort: Optional[str] = None
    search: Optional[str] = None
    cursor: Optional[str] = None
    limit: int = Field(20, ge=1, le=100)


class HandCreate(BaseModel):
    slug: str = Field(..., min_length=3, max_length=80)
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=10)
    long_description: Optional[str] = None
    category: str
    tags: List[str] = []
    price_monthly_cents: Optional[int] = None
    price_quick_lamports: Optional[int] = None
    price_deep_lamports: Optional[int] = None
    free_trial_runs: int = 0
    hand_toml_url: Optional[str] = None
    skill_md_url: Optional[str] = None
    system_prompt_url: Optional[str] = None
    icon_emoji: Optional[str] = None
    cover_image_url: Optional[str] = None
    demo_video_url: Optional[str] = None


class UserReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)


class UserReviewResponse(BaseModel):
    id: uuid.UUID
    user_address: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
