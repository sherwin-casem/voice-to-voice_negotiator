from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiError(BaseModel):
    code: str
    message: str
    request_id: str | None = None


class ApiResponse(BaseModel, Generic[T]):
    data: T | None = None
    error: ApiError | None = None


class HealthData(BaseModel):
    status: str = Field(examples=["ok"])
