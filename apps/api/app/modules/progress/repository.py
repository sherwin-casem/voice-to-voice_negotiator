import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import InterviewType
from app.db.models.progress import UserProgressSnapshot
from app.modules.progress.constants import WeaknessPattern
from app.modules.progress.schemas import SessionProgressRecord

PROGRESS_META_KEY = "_progress_meta"


class ProgressRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_snapshots(
        self,
        user_id: UUID,
        *,
        limit: int = 20,
    ) -> list[SessionProgressRecord]:
        result = await self._session.execute(
            select(UserProgressSnapshot)
            .where(UserProgressSnapshot.user_id == user_id)
            .order_by(UserProgressSnapshot.recorded_at.desc())
            .limit(limit)
        )
        snapshots = list(result.scalars())
        snapshots.reverse()
        return [_to_record(snapshot) for snapshot in snapshots]

    async def count_completed_sessions(self, user_id: UUID) -> int:
        result = await self._session.execute(
            select(UserProgressSnapshot.id).where(UserProgressSnapshot.user_id == user_id)
        )
        return len(result.scalars().all())

    async def create_snapshot(
        self,
        record: SessionProgressRecord,
        *,
        evaluation_run_id: UUID,
    ) -> UserProgressSnapshot:
        sessions_completed = await self.count_completed_sessions(record.user_id) + 1
        dimension_payload = _serialize_dimension_scores(record)
        snapshot = UserProgressSnapshot(
            id=uuid.uuid4(),
            user_id=record.user_id,
            session_id=record.session_id,
            evaluation_run_id=evaluation_run_id,
            interview_type=record.interview_type,
            overall_score=Decimal(str(round(record.overall_score, 2))),
            dimension_scores=dimension_payload,
            sessions_completed_count=sessions_completed,
            recorded_at=record.recorded_at,
        )
        self._session.add(snapshot)
        await self._session.flush()
        return snapshot


def _serialize_dimension_scores(record: SessionProgressRecord) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in record.dimension_scores.items():
        if value is not None:
            payload[key] = round(value, 1)
    payload[PROGRESS_META_KEY] = {
        "difficulty": record.difficulty,
        "interview_type": record.interview_type.value,
        "pattern_signals": [signal.value for signal in record.pattern_signals],
    }
    return payload


def _to_record(snapshot: UserProgressSnapshot) -> SessionProgressRecord:
    raw_scores = dict(snapshot.dimension_scores or {})
    meta = raw_scores.pop(PROGRESS_META_KEY, {})
    difficulty = meta.get("difficulty", "mid")
    pattern_values = meta.get("pattern_signals", [])
    pattern_signals = tuple(
        WeaknessPattern(value) for value in pattern_values if value in WeaknessPattern._value2member_map_
    )

    dimension_scores: dict[str, float | None] = {}
    for key, value in raw_scores.items():
        dimension_scores[key] = float(value) if value is not None else None

    return SessionProgressRecord(
        session_id=snapshot.session_id,
        user_id=snapshot.user_id,
        interview_type=snapshot.interview_type,
        difficulty=difficulty,
        recorded_at=snapshot.recorded_at,
        overall_score=float(snapshot.overall_score),
        dimension_scores=dimension_scores,
        pattern_signals=pattern_signals,
    )
