import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CheckoutCreate(BaseModel):
    hand_id: uuid.UUID
    price_id: str
    success_url: str
    cancel_url: str
    config: Dict[str, Any] = {}
    delivery_channel: Optional[str] = "dashboard"
    delivery_target: Optional[str] = None


class CreditDeposit(BaseModel):
    tx_signature: str
    lamports: int


class CreditBalanceResponse(BaseModel):
    lamports: int
    usd_equivalent: float


class PaymentHistoryItem(BaseModel):
    id: uuid.UUID
    type: str
    status: str
    currency: str
    amount_cents: Optional[int] = None
    amount_lamports: Optional[int] = None
    hand_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BurnEvent(BaseModel):
    id: uuid.UUID
    fgh_burned: int
    tx_signature: str
    trigger_type: str
    burned_at: datetime

    model_config = {"from_attributes": True}


class BurnStats(BaseModel):
    total_burned: int
    total_events: int
    last_burn_at: Optional[datetime] = None
