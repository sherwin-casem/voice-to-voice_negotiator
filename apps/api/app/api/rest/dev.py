from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_interview_repository
from app.modules.interview.repository import InterviewRepository
from app.schemas.common import ApiResponse

dev_router = APIRouter(prefix="/dev", tags=["dev"])


class CreateDevUserRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class DevUserResponse(BaseModel):
    id: UUID
    email: str


@dev_router.post("/users", response_model=ApiResponse[DevUserResponse])
async def create_dev_user(
    body: CreateDevUserRequest,
    repository: InterviewRepository = Depends(get_interview_repository),
) -> ApiResponse[DevUserResponse]:
    """Create a user for local development until authentication is implemented."""
    user = await repository.create_user(email=body.email.lower())
    return ApiResponse(data=DevUserResponse(id=user.id, email=user.email))
