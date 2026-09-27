from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: str = "ERROR"
    details: Optional[Any] = None


class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
