"""Unit-of-work orchestrator wrapper for long-lived connections.

WebSocket connections outlive any single request, and background turn tasks
can run concurrently with the receive loop. SQLAlchemy ``AsyncSession`` is not
safe for concurrent use, so instead of sharing one request-scoped session for
the whole connection, every orchestrator operation here runs in its own
session/transaction.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.session import async_session_factory
from app.modules.context.deps import build_context_preparation_service
from app.modules.interview.interviewer_agent import InterviewerAgent
from app.modules.interview.orchestrator import (
    InterviewOrchestrator,
    QuestionResult,
    SubmitAnswerResult,
)
from app.modules.interview.repository import InterviewRepository
from app.modules.interview.schemas import QuestionRecord, SessionRecord


class SessionScopedOrchestrator:
    """Delegates to :class:`InterviewOrchestrator` with a fresh DB session per call."""

    def __init__(
        self,
        interviewer: InterviewerAgent,
        session_factory: async_sessionmaker | None = None,
    ) -> None:
        self._interviewer = interviewer
        self._session_factory = session_factory or async_session_factory

    @asynccontextmanager
    async def _scope(self) -> AsyncIterator[InterviewOrchestrator]:
        async with self._session_factory() as session:
            try:
                orchestrator = InterviewOrchestrator(
                    InterviewRepository(session),
                    self._interviewer,
                    build_context_preparation_service(session),
                )
                yield orchestrator
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def get_session(self, session_id: UUID, user_id: UUID) -> SessionRecord:
        async with self._scope() as orchestrator:
            return await orchestrator.get_session(session_id, user_id)

    async def get_current_question(
        self,
        session_id: UUID,
        user_id: UUID,
    ) -> tuple[QuestionRecord, bool] | None:
        async with self._scope() as orchestrator:
            return await orchestrator.get_current_question(session_id, user_id)

    async def start(self, session_id: UUID, user_id: UUID) -> QuestionResult:
        async with self._scope() as orchestrator:
            return await orchestrator.start(session_id, user_id)

    async def ask_next_question(self, session_id: UUID, user_id: UUID) -> QuestionResult:
        async with self._scope() as orchestrator:
            return await orchestrator.ask_next_question(session_id, user_id)

    async def submit_answer(
        self,
        session_id: UUID,
        user_id: UUID,
        question_id: UUID,
        *,
        answer_text: str,
        duration_ms: int | None = None,
    ) -> SubmitAnswerResult:
        async with self._scope() as orchestrator:
            return await orchestrator.submit_answer(
                session_id,
                user_id,
                question_id,
                answer_text=answer_text,
                duration_ms=duration_ms,
            )

    async def end_session(
        self,
        session_id: UUID,
        user_id: UUID,
        *,
        reason: str = "user_ended",
    ) -> SessionRecord:
        async with self._scope() as orchestrator:
            return await orchestrator.end_session(session_id, user_id, reason=reason)

    async def abandon_session(
        self,
        session_id: UUID,
        user_id: UUID,
        *,
        reason: str = "disconnect",
    ) -> SessionRecord:
        async with self._scope() as orchestrator:
            return await orchestrator.abandon_session(session_id, user_id, reason=reason)
