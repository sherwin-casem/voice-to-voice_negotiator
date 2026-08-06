from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.modules.auth.deps import get_user_id
from app.modules.progress.constants import DIMENSION_LABELS
from app.modules.progress.deps import get_progress_analysis_service
from app.modules.progress.service import ProgressAnalysisService
from app.schemas.common import ApiResponse
from app.schemas.progress import (
    DimensionTrendResponse,
    ProgressAnalysisResponse,
    RecurringWeaknessResponse,
)

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("", response_model=ApiResponse[ProgressAnalysisResponse])
async def get_progress_analysis(
    user_id: UUID = Depends(get_user_id),
    window: int = Query(default=5, ge=2, le=20),
    service: ProgressAnalysisService = Depends(get_progress_analysis_service),
) -> ApiResponse[ProgressAnalysisResponse]:
    analysis = await service.analyze_user(user_id, window=window)
    return ApiResponse(
        data=ProgressAnalysisResponse(
            user_id=analysis.user_id,
            sessions_analyzed=analysis.sessions_analyzed,
            window_size=analysis.window_size,
            dimension_trends=[
                DimensionTrendResponse(
                    dimension=trend.dimension,
                    label=DIMENSION_LABELS.get(trend.dimension, trend.dimension),
                    direction=trend.direction.value,
                    recent_average=trend.recent_average,
                    prior_average=trend.prior_average,
                    delta=trend.delta,
                    sessions_compared=trend.sessions_compared,
                    comparable_sessions=trend.comparable_sessions,
                )
                for trend in analysis.dimension_trends
            ],
            recurring_weaknesses=[
                RecurringWeaknessResponse(
                    pattern=item.pattern.value,
                    label=item.label,
                    occurrences=item.occurrences,
                    session_count=item.session_count,
                    frequency=item.frequency,
                    is_persistent=item.is_persistent,
                )
                for item in analysis.recurring_weaknesses
            ],
            improvements=analysis.improvements,
            persistent_weaknesses=analysis.persistent_weaknesses,
            narrative_summary=analysis.narrative_summary,
        )
    )
