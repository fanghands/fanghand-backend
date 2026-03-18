import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class ActivationCreate(BaseModel):
    hand_id: uuid.UUID
    config: Dict[str, Any] = {}
    delivery_channel: str = "dashboard"
    delivery_target: Optional[str] = None
    payment_currency: str = "usd"
    payment_method: Optional[str] = None
    stripe_payment_method_id: Optional[str] = None
    solana_tx_signature: Optional[str] = None
    discount_applied_pct: Optional[int] = 0


class ActivationResponse(BaseModel):
    id: uuid.UUID
    hand_id: uuid.UUID
    hand_name: str
    status: str
    config: Dict[str, Any] = {}
    delivery_channel: str
    openfang_agent_id: Optional[str] = None
    payment_currency: str
    discount_pct: int = 0
    activated_at: datetime
    paused_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivationConfigUpdate(BaseModel):
    config: Dict[str, Any]


class StatusEvent(BaseModel):
    status: str
    message: str
    timestamp: datetime
