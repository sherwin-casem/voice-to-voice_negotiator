import pytest

from app.ai.prompts.interviewer.v1.builder import PROMPT_VERSION
from app.ai.schemas.interviewer import InterviewerContext, PriorTurn
from app.db.enums import InterviewType
from app.modules.interview.interviewer_agent import InterviewerAgent, MockInterviewerLLMProvider


@pytest.mark.parametrize(
    "interview_type",
    [
        InterviewType.BEHAVIORAL,
        InterviewType.TECHNICAL,
        InterviewType.SYSTEM_DESIGN,
        InterviewType.LEADERSHIP,
        InterviewType.HR,
    ],
)
@pytest.mark.asyncio
async def test_mock_interviewer_generates_opening_question(
    interview_type: InterviewType,
) -> None:
    agent = InterviewerAgent(MockInterviewerLLMProvider())
    output = await agent.generate_question(
        InterviewerContext(
            interview_type=interview_type,
            difficulty="mid",
            question_number=1,
            max_questions=3,
        )
    )

    assert output.question_text
    assert output.topic_tag
    assert output.is_follow_up is False
    assert output.should_end_session is False
    assert output.prompt_version == PROMPT_VERSION


@pytest.mark.asyncio
async def test_mock_interviewer_marks_final_question_for_end() -> None:
    agent = InterviewerAgent(MockInterviewerLLMProvider())
    output = await agent.generate_question(
        InterviewerContext(
            interview_type=InterviewType.TECHNICAL,
            difficulty="mid",
            question_number=3,
            max_questions=3,
            prior_turns=[
                PriorTurn(sequence_num=1, question_text="Q1", answer_text="A1", topic_tag="t1"),
                PriorTurn(sequence_num=2, question_text="Q2", answer_text="A2", topic_tag="t2"),
            ],
            asked_topics=["t1", "t2"],
        )
    )

    assert output.should_end_session is True


@pytest.mark.asyncio
async def test_mock_interviewer_avoids_duplicate_topic_tags() -> None:
    agent = InterviewerAgent(MockInterviewerLLMProvider())
    opening = MockInterviewerLLMProvider._OPENING_QUESTIONS[InterviewType.HR]
    output = await agent.generate_question(
        InterviewerContext(
            interview_type=InterviewType.HR,
            difficulty="mid",
            question_number=2,
            asked_topics=[opening[1]],
            prior_turns=[
                PriorTurn(sequence_num=1, question_text="Q1", answer_text="A1", topic_tag=opening[1]),
            ],
        )
    )

    assert output.topic_tag != opening[1] or "new area" in output.question_text.lower()


@pytest.mark.asyncio
async def test_mock_interviewer_uses_likely_interview_topics() -> None:
    agent = InterviewerAgent(MockInterviewerLLMProvider())
    output = await agent.generate_question(
        InterviewerContext(
            interview_type=InterviewType.TECHNICAL,
            difficulty="mid",
            question_number=1,
            likely_interview_topics=["Distributed systems"],
        )
    )

    assert "distributed systems" in output.question_text.lower()
    assert output.topic_tag == "distributed_systems"
