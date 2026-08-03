import json
from pathlib import Path

from app.ai.schemas.evaluation.judge import JudgeEvaluationOutput
from app.modules.evaluation.judge.scoring_model import METHODOLOGY_VERSION, ScoringBaseline
from app.modules.evaluation.schemas import AgentExecutionResult, EvaluationContext

PROMPT_VERSION = "1.0"
SCHEMA_VERSION = "1.0"
_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _load_template(name: str) -> str:
    return (_TEMPLATES_DIR / name).read_text(encoding="utf-8")


def _serialize_specialist_outputs(results: list[AgentExecutionResult]) -> str:
    payload = []
    for result in results:
        entry = {
            "agent_name": result.agent_name.value,
            "status": result.status.value,
            "skipped": result.skipped,
            "skip_reason": result.skip_reason,
            "error_message": result.error_message,
            "output": result.output.model_dump(mode="json") if result.output else None,
        }
        payload.append(entry)
    return json.dumps(payload, indent=2)


def build_judge_messages(
    context: EvaluationContext,
    specialist_results: list[AgentExecutionResult],
    baseline: ScoringBaseline,
) -> list[dict[str, str]]:
    fields = {
        "interview_type": context.interview_type.value,
        "difficulty": context.difficulty,
        "target_role": context.target_role or "Not specified",
        "company_context": context.company_context or "Not specified",
        "scope": context.scope.value,
        "prompt_version": PROMPT_VERSION,
        "methodology_version": METHODOLOGY_VERSION,
        "answer_text": context.answer_text,
        "question_text": context.question_text,
        "specialist_outputs": _serialize_specialist_outputs(specialist_results),
        "baseline_scores": json.dumps(
            {
                "overall_score": baseline.overall_score,
                "dimension_scores": baseline.dimension_scores.model_dump(mode="json"),
                "weights_applied": baseline.weights_applied,
                "applicable_dimensions": baseline.applicable_dimensions,
            },
            indent=2,
        ),
        "conflict_resolutions": (
            "\n".join(f"- {item}" for item in baseline.conflict_resolutions)
            if baseline.conflict_resolutions
            else "None"
        ),
        "strongest_dimensions": ", ".join(baseline.strongest_dimensions) or "None",
        "weakest_dimensions": ", ".join(baseline.weakest_dimensions) or "None",
    }

    return [
        {
            "role": "system",
            "content": _load_template("system.txt").format(**fields).strip(),
        },
        {"role": "user", "content": _load_template("user.txt").format(**fields).strip()},
    ]


def merge_judge_output(
    baseline: ScoringBaseline,
    synthesis: JudgeEvaluationOutput | object,
    *,
    prompt_version: str = PROMPT_VERSION,
) -> JudgeEvaluationOutput:
    if isinstance(synthesis, JudgeEvaluationOutput):
        return synthesis

    from app.ai.schemas.evaluation.judge import JudgeSynthesisOutput

    assert isinstance(synthesis, JudgeSynthesisOutput)
    return JudgeEvaluationOutput(
        overall_score=baseline.overall_score,
        dimension_scores=baseline.dimension_scores,
        strengths=synthesis.strengths,
        weaknesses=synthesis.weaknesses,
        evidence=synthesis.evidence,
        priority_improvements=synthesis.priority_improvements,
        strongest_dimensions=baseline.strongest_dimensions,
        weakest_dimensions=baseline.weakest_dimensions,
        conflict_resolutions=baseline.conflict_resolutions,
        weights_applied=baseline.weights_applied,
        scoring_methodology_version=METHODOLOGY_VERSION,
        prompt_version=prompt_version,
        summary=synthesis.summary,
    )
