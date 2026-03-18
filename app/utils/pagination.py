from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Generic, List, Optional, Sequence, TypeVar

from loguru import logger
from sqlalchemy import select, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


@dataclass
class PaginatedResponse(Generic[T]):
    items: List[T] = field(default_factory=list)
    next_cursor: Optional[str] = None
    has_more: bool = False


class CursorPaginator:
    """Cursor-based paginator using UUID cursors."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def paginate(
        self,
        query,
        cursor: Optional[str] = None,
        limit: int = 20,
        order_by: str = "id",
        descending: bool = True,
    ) -> PaginatedResponse:
        """Execute a paginated query using UUID cursor.

        Args:
            query: SQLAlchemy select statement.
            cursor: UUID string of the last item from the previous page.
            limit: Maximum number of items to return (capped at 100).
            order_by: Column name to order by.
            descending: Whether to sort descending (newest first).

        Returns:
            PaginatedResponse with items, next_cursor, and has_more flag.
        """
        from app.utils.constants import MAX_PAGE_SIZE

        limit = min(limit, MAX_PAGE_SIZE)

        # Determine the model from the query columns
        entity = query.column_descriptions[0]["entity"]
        order_col = getattr(entity, order_by, None)

        if order_col is None:
            logger.error("Invalid order_by column: {}", order_by)
            return PaginatedResponse()

        direction = desc if descending else asc

        if cursor:
            try:
                cursor_uuid = uuid.UUID(cursor)
            except ValueError:
                logger.warning("Invalid cursor UUID: {}", cursor)
                return PaginatedResponse()

            if descending:
                query = query.where(order_col < cursor_uuid)
            else:
                query = query.where(order_col > cursor_uuid)

        query = query.order_by(direction(order_col)).limit(limit + 1)

        result = await self.session.execute(query)
        rows = list(result.scalars().all())

        has_more = len(rows) > limit
        items = rows[:limit]

        next_cursor = None
        if has_more and items:
            last = items[-1]
            next_cursor = str(getattr(last, order_by))

        return PaginatedResponse(items=items, next_cursor=next_cursor, has_more=has_more)
