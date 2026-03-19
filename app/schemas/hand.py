import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, computed_field

from app.schemas.auth import UserResponse


class HandListItem(BaseModel):
    """Schema matching the frontend Hand type."""
    id: uuid.UUID
    slug: str
    name: str
    description: str
    emoji: Optional[str] = None
    badge: str = "OFFICIAL"
    category: List[str] = []
    features: List[str] = []
    author: str = ""
    author_verified: bool = True
    version: str = "0.1.0"
    activations: int = 0
    rating: float = 0
    reviews_count: int = 0
    price_monthly_cents: Optional[int] = None
    price_per_run_cents: Optional[int] = None
    toml_preview: str = ""
    system_prompt_preview: Optional[str] = None
    settings_schema: Optional[Dict[str, Any]] = None
    status: str = "active"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_hand(cls, hand) -> "HandListItem":
        """Map a Hand ORM model to the frontend-compatible schema."""
        badge = "OFFICIAL" if hand.type.value == "official" else "COMMUNITY"
        # Map category enum to list, add tags
        cats = [hand.category.value] + (hand.tags or [])
        # Map status
        status_map = {"live": "active", "draft": "pending", "review": "pending",
                       "approved": "pending", "deprecated": "deprecated",
                       "suspended": "deprecated"}
        fe_status = status_map.get(hand.status.value, "active")
        # Author name
        author_name = hand.author.username or hand.author.display_name or hand.author.wallet_address[:8] + "..." if hand.author else "unknown"

        return cls(
            id=hand.id,
            slug=hand.slug,
            name=hand.name,
            description=hand.description,
            emoji=hand.icon_emoji or "",
            badge=badge,
            category=cats,
            features=hand.tags or [],
            author=author_name,
            author_verified=hand.type.value == "official",
            version=hand.version,
            activations=hand.total_activations,
            rating=float(hand.avg_rating),
            reviews_count=hand.review_count,
            price_monthly_cents=hand.price_monthly_cents,
            price_per_run_cents=int(hand.price_quick_lamports / 10000) if hand.price_quick_lamports else None,
            toml_preview=hand.hand_toml_url or "",
            system_prompt_preview=hand.system_prompt_url,
            settings_schema=None,
            status=fe_status,
            created_at=hand.created_at,
            updated_at=hand.updated_at,
        )


class HandDetail(HandListItem):
    long_description: Optional[str] = None
    hand_toml_url: Optional[str] = None
    skill_md_url: Optional[str] = None
    system_prompt_url: Optional[str] = None
    changelog: List[Dict[str, Any]] = []
    published_at: Optional[datetime] = None

    @classmethod
    def from_hand(cls, hand) -> "HandDetail":
        base = HandListItem.from_hand(hand)
        return cls(
            **base.model_dump(),
            long_description=hand.long_description,
            hand_toml_url=hand.hand_toml_url,
            skill_md_url=hand.skill_md_url,
            system_prompt_url=hand.system_prompt_url,
            changelog=hand.changelog or [],
            published_at=hand.published_at,
        )


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
