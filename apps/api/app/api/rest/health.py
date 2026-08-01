from fastapi import APIRouter

from app.schemas.common import ApiResponse, HealthData

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse[HealthData])
async def health_check() -> ApiResponse[HealthData]:
    return ApiResponse(data=HealthData(status="ok"))
