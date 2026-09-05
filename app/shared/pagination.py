from typing import Generic, Sequence, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic pagination response wrapper."""
    items: Sequence[T]
    total: int
    skip: int
    limit: int
