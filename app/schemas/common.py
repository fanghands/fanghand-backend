from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class CursorPage(BaseModel, Generic[T]):
    data: List[T]
    next_cursor: Optional[str] = None
    total: int = 0


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
    timestamp: datetime = datetime.utcnow()

    model_config = {"json_schema_extra": {"example": {"detail": "Not found", "code": "NOT_FOUND"}}}
