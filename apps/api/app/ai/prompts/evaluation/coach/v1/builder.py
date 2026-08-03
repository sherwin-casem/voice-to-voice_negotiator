import json
from pathlib import Path

from app.ai.schemas.evaluation.judge import JudgeEvaluationOutput
from app.modules.evaluation.context_format import format_prior_turns
from app.modules.evaluation.schemas import AgentExecutionResult, CoachInput

PROMPT_VERSION = "1.0"
SCHEMA_VERSION = "1.0"
_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _load_template(name: str) -> str:
    return (_TEMPLATES_DIR / name).read_text(encoding="utf-8")


def _serialize_specialist_outputs(results: list[AgentExecutionResult]) -> str:
    payload = []
    for result in results:
        payload.append(
            {
                "agent_name": result.agent_name.value,
                "status": result.status.value,
                "skipped": result.skipped,
                "output": result.output.model_dump(mode="json") if result.output else None,
            }
        )
    return json.dumps(payload, indent=2)


def _format_candidate_profile(coach_input: CoachInput) -> str:
    profile = coach_input.candidate_profile
    if profile is None:
        resume = coach_input.context.resume_summary
        role = coach_input.context.target_role
        if resume or role:
            return f"Target role: {role or 'Not specified'}\nResume summary: {resume or 'Not provided'}"
        return "Not provided"

    lines = []
    if profile.target_role:
        lines.append(f"Target role: {profile.target_role}")
    if profile.experience_level:
        lines.append(f"Experience level: {profile.experience_level}")
    if profile.summary:
        lines.append(f"Summary: {profile.summary}")
    return "\n".join(lines) if lines else "Not provided"


def _format_historical_weaknesses(coach_input: CoachInput) -> str:
    weaknesses = coach_input.historical_weaknesses or coach_input.context.historical_weaknesses
    if not weaknesses:
        return "None recorded"
    return "\n".join(f"- {item}" for item in weaknesses)


def build_coach_messages(coach_input: CoachInput) -> list[dict[str, str]]:
    context = coach_input.context
    judge: JudgeEvaluationOutput = coach_input.judge_output

    fields = {
        "prompt_version": PROMPT_VERSION,
        "interview_type": context.interview_type.value,
        "difficulty": context.difficulty,
        "target_role": context.target_role or "Not specified",
        "company_context": context.company_context or "Not specified",
        "candidate_profile": _format_candidate_profile(coach_input),
        "historical_weaknesses": _format_historical_weaknesses(coach_input),
        "question_text": context.question_text,
        "answer_text": context.answer_text,
        "judge_output": judge.model_dump_json(indent=2),
        "specialist_outputs": _serialize_specialist_outputs(coach_input.specialist_results),
        "weakest_dimensions": ", ".join(judge.weakest_dimensions) or "None",
        "strongest_dimensions": ", ".join(judge.strongest_dimensions) or "None",
        "overall_score": str(judge.overall_score),
        "prior_turns": format_prior_turns(context.prior_turns),
    }

    return [
        {
            "role": "system",
            "content": _load_template("system.txt").format(**fields).strip(),
        },
        {"role": "user", "content": _load_template("user.txt").format(**fields).strip()},
    ]
