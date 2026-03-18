import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class RunCreate(BaseModel):
    hand_id: uuid.UUID
    tier: str = "quick"
    config: Dict[str, Any] = {}
    delivery_channel: Optional[str] = "dashboard"
    delivery_target: Optional[str] = None
    payment_method: str = "credits"
    solana_tx_signature: Optional[str] = None


class RunResponse(BaseModel):
    id: uuid.UUID
    hand_name: str
    status: str
    tier: str
    output_preview: Optional[str] = None
    token_count: Optional[int] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    lamports_charged: Optional[int] = None
    queued_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RunOutput(BaseModel):
    type: str
    content: str
    timestamp: datetime
