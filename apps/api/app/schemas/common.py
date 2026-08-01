from typing import Generic, Literal, TypeVar

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
    status: Literal["ok", "degraded"] = Field(examples=["ok"])
    database: Literal["ok", "error"] = Field(examples=["ok"])
