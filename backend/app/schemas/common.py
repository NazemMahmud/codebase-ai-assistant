from typing import Generic, Optional, TypeVar

from fastapi import status
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: str = ""
    data: Optional[T] = None
    statusCode: Optional[int] = status.HTTP_200_OK
