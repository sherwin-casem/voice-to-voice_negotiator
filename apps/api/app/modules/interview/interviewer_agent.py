from app.ai.prompts.interviewer.v1 import PROMPT_VERSION, build_interviewer_messages
from app.ai.providers.base import StructuredOutputProvider
from app.ai.schemas.interviewer import InterviewerContext, InterviewerQuestionOutput
from app.db.enums import InterviewType


class MockInterviewerLLMProvider:
    """Deterministic interviewer responses for tests and local development."""

    _OPENING_QUESTIONS: dict[InterviewType, tuple[str, str]] = {
        InterviewType.BEHAVIORAL: (
            "Tell me about a time you faced a significant challenge at work and how you handled it.",
            "challenge_handling",
        ),
        InterviewType.TECHNICAL: (
            "Walk me through how you would debug a production issue causing elevated API latency.",
            "debugging",
        ),
        InterviewType.SYSTEM_DESIGN: (
            "How would you design a scalable notification system for millions of users?",
            "notifications_design",
        ),
        InterviewType.LEADERSHIP: (
            "Describe a situation where you had to align a team around a difficult decision.",
            "team_alignment",
        ),
        InterviewType.HR: (
            "What motivated you to pursue this role, and what are you looking for in your next team?",
            "motivation",
        ),
    }

    _FOLLOW_UP_QUESTIONS: dict[InterviewType, tuple[str, str]] = {
        InterviewType.BEHAVIORAL: (
            "What was the outcome of that situation, and what would you do differently next time?",
            "reflection",
        ),
        InterviewType.TECHNICAL: (
            "What trade-offs did you consider, and how would you prevent this issue from recurring?",
            "tradeoffs",
        ),
        InterviewType.SYSTEM_DESIGN: (
            "How would your design handle peak traffic spikes and partial regional outages?",
            "resilience",
        ),
        InterviewType.LEADERSHIP: (
            "How did you measure whether that decision improved team outcomes?",
            "impact_measurement",
        ),
        InterviewType.HR: (
            "How does this role fit your longer-term career goals?",
            "career_goals",
        ),
    }

    async def generate_structured(
        self,
        messages: list[dict[str, str]] | list,
        response_model: type[InterviewerQuestionOutput],
        **kwargs: object,
    ) -> InterviewerQuestionOutput:
        _ = messages, kwargs
        raise NotImplementedError("Use generate_question(context) for mock interviewer output")

    async def generate_question(self, context: InterviewerContext) -> InterviewerQuestionOutput:
        asked_topics = set(context.asked_topics)
        is_follow_up = bool(context.prior_turns and context.prior_turns[-1].answer_text)

        if is_follow_up:
            question_text, topic_tag = self._FOLLOW_UP_QUESTIONS[context.interview_type]
        else:
            question_text, topic_tag = self._OPENING_QUESTIONS[context.interview_type]

        if topic_tag in asked_topics:
            question_text = (
                f"Building on a new area we have not covered yet, {question_text.lower()}"
            )
            topic_tag = f"{topic_tag}_variant"

        should_end = False
        if context.max_questions is not None and context.question_number >= context.max_questions:
            should_end = True

        difficulty_adjustment = "same"
        if context.difficulty == "junior":
            difficulty_adjustment = "easier"
        elif context.difficulty == "senior" and is_follow_up:
            difficulty_adjustment = "harder"

        return InterviewerQuestionOutput(
            question_text=question_text,
            topic_tag=topic_tag,
            follow_up_intent="Probe deeper based on the prior answer" if is_follow_up else None,
            is_follow_up=is_follow_up,
            should_end_session=should_end,
            difficulty_adjustment=difficulty_adjustment,
            prompt_version=PROMPT_VERSION,
        )


class InterviewerAgent:
    """Generates the next interview question using versioned prompts and structured output."""

    def __init__(self, llm_provider: StructuredOutputProvider | MockInterviewerLLMProvider) -> None:
        self._llm = llm_provider

    async def generate_question(self, context: InterviewerContext) -> InterviewerQuestionOutput:
        if isinstance(self._llm, MockInterviewerLLMProvider):
            return await self._llm.generate_question(context)

        messages = build_interviewer_messages(context)
        output = await self._llm.generate_structured(
            messages,
            InterviewerQuestionOutput,
        )
        return output.model_copy(update={"prompt_version": PROMPT_VERSION})
