from dataclasses import replace

from app.ai.prompts.evaluation.coach.v1.builder import build_coach_messages
from app.db.enums import AgentName, InterviewType
from app.modules.evaluation.schemas import CandidateProfile, CoachInput
from tests.evaluation.helpers import build_specialist_results, sample_context
from tests.evaluation.test_coach_agent import _judge_output


def test_coach_prompt_includes_profile_and_judge_scores() -> None:
    context = replace(
        sample_context(
            InterviewType.BEHAVIORAL,
            answer_text="I led a migration that reduced deployment time by 40%.",
        ),
        candidate_profile=CandidateProfile(
            summary="8 years in backend engineering",
            target_role="Engineering Manager",
            experience_level="senior",
        ),
        historical_weaknesses=["Tends to skip measurable outcomes"],
    )

    coach_input = CoachInput(
        context=context,
        specialist_results=build_specialist_results(
            skipped_agents={AgentName.TECHNICAL_EVALUATION: "Not applicable"},
        ),
        judge_output=_judge_output(),
        historical_weaknesses=["Tends to skip measurable outcomes"],
    )

    messages = build_coach_messages(coach_input)

    assert messages[0]["role"] == "system"
    assert "NEVER use vague advice" in messages[0]["content"]
    assert "Engineering Manager" in messages[0]["content"]
    assert "measurable outcomes" in messages[0]["content"]
    assert "72" in messages[1]["content"]
