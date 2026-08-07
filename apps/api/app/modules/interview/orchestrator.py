from dataclasses import dataclass
from uuid import UUID

from app.ai.schemas.interviewer import InterviewerContext, PriorTurn
from app.core.exceptions import (
    ConflictError,
    InvalidStateError,
    MaxQuestionsReachedError,
    NotFoundError,
)
from app.db.enums import InterviewSessionStatus
from app.db.models.interview import InterviewSession
from app.modules.interview.interviewer_agent import InterviewerAgent
from app.modules.interview.repository import InterviewRepository
from app.modules.interview.schemas import (
    AnswerRecord,
    QuestionRecord,
    SessionConfigInput,
    SessionRecord,
)
from app.modules.interview.state_machine import assert_transition, is_terminal
from app.modules.interview.validators import normalize_question_output
from app.modules.context.service import ContextPreparationService


@dataclass(frozen=True)
class QuestionResult:
    session: SessionRecord
    question: QuestionRecord
    should_end_session: bool


@dataclass(frozen=True)
class SubmitAnswerResult:
    session: SessionRecord
    answer: AnswerRecord


class InterviewOrchestrator:
    def __init__(
        self,
        repository: InterviewRepository,
        interviewer: InterviewerAgent,
        context_preparation: ContextPreparationService | None = None,
    ) -> None:
        self._repository = repository
        self._interviewer = interviewer
        self._context_preparation = context_preparation

    async def create_session(self, user_id: UUID, title: str | None = None) -> SessionRecord:
        return await self._repository.create_session(user_id, title=title)

    async def configure_session(
        self,
        session_id: UUID,
        user_id: UUID,
        config: SessionConfigInput,
    ) -> SessionRecord:
        interview_session = await self._repository.get_session_for_user(session_id, user_id)
        self._ensure_status(interview_session, {InterviewSessionStatus.CREATED})
        assert_transition(interview_session.status, InterviewSessionStatus.CONFIGURED)
        session = await self._repository.configure_session(session_id, user_id, config)
        if self._context_preparation is not None:
            loaded = await self._repository.get_session_for_user(session_id, user_id)
            await self._context_preparation.ensure_session_documents_prepared(loaded, user_id)
        return session

    async def start(self, session_id: UUID, user_id: UUID) -> QuestionResult:
        interview_session = await self._repository.get_session_for_user(session_id, user_id)
        self._ensure_status(interview_session, {InterviewSessionStatus.CONFIGURED})
        assert_transition(interview_session.status, InterviewSessionStatus.ACTIVE)
        await self._repository.update_session_status(interview_session, InterviewSessionStatus.ACTIVE)
        return await self._ask_next_question(interview_session)

    async def ask_next_question(self, session_id: UUID, user_id: UUID) -> QuestionResult:
        interview_session = await self._repository.get_session_for_user(session_id, user_id)
        self._ensure_status(interview_session, {InterviewSessionStatus.ACTIVE})
        await self._ensure_ready_for_next_question(interview_session)
        return await self._ask_next_question(interview_session)

    async def submit_answer(
        self,
        session_id: UUID,
        user_id: UUID,
        question_id: UUID,
        *,
        answer_text: str,
        duration_ms: int | None = None,
    ) -> SubmitAnswerResult:
        interview_session = await self._repository.get_session_for_user(session_id, user_id)
        self._ensure_status(interview_session, {InterviewSessionStatus.ACTIVE})

        latest = await self._repository.get_latest_question(interview_session)
        if latest is None or latest.id != question_id:
            raise NotFoundError("Question not found or not the current question")
        if latest.answer is not None:
            raise ConflictError("This question already has an answer")

        answer = await self._repository.add_answer(
            interview_session,
            question_id,
            answer_text=answer_text.strip(),
            duration_ms=duration_ms,
        )
        session = InterviewRepository.to_session_record(interview_session)
        return SubmitAnswerResult(session=session, answer=answer)

    async def end_session(
        self,
        session_id: UUID,
        user_id: UUID,
        *,
        reason: str = "user_ended",
    ) -> SessionRecord:
        interview_session = await self._repository.get_session_for_user(session_id, user_id)
        self._ensure_status(
            interview_session,
            {
                InterviewSessionStatus.ACTIVE,
                InterviewSessionStatus.CONFIGURED,
                InterviewSessionStatus.COMPLETING,
            },
        )

        if interview_session.status == InterviewSessionStatus.CONFIGURED:
            return await self._repository.update_session_status(
                interview_session,
                InterviewSessionStatus.ABANDONED,
                end_reason=reason,
            )

        if interview_session.status == InterviewSessionStatus.COMPLETING:
            # Evaluation already in flight; don't race it to COMPLETED.
            return InterviewRepository.to_session_record(interview_session)

        has_answers = any(
            question.answer is not None for question in interview_session.questions
        )
        if not has_answers:
            # Nothing to evaluate: complete directly.
            assert_transition(interview_session.status, InterviewSessionStatus.COMPLETED)
            return await self._repository.update_session_status(
                interview_session,
                InterviewSessionStatus.COMPLETED,
                end_reason=reason,
            )

        # Hand off to the evaluation pipeline; the background runner moves the
        # session to COMPLETED or EVALUATION_FAILED.
        assert_transition(interview_session.status, InterviewSessionStatus.COMPLETING)
        return await self._repository.update_session_status(
            interview_session,
            InterviewSessionStatus.COMPLETING,
            end_reason=reason,
        )

    async def abandon_session(
        self,
        session_id: UUID,
        user_id: UUID,
        *,
        reason: str = "disconnect",
    ) -> SessionRecord:
        interview_session = await self._repository.get_session_for_user(session_id, user_id)
        if interview_session.status != InterviewSessionStatus.ACTIVE:
            return InterviewRepository.to_session_record(interview_session)
        assert_transition(interview_session.status, InterviewSessionStatus.ABANDONED)
        return await self._repository.update_session_status(
            interview_session,
            InterviewSessionStatus.ABANDONED,
            end_reason=reason,
        )

    async def get_session(self, session_id: UUID, user_id: UUID) -> SessionRecord:
        interview_session = await self._repository.get_session_for_user(session_id, user_id)
        return InterviewRepository.to_session_record(interview_session)

    async def get_current_question(
        self,
        session_id: UUID,
        user_id: UUID,
    ) -> tuple[QuestionRecord, bool] | None:
        """Latest question and whether it has been answered (for WS resume)."""
        interview_session = await self._repository.get_session_for_user(session_id, user_id)
        latest = await self._repository.get_latest_question(interview_session)
        if latest is None:
            return None
        return (
            InterviewRepository.to_question_record(latest),
            latest.answer is not None,
        )

    async def _ask_next_question(
        self,
        interview_session: InterviewSession,
    ) -> QuestionResult:
        config = interview_session.config_snapshot
        max_questions = config.get("max_questions")
        next_sequence = interview_session.question_count + 1

        if max_questions is not None and next_sequence > max_questions:
            raise MaxQuestionsReachedError(
                "Maximum question count reached; end the session instead"
            )

        context = await self._build_interviewer_context(interview_session)
        output = await self._interviewer.generate_question(context)
        output = normalize_question_output(output, context.asked_topics)

        parent_question_id = None
        if output.is_follow_up and interview_session.questions:
            parent_question_id = max(interview_session.questions, key=lambda q: q.sequence_num).id

        question = await self._repository.add_question(
            interview_session,
            question_text=output.question_text,
            topic_tag=output.topic_tag,
            follow_up_intent=output.follow_up_intent,
            is_follow_up=output.is_follow_up,
            parent_question_id=parent_question_id,
            agent_metadata={
                "prompt_version": output.prompt_version,
                "should_end_session": output.should_end_session,
                "difficulty_adjustment": output.difficulty_adjustment,
            },
        )

        session = InterviewRepository.to_session_record(interview_session)

        # should_end_session marks this as the closing question. The session
        # stays ACTIVE so the candidate can still answer it; the caller ends
        # the session once that final answer has been submitted.
        return QuestionResult(
            session=session,
            question=question,
            should_end_session=output.should_end_session,
        )

    async def _build_interviewer_context(
        self,
        interview_session: InterviewSession,
    ) -> InterviewerContext:
        config = interview_session.config_snapshot
        summaries = await self._repository.get_context_summaries(interview_session)

        prior_turns: list[PriorTurn] = []
        asked_topics: list[str] = []
        for question in sorted(interview_session.questions, key=lambda q: q.sequence_num):
            asked_topics.append(question.topic_tag or "general")
            prior_turns.append(
                PriorTurn(
                    sequence_num=question.sequence_num,
                    question_text=question.question_text,
                    answer_text=question.answer.answer_text if question.answer else None,
                    topic_tag=question.topic_tag,
                )
            )

        company_context = config.get("company_context")
        if summaries.company_name and company_context:
            company_context = f"{summaries.company_name}: {company_context}"
        elif summaries.company_name:
            company_context = summaries.company_name

        if self._context_preparation is not None:
            return self._context_preparation.build_interviewer_context(
                interview_session,
                prior_turns=prior_turns,
                asked_topics=asked_topics,
                question_number=interview_session.question_count + 1,
                max_questions=config.get("max_questions"),
                company_context=company_context,
            )

        return InterviewerContext(
            interview_type=interview_session.interview_type,
            difficulty=config.get("difficulty", "mid"),
            target_role=config.get("target_role"),
            company_context=company_context,
            resume_summary=summaries.resume_summary,
            job_description_summary=summaries.job_description_summary,
            prior_turns=prior_turns,
            question_number=interview_session.question_count + 1,
            max_questions=config.get("max_questions"),
            asked_topics=asked_topics,
        )

    async def _ensure_ready_for_next_question(self, interview_session: InterviewSession) -> None:
        if interview_session.question_count == 0:
            return

        latest = await self._repository.get_latest_question(interview_session)
        if latest is None:
            return
        if latest.answer is None:
            raise ConflictError("Answer the current question before requesting the next one")

        config = interview_session.config_snapshot
        max_questions = config.get("max_questions")
        if max_questions is not None and interview_session.question_count >= max_questions:
            raise MaxQuestionsReachedError(
                "Maximum question count reached; end the session instead"
            )

    @staticmethod
    def _ensure_status(
        interview_session: InterviewSession,
        allowed: set[InterviewSessionStatus],
    ) -> None:
        if is_terminal(interview_session.status):
            raise InvalidStateError(f"Session is already {interview_session.status.value}")
        if interview_session.status not in allowed:
            allowed_values = ", ".join(sorted(s.value for s in allowed))
            raise InvalidStateError(
                f"Session must be in one of [{allowed_values}], got {interview_session.status.value}",
            )
