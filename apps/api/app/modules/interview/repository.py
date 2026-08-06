import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.exceptions import NotFoundError
from app.db.enums import InterviewSessionStatus, InterviewType
from app.db.models.context import JobDescription, Resume
from app.db.models.interview import CandidateAnswer, InterviewQuestion, InterviewSession
from app.db.models.progress import UserProgressSnapshot
from app.db.models.user import User
from app.modules.interview.schemas import (
    AnswerRecord,
    ContextSummaries,
    QuestionRecord,
    SessionConfigInput,
    SessionRecord,
)


class InterviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ensure_user_exists(self, user_id: uuid.UUID) -> None:
        user = await self._session.get(User, user_id)
        if user is not None:
            return
        if settings.is_development:
            await self._create_dev_user_with_id(user_id)
            return
        raise NotFoundError("User not found")

    async def _create_dev_user_with_id(self, user_id: uuid.UUID) -> User:
        user = User(
            id=user_id,
            email=f"dev+{user_id}@local.voxforge",
            password_hash="dev",
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def create_user(self, email: str, password_hash: str = "dev") -> User:
        user = User(email=email, password_hash=password_hash)
        self._session.add(user)
        await self._session.flush()
        return user

    async def create_session(self, user_id: uuid.UUID, title: str | None = None) -> SessionRecord:
        await self.ensure_user_exists(user_id)
        interview_session = InterviewSession(
            user_id=user_id,
            interview_type=InterviewType.BEHAVIORAL,
            title=title,
            status=InterviewSessionStatus.CREATED,
        )
        self._session.add(interview_session)
        await self._session.flush()
        return self._to_session_record(interview_session)

    async def get_session_for_user(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> InterviewSession:
        result = await self._session.execute(
            select(InterviewSession)
            .where(
                InterviewSession.id == session_id,
                InterviewSession.user_id == user_id,
            )
            .options(
                selectinload(InterviewSession.questions).selectinload(InterviewQuestion.answer),
                selectinload(InterviewSession.resume),
                selectinload(InterviewSession.job_description),
            )
        )
        interview_session = result.scalar_one_or_none()
        if interview_session is None:
            raise NotFoundError("Interview session not found")
        return interview_session

    async def list_sessions_for_user(
        self,
        user_id: uuid.UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[InterviewSession]:
        result = await self._session.execute(
            select(InterviewSession)
            .where(InterviewSession.user_id == user_id)
            .order_by(InterviewSession.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_latest_overall_scores(
        self,
        session_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, float]:
        if not session_ids:
            return {}

        result = await self._session.execute(
            select(UserProgressSnapshot.session_id, UserProgressSnapshot.overall_score)
            .where(UserProgressSnapshot.session_id.in_(session_ids))
            .order_by(UserProgressSnapshot.recorded_at.desc())
        )

        scores: dict[uuid.UUID, float] = {}
        for session_id, overall_score in result.all():
            if session_id not in scores:
                scores[session_id] = float(overall_score)
        return scores

    async def configure_session(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        config: SessionConfigInput,
    ) -> SessionRecord:
        interview_session = await self.get_session_for_user(session_id, user_id)

        if config.resume_id is not None:
            await self._get_resume_for_user(config.resume_id, user_id)
            interview_session.resume_id = config.resume_id

        if config.job_description_id is not None:
            await self._get_job_description_for_user(config.job_description_id, user_id)
            interview_session.job_description_id = config.job_description_id

        interview_session.interview_type = config.interview_type
        interview_session.title = config.title or interview_session.title
        interview_session.config_snapshot = self._build_config_snapshot(config)
        interview_session.status = InterviewSessionStatus.CONFIGURED

        await self._session.flush()
        return self._to_session_record(interview_session)

    async def update_session_status(
        self,
        interview_session: InterviewSession,
        status: InterviewSessionStatus,
        *,
        end_reason: str | None = None,
    ) -> SessionRecord:
        interview_session.status = status
        if status == InterviewSessionStatus.ACTIVE and interview_session.started_at is None:
            interview_session.started_at = datetime.now(UTC)
        if status in {
            InterviewSessionStatus.COMPLETED,
            InterviewSessionStatus.ABANDONED,
            InterviewSessionStatus.EVALUATION_FAILED,
        }:
            interview_session.ended_at = datetime.now(UTC)
            interview_session.end_reason = end_reason
        await self._session.flush()
        return self._to_session_record(interview_session)

    async def add_question(
        self,
        interview_session: InterviewSession,
        *,
        question_text: str,
        topic_tag: str | None,
        follow_up_intent: str | None,
        is_follow_up: bool,
        agent_metadata: dict[str, Any],
        parent_question_id: uuid.UUID | None = None,
    ) -> QuestionRecord:
        sequence_num = interview_session.question_count + 1
        question = InterviewQuestion(
            session_id=interview_session.id,
            sequence_num=sequence_num,
            question_text=question_text,
            topic_tag=topic_tag,
            follow_up_intent=follow_up_intent,
            is_follow_up=is_follow_up,
            parent_question_id=parent_question_id,
            agent_metadata=agent_metadata,
            asked_at=datetime.now(UTC),
        )
        interview_session.question_count = sequence_num
        self._session.add(question)
        await self._session.flush()
        return self._to_question_record(question)

    async def add_answer(
        self,
        interview_session: InterviewSession,
        question_id: uuid.UUID,
        *,
        answer_text: str,
        duration_ms: int | None = None,
    ) -> AnswerRecord:
        question = next((q for q in interview_session.questions if q.id == question_id), None)
        if question is None:
            raise NotFoundError("Interview question not found")
        if question.answer is not None:
            raise ValueError("Question already has an answer")

        word_count = len(answer_text.split())
        answer = CandidateAnswer(
            session_id=interview_session.id,
            question_id=question_id,
            answer_text=answer_text,
            duration_ms=duration_ms,
            word_count=word_count,
            answered_at=datetime.now(UTC),
        )
        self._session.add(answer)
        await self._session.flush()
        return self._to_answer_record(answer)

    async def get_latest_question(
        self,
        interview_session: InterviewSession,
    ) -> InterviewQuestion | None:
        if not interview_session.questions:
            return None
        return max(interview_session.questions, key=lambda q: q.sequence_num)

    async def get_context_summaries(
        self,
        interview_session: InterviewSession,
    ) -> ContextSummaries:
        resume_summary = None
        jd_summary = None
        company_name = None

        if interview_session.resume is not None:
            resume_summary = interview_session.resume.summary_text
            if not resume_summary and interview_session.resume.parsed_profile:
                resume_summary = interview_session.resume.parsed_profile.get("summary_text")
            if not resume_summary:
                resume_summary = interview_session.resume.raw_text[:500]
        if interview_session.job_description is not None:
            jd = interview_session.job_description
            jd_summary = jd.summary_text
            if not jd_summary and jd.parsed_requirements:
                jd_summary = jd.parsed_requirements.get("summary_text")
            if not jd_summary:
                jd_summary = jd.raw_text[:500]
            company_name = jd.company_name

        return ContextSummaries(
            resume_summary=resume_summary,
            job_description_summary=jd_summary,
            company_name=company_name,
        )

    async def create_resume(
        self,
        user_id: uuid.UUID,
        *,
        title: str,
        raw_text: str,
        summary_text: str | None = None,
    ) -> Resume:
        await self.ensure_user_exists(user_id)
        resume = Resume(
            user_id=user_id,
            title=title,
            raw_text=raw_text,
            summary_text=summary_text,
        )
        self._session.add(resume)
        await self._session.flush()
        return resume

    async def create_job_description(
        self,
        user_id: uuid.UUID,
        *,
        title: str,
        raw_text: str,
        company_name: str | None = None,
        summary_text: str | None = None,
    ) -> JobDescription:
        await self.ensure_user_exists(user_id)
        job_description = JobDescription(
            user_id=user_id,
            title=title,
            raw_text=raw_text,
            company_name=company_name,
            summary_text=summary_text,
        )
        self._session.add(job_description)
        await self._session.flush()
        return job_description

    async def _get_resume_for_user(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> Resume:
        result = await self._session.execute(
            select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
        )
        resume = result.scalar_one_or_none()
        if resume is None:
            raise NotFoundError("Resume not found")
        return resume

    async def _get_job_description_for_user(
        self,
        job_description_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> JobDescription:
        result = await self._session.execute(
            select(JobDescription).where(
                JobDescription.id == job_description_id,
                JobDescription.user_id == user_id,
            )
        )
        job_description = result.scalar_one_or_none()
        if job_description is None:
            raise NotFoundError("Job description not found")
        return job_description

    @staticmethod
    def _build_config_snapshot(config: SessionConfigInput) -> dict[str, Any]:
        return {
            "interview_type": config.interview_type.value,
            "difficulty": config.difficulty,
            "target_role": config.target_role,
            "company_context": config.company_context,
            "max_questions": config.max_questions,
            "target_duration_minutes": config.target_duration_minutes,
        }

    @classmethod
    def to_session_record(cls, interview_session: InterviewSession) -> SessionRecord:
        return cls._to_session_record(interview_session)

    @staticmethod
    def _to_session_record(interview_session: InterviewSession) -> SessionRecord:
        return SessionRecord(
            id=interview_session.id,
            user_id=interview_session.user_id,
            status=interview_session.status,
            interview_type=interview_session.interview_type,
            title=interview_session.title,
            config_snapshot=interview_session.config_snapshot,
            question_count=interview_session.question_count,
            resume_id=interview_session.resume_id,
            job_description_id=interview_session.job_description_id,
            started_at=interview_session.started_at,
            ended_at=interview_session.ended_at,
            end_reason=interview_session.end_reason,
        )

    @staticmethod
    def _to_question_record(question: InterviewQuestion) -> QuestionRecord:
        return QuestionRecord(
            id=question.id,
            session_id=question.session_id,
            sequence_num=question.sequence_num,
            question_text=question.question_text,
            topic_tag=question.topic_tag,
            follow_up_intent=question.follow_up_intent,
            is_follow_up=question.is_follow_up,
            asked_at=question.asked_at,
            agent_metadata=question.agent_metadata,
        )

    @staticmethod
    def _to_answer_record(answer: CandidateAnswer) -> AnswerRecord:
        return AnswerRecord(
            id=answer.id,
            session_id=answer.session_id,
            question_id=answer.question_id,
            answer_text=answer.answer_text,
            answered_at=answer.answered_at,
            duration_ms=answer.duration_ms,
            word_count=answer.word_count,
        )
