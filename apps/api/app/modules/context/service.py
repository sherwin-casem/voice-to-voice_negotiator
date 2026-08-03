from uuid import UUID

from app.ai.schemas.context import ParsedJobRequirements, ParsedResumeProfile
from app.ai.schemas.interviewer import InterviewerContext, PriorTurn
from app.core.exceptions import AppError
from app.db.enums import DocumentParseStatus, InterviewType
from app.db.models.interview import InterviewSession
from app.modules.context.extractor import HeuristicContextExtractor, LLMContextExtractor
from app.modules.context.repository import ContextRepository
from app.modules.context.schemas import InterviewStep, PreparedContextBundle, StepContext
from app.modules.context.selector import ContextSelector
from app.modules.evaluation.schemas import CandidateProfile, ConversationTurn, EvaluationContext
from app.db.enums import EvaluationScope


class ContextPreparationService:
    """Parse documents once, then serve compact step-specific context slices."""

    def __init__(
        self,
        repository: ContextRepository,
        extractor: HeuristicContextExtractor | LLMContextExtractor,
        selector: ContextSelector | None = None,
    ) -> None:
        self._repository = repository
        self._extractor = extractor
        self._selector = selector or ContextSelector()

    async def prepare_resume(
        self,
        resume_id: UUID,
        user_id: UUID,
        *,
        source_filename: str | None = None,
        mime_type: str | None = None,
    ) -> ParsedResumeProfile:
        resume = await self._repository.get_resume(resume_id, user_id)
        try:
            profile = await self._extractor.extract_resume(resume.raw_text, title=resume.title)
            await self._repository.save_resume_preparation(
                resume,
                parsed_profile=profile.model_dump(mode="json"),
                summary_text=profile.summary_text,
                parse_status=DocumentParseStatus.PARSED,
                source_filename=source_filename,
                mime_type=mime_type,
            )
            return profile
        except Exception as exc:
            await self._repository.save_resume_preparation(
                resume,
                parsed_profile=resume.parsed_profile or {},
                summary_text=resume.summary_text or resume.raw_text[:500],
                parse_status=DocumentParseStatus.FAILED,
                source_filename=source_filename,
                mime_type=mime_type,
            )
            raise AppError(
                "CONTEXT_PREPARATION_FAILED",
                f"Resume preparation failed: {exc}",
            ) from exc

    async def prepare_job_description(
        self,
        job_description_id: UUID,
        user_id: UUID,
        *,
        source_filename: str | None = None,
        mime_type: str | None = None,
    ) -> ParsedJobRequirements:
        job_description = await self._repository.get_job_description(job_description_id, user_id)
        try:
            requirements = await self._extractor.extract_job_description(
                job_description.raw_text,
                title=job_description.title,
                company_name=job_description.company_name,
            )
            await self._repository.save_job_description_preparation(
                job_description,
                parsed_requirements=requirements.model_dump(mode="json"),
                summary_text=requirements.summary_text,
                parse_status=DocumentParseStatus.PARSED,
                source_filename=source_filename,
                mime_type=mime_type,
            )
            return requirements
        except Exception as exc:
            await self._repository.save_job_description_preparation(
                job_description,
                parsed_requirements=job_description.parsed_requirements or {},
                summary_text=job_description.summary_text or job_description.raw_text[:500],
                parse_status=DocumentParseStatus.FAILED,
                source_filename=source_filename,
                mime_type=mime_type,
            )
            raise AppError(
                "CONTEXT_PREPARATION_FAILED",
                f"Job description preparation failed: {exc}",
            ) from exc

    async def ensure_session_documents_prepared(
        self,
        interview_session: InterviewSession,
        user_id: UUID,
    ) -> None:
        if interview_session.resume_id is not None and interview_session.resume is not None:
            if interview_session.resume.parse_status != DocumentParseStatus.PARSED:
                await self.prepare_resume(interview_session.resume_id, user_id)
        if (
            interview_session.job_description_id is not None
            and interview_session.job_description is not None
        ):
            if interview_session.job_description.parse_status != DocumentParseStatus.PARSED:
                await self.prepare_job_description(interview_session.job_description_id, user_id)

    def build_bundle(self, interview_session: InterviewSession) -> PreparedContextBundle:
        config = interview_session.config_snapshot
        resume_profile = None
        job_requirements = None

        if interview_session.resume and interview_session.resume.parsed_profile:
            resume_profile = ParsedResumeProfile.model_validate(interview_session.resume.parsed_profile)
        elif interview_session.resume and interview_session.resume.summary_text:
            resume_profile = ParsedResumeProfile(
                summary_text=_ensure_summary(
                    interview_session.resume.summary_text or interview_session.resume.raw_text
                ),
                skills=[],
            )

        if interview_session.job_description and interview_session.job_description.parsed_requirements:
            job_requirements = ParsedJobRequirements.model_validate(
                interview_session.job_description.parsed_requirements
            )
        elif interview_session.job_description and interview_session.job_description.summary_text:
            job_requirements = ParsedJobRequirements(
                summary_text=_ensure_summary(
                    interview_session.job_description.summary_text
                    or interview_session.job_description.raw_text
                ),
            )

        company_name = (
            interview_session.job_description.company_name
            if interview_session.job_description
            else None
        )
        return PreparedContextBundle(
            resume_profile=resume_profile,
            job_requirements=job_requirements,
            company_name=company_name,
            target_role=config.get("target_role"),
            interview_type=interview_session.interview_type.value,
            difficulty=config.get("difficulty"),
        )

    def select_step_context(
        self,
        interview_session: InterviewSession,
        step: InterviewStep,
        *,
        asked_topics: list[str] | None = None,
        current_topic_tag: str | None = None,
        prior_answer_text: str | None = None,
    ) -> StepContext:
        bundle = self.build_bundle(interview_session)
        return self._selector.select(
            bundle,
            step,
            asked_topics=asked_topics,
            current_topic_tag=current_topic_tag,
            prior_answer_text=prior_answer_text,
        )

    def build_interviewer_context(
        self,
        interview_session: InterviewSession,
        *,
        prior_turns: list[PriorTurn],
        asked_topics: list[str],
        question_number: int,
        max_questions: int | None,
        company_context: str | None,
    ) -> InterviewerContext:
        is_follow_up = bool(prior_turns and prior_turns[-1].answer_text)
        step = InterviewStep.INTERVIEWER_FOLLOW_UP if is_follow_up else InterviewStep.INTERVIEWER_OPENING
        current_topic = prior_turns[-1].topic_tag if prior_turns else None
        prior_answer = prior_turns[-1].answer_text if prior_turns else None
        selected = self.select_step_context(
            interview_session,
            step,
            asked_topics=asked_topics,
            current_topic_tag=current_topic,
            prior_answer_text=prior_answer,
        )
        config = interview_session.config_snapshot
        difficulty = selected.suggested_difficulty or config.get("difficulty", "mid")

        return InterviewerContext(
            interview_type=interview_session.interview_type,
            difficulty=difficulty,
            target_role=config.get("target_role"),
            company_context=company_context,
            resume_summary=selected.resume_summary,
            job_description_summary=selected.job_description_summary,
            candidate_skills=selected.candidate_skills,
            relevant_experience=selected.relevant_experience,
            relevant_projects=selected.relevant_projects,
            role_responsibilities=selected.role_responsibilities,
            technical_focus_areas=selected.technical_focus_areas,
            behavioral_focus_areas=selected.behavioral_focus_areas,
            likely_interview_topics=selected.likely_interview_topics,
            evaluation_rubric_hints=selected.evaluation_rubric_hints,
            prior_turns=prior_turns,
            question_number=question_number,
            max_questions=max_questions,
            asked_topics=asked_topics,
        )

    def build_evaluation_context(
        self,
        interview_session: InterviewSession,
        *,
        question_text: str,
        answer_text: str,
        topic_tag: str | None,
        prior_turns: list[ConversationTurn],
        scope: EvaluationScope = EvaluationScope.ANSWER,
    ) -> EvaluationContext:
        selected = self.select_step_context(
            interview_session,
            InterviewStep.EVALUATION_ANSWER,
            current_topic_tag=topic_tag,
        )
        rubric = self.select_step_context(
            interview_session,
            InterviewStep.EVALUATION_RUBRIC,
            current_topic_tag=topic_tag,
        )
        config = interview_session.config_snapshot
        company_context = config.get("company_context")
        if interview_session.job_description and interview_session.job_description.company_name:
            if company_context:
                company_context = (
                    f"{interview_session.job_description.company_name}: {company_context}"
                )
            else:
                company_context = interview_session.job_description.company_name

        resume = interview_session.resume
        candidate_profile = None
        if resume and resume.parsed_profile:
            profile = ParsedResumeProfile.model_validate(resume.parsed_profile)
            candidate_profile = CandidateProfile(
                summary=profile.summary_text,
                target_role=config.get("target_role"),
                experience_level=selected.suggested_difficulty,
            )

        merged_rubric = _unique_strings(
            selected.evaluation_rubric_hints + rubric.evaluation_rubric_hints
        )

        return EvaluationContext(
            interview_type=interview_session.interview_type,
            difficulty=selected.suggested_difficulty or config.get("difficulty", "mid"),
            question_text=question_text,
            answer_text=answer_text,
            scope=scope,
            target_role=config.get("target_role"),
            company_context=company_context,
            resume_summary=selected.resume_summary,
            job_description_summary=selected.job_description_summary,
            topic_tag=topic_tag,
            prior_turns=prior_turns,
            session_id=interview_session.id,
            candidate_profile=candidate_profile,
            candidate_skills=selected.candidate_skills,
            relevant_experience=selected.relevant_experience,
            role_responsibilities=selected.role_responsibilities,
            technical_focus_areas=selected.technical_focus_areas,
            behavioral_focus_areas=selected.behavioral_focus_areas,
            evaluation_rubric_hints=merged_rubric,
        )


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(value)
    return output


def _ensure_summary(value: str) -> str:
    trimmed = value.strip()[:5000]
    if len(trimmed) >= 10:
        return trimmed
    return "Context summary prepared for interview personalization."
