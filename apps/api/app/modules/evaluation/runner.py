"""Background execution of session-scope evaluations.

Triggered when an interview session transitions ACTIVE -> COMPLETING. Runs the
multi-agent evaluation outside the request/WebSocket lifecycle, persists the
results, records a progress snapshot, and finalizes the session status
(COMPLETED or EVALUATION_FAILED).
"""

import asyncio
import logging
from dataclasses import dataclass
from uuid import UUID

from app.config import settings
from app.db.enums import EvaluationRunStatus, EvaluationScope, InterviewSessionStatus
from app.db.models.interview import InterviewSession
from app.db.session import async_session_factory
from app.modules.context.deps import build_context_preparation_service
from app.modules.evaluation.factory import build_evaluation_service
from app.modules.evaluation.repository import EvaluationRepository
from app.modules.evaluation.schemas import ConversationTurn, EvaluationContext
from app.modules.evaluation.service import ORCHESTRATION_VERSION
from app.modules.interview.repository import InterviewRepository
from app.modules.progress.repository import ProgressRepository
from app.modules.progress.schemas import AnswerMetrics
from app.modules.progress.service import ProgressAnalysisService

logger = logging.getLogger(__name__)

_background_tasks: set[asyncio.Task] = set()


def schedule_session_evaluation(session_id: UUID, user_id: UUID) -> None:
    """Fire-and-forget evaluation of a session that just entered COMPLETING."""
    task = asyncio.create_task(
        run_session_evaluation(session_id, user_id),
        name=f"session-evaluation-{session_id}",
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


@dataclass(frozen=True)
class _PreparedEvaluation:
    run_id: UUID
    context: EvaluationContext
    answer_metrics: list[AnswerMetrics]
    end_reason: str | None


async def run_session_evaluation(
    session_id: UUID,
    user_id: UUID,
    *,
    trigger: str = "session_end",
) -> None:
    log_extra = {"component": "evaluation_runner", "session_id": str(session_id)}
    run_id: UUID | None = None
    try:
        prepared = await _prepare(session_id, user_id, trigger)
        if prepared is None:
            return
        run_id = prepared.run_id
        log_extra["evaluation_run_id"] = str(run_id)

        service = build_evaluation_service()
        result = await asyncio.wait_for(
            service.evaluate(prepared.context),
            timeout=settings.evaluation_timeout_seconds,
        )

        await _finalize(session_id, user_id, prepared, result)
        logger.info("Session evaluation finished", extra=log_extra)
    except Exception as exc:  # noqa: BLE001 - background task boundary
        logger.exception("Session evaluation failed", extra=log_extra)
        await _mark_failed(session_id, user_id, run_id, str(exc))


async def _prepare(
    session_id: UUID,
    user_id: UUID,
    trigger: str,
) -> _PreparedEvaluation | None:
    """Validate state, create the RUNNING run row, and build the evaluation input.

    Uses a short-lived DB session so no connection is held during LLM calls.
    """
    async with async_session_factory() as db:
        try:
            interview_repository = InterviewRepository(db)
            evaluation_repository = EvaluationRepository(db)

            interview_session = await interview_repository.get_session_for_user(
                session_id, user_id
            )
            if interview_session.status != InterviewSessionStatus.COMPLETING:
                logger.info(
                    "Skipping evaluation: session not in completing state",
                    extra={
                        "component": "evaluation_runner",
                        "session_id": str(session_id),
                        "status": interview_session.status.value,
                    },
                )
                return None

            existing = await evaluation_repository.get_latest_session_run(session_id)
            if existing is not None and existing.status in {
                EvaluationRunStatus.RUNNING,
                EvaluationRunStatus.COMPLETED,
            }:
                return None

            answered = _answered_questions(interview_session)
            if not answered:
                # Nothing to evaluate; complete the session directly.
                await interview_repository.update_session_status(
                    interview_session,
                    InterviewSessionStatus.COMPLETED,
                    end_reason=interview_session.end_reason,
                )
                await db.commit()
                return None

            run = await evaluation_repository.create_run(
                session_id,
                scope=EvaluationScope.SESSION,
                trigger=trigger,
                orchestration_version=ORCHESTRATION_VERSION,
            )
            context = _build_session_context(db, interview_session, answered)
            answer_metrics = [
                AnswerMetrics(
                    answer_text=question.answer.answer_text,
                    word_count=question.answer.word_count,
                    duration_ms=question.answer.duration_ms,
                    topic_tag=question.topic_tag,
                )
                for question in answered
            ]
            prepared = _PreparedEvaluation(
                run_id=run.id,
                context=context,
                answer_metrics=answer_metrics,
                end_reason=interview_session.end_reason,
            )
            await db.commit()
            return prepared
        except Exception:
            await db.rollback()
            raise


def _answered_questions(interview_session: InterviewSession) -> list:
    return [
        question
        for question in sorted(interview_session.questions, key=lambda q: q.sequence_num)
        if question.answer is not None
    ]


def _build_session_context(
    db,
    interview_session: InterviewSession,
    answered: list,
) -> EvaluationContext:
    context_service = build_context_preparation_service(db)
    last = answered[-1]
    prior_turns = [
        ConversationTurn(
            sequence_num=question.sequence_num,
            question_text=question.question_text,
            answer_text=question.answer.answer_text,
            topic_tag=question.topic_tag,
        )
        for question in answered[:-1]
    ]
    return context_service.build_evaluation_context(
        interview_session,
        question_text=last.question_text,
        answer_text=last.answer.answer_text,
        topic_tag=last.topic_tag,
        prior_turns=prior_turns,
        scope=EvaluationScope.SESSION,
    )


async def _finalize(
    session_id: UUID,
    user_id: UUID,
    prepared: _PreparedEvaluation,
    result,
) -> None:
    async with async_session_factory() as db:
        try:
            interview_repository = InterviewRepository(db)
            evaluation_repository = EvaluationRepository(db)

            await evaluation_repository.persist_run_result(
                prepared.run_id, session_id, result
            )

            interview_session = await interview_repository.get_session_for_user(
                session_id, user_id
            )

            evaluation_succeeded = result.status == EvaluationRunStatus.COMPLETED
            if evaluation_succeeded:
                await _record_progress_snapshot(
                    db, interview_session, prepared, result, user_id
                )

            if interview_session.status == InterviewSessionStatus.COMPLETING:
                await interview_repository.update_session_status(
                    interview_session,
                    (
                        InterviewSessionStatus.COMPLETED
                        if evaluation_succeeded
                        else InterviewSessionStatus.EVALUATION_FAILED
                    ),
                    end_reason=prepared.end_reason,
                )
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def _record_progress_snapshot(
    db,
    interview_session: InterviewSession,
    prepared: _PreparedEvaluation,
    result,
    user_id: UUID,
) -> None:
    progress_service = ProgressAnalysisService(ProgressRepository(db))
    record = progress_service.build_record_from_evaluation(
        session_id=interview_session.id,
        user_id=user_id,
        interview_type=interview_session.interview_type,
        difficulty=str(interview_session.config_snapshot.get("difficulty", "mid")),
        evaluation_result=result,
        answer_metrics=prepared.answer_metrics,
    )
    if record is not None:
        await progress_service.record_session_progress(
            record, evaluation_run_id=prepared.run_id
        )


async def _mark_failed(
    session_id: UUID,
    user_id: UUID,
    run_id: UUID | None,
    error_message: str,
) -> None:
    try:
        async with async_session_factory() as db:
            interview_repository = InterviewRepository(db)
            evaluation_repository = EvaluationRepository(db)

            if run_id is not None:
                await evaluation_repository.mark_run_failed(run_id, error_message)

            interview_session = await interview_repository.get_session_for_user(
                session_id, user_id
            )
            if interview_session.status == InterviewSessionStatus.COMPLETING:
                await interview_repository.update_session_status(
                    interview_session,
                    InterviewSessionStatus.EVALUATION_FAILED,
                    end_reason=interview_session.end_reason,
                )
            await db.commit()
    except Exception:  # noqa: BLE001 - last-resort error path
        logger.exception(
            "Could not mark evaluation as failed",
            extra={"component": "evaluation_runner", "session_id": str(session_id)},
        )
