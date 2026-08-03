from datetime import UTC, datetime

from app.ai.schemas.evaluation.behavioral import BehavioralDimensions, BehavioralEvaluationOutput
from app.ai.schemas.evaluation.common import DimensionScore
from app.ai.schemas.evaluation.communication import CommunicationDimensions, CommunicationEvaluationOutput
from app.ai.schemas.evaluation.hiring_manager import HiringManagerDimensions, HiringManagerEvaluationOutput
from app.ai.schemas.evaluation.relevance import RelevanceDimensions, RelevanceEvaluationOutput
from app.ai.schemas.evaluation.technical import TechnicalDimensions, TechnicalEvaluationOutput
from app.db.enums import AgentName, EvaluationRunStatus, HireRecommendation, InterviewType
from app.modules.evaluation.schemas import AgentExecutionResult, EvaluationContext


def _dim(score: float, rationale: str = "Test rationale.") -> DimensionScore:
    return DimensionScore(score=score, rationale=rationale, evidence=["Test evidence."])


def _completed(
    agent_name: AgentName,
    output,
) -> AgentExecutionResult:
    return AgentExecutionResult(
        agent_name=agent_name,
        status=EvaluationRunStatus.COMPLETED,
        schema_version="1.0",
        output=output,
        model_id="mock-structured",
        prompt_version="1.0",
        latency_ms=10,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )


def _failed(agent_name: AgentName) -> AgentExecutionResult:
    return AgentExecutionResult(
        agent_name=agent_name,
        status=EvaluationRunStatus.FAILED,
        schema_version="1.0",
        error_message="Simulated failure",
        model_id="mock-structured",
        prompt_version="1.0",
        latency_ms=5,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )


def _skipped(agent_name: AgentName, reason: str) -> AgentExecutionResult:
    return AgentExecutionResult(
        agent_name=agent_name,
        status=EvaluationRunStatus.SKIPPED,
        schema_version="1.0",
        skipped=True,
        skip_reason=reason,
        model_id="mock-structured",
        prompt_version="1.0",
        latency_ms=1,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )


def communication_output(
    *,
    clarity: float = 7.5,
    structure: float = 7.0,
    conciseness: float = 6.0,
    confidence: float = 8.0,
    tone: float = 8.0,
) -> CommunicationEvaluationOutput:
    return CommunicationEvaluationOutput(
        summary="Communication evaluation summary for tests.",
        strengths=["Clear delivery"],
        gaps=["Could be tighter"],
        dimensions=CommunicationDimensions(
            clarity=_dim(clarity),
            structure=_dim(structure),
            conciseness=_dim(conciseness),
            confidence=_dim(confidence),
            tone=_dim(tone),
        ),
    )


def technical_output(
    *,
    depth: float = 7.0,
    accuracy: float = 7.5,
    problem_solving: float = 7.0,
    trade_off_awareness: float = 6.5,
) -> TechnicalEvaluationOutput:
    return TechnicalEvaluationOutput(
        summary="Technical evaluation summary for tests.",
        strengths=["Solid reasoning"],
        gaps=["Limited edge-case depth"],
        dimensions=TechnicalDimensions(
            depth=_dim(depth),
            accuracy=_dim(accuracy),
            problem_solving=_dim(problem_solving),
            trade_off_awareness=_dim(trade_off_awareness),
        ),
    )


def behavioral_output(
    *,
    star_method: float = 8.0,
    ownership: float = 7.5,
    collaboration: float = 7.0,
    impact: float = 6.5,
) -> BehavioralEvaluationOutput:
    return BehavioralEvaluationOutput(
        summary="Behavioral evaluation summary for tests.",
        strengths=["STAR structure"],
        gaps=["Impact not quantified"],
        dimensions=BehavioralDimensions(
            star_method=_dim(star_method),
            ownership=_dim(ownership),
            collaboration=_dim(collaboration),
            impact=_dim(impact),
        ),
    )


def relevance_output(
    *,
    role_alignment: float = 7.5,
    jd_alignment: float = 7.0,
    question_responsiveness: float = 8.0,
    context_usage: float = 7.0,
) -> RelevanceEvaluationOutput:
    return RelevanceEvaluationOutput(
        summary="Relevance evaluation summary for tests.",
        strengths=["On topic"],
        gaps=["JD alignment could improve"],
        dimensions=RelevanceDimensions(
            role_alignment=_dim(role_alignment),
            jd_alignment=_dim(jd_alignment),
            question_responsiveness=_dim(question_responsiveness),
            context_usage=_dim(context_usage),
        ),
    )


def hiring_manager_output(
    *,
    role_readiness: float = 7.0,
    culture_fit: float = 7.5,
    growth_potential: float = 7.0,
    risk_assessment: float = 6.5,
) -> HiringManagerEvaluationOutput:
    return HiringManagerEvaluationOutput(
        summary="Hiring manager evaluation summary for tests.",
        strengths=["Promising fit"],
        gaps=["Needs more depth"],
        hire_recommendation=HireRecommendation.LEAN_HIRE,
        decision_rationale="Proceed with follow-up questions.",
        dimensions=HiringManagerDimensions(
            role_readiness=_dim(role_readiness),
            culture_fit=_dim(culture_fit),
            growth_potential=_dim(growth_potential),
            risk_assessment=_dim(risk_assessment),
        ),
    )


def build_specialist_results(
    *,
    communication: CommunicationEvaluationOutput | None = None,
    technical: TechnicalEvaluationOutput | None = None,
    behavioral: BehavioralEvaluationOutput | None = None,
    relevance: RelevanceEvaluationOutput | None = None,
    hiring_manager: HiringManagerEvaluationOutput | None = None,
    failed_agents: set[AgentName] | None = None,
    skipped_agents: dict[AgentName, str] | None = None,
) -> list[AgentExecutionResult]:
    failed = failed_agents or set()
    skipped = skipped_agents or {}
    results: list[AgentExecutionResult] = []

    outputs: dict[AgentName, object | None] = {
        AgentName.COMMUNICATION_EVALUATION: communication if communication is not None else communication_output(),
        AgentName.TECHNICAL_EVALUATION: technical,
        AgentName.BEHAVIORAL_EVALUATION: behavioral if behavioral is not None else behavioral_output(),
        AgentName.RELEVANCE_EVALUATION: relevance if relevance is not None else relevance_output(),
        AgentName.HIRING_MANAGER_EVALUATION: hiring_manager if hiring_manager is not None else hiring_manager_output(),
    }

    if outputs[AgentName.TECHNICAL_EVALUATION] is None and AgentName.TECHNICAL_EVALUATION not in skipped:
        outputs[AgentName.TECHNICAL_EVALUATION] = technical_output()

    for agent_name, output in outputs.items():
        if agent_name in failed:
            results.append(_failed(agent_name))
        elif agent_name in skipped:
            results.append(_skipped(agent_name, skipped[agent_name]))
        elif output is None:
            results.append(_skipped(agent_name, "Not applicable"))
        else:
            results.append(_completed(agent_name, output))

    return results


def sample_context(
    interview_type: InterviewType = InterviewType.TECHNICAL,
    *,
    answer_text: str = "I would inspect metrics, traces, and recent deploys before narrowing to a bottleneck.",
) -> EvaluationContext:
    return EvaluationContext(
        interview_type=interview_type,
        difficulty="senior",
        target_role="Staff Engineer",
        question_text="How would you debug elevated API latency?",
        answer_text=answer_text,
        topic_tag="debugging",
    )
