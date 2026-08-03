from app.ai.prompts.evaluation.behavioral.v1.builder import (
    PROMPT_VERSION as BEHAVIORAL_PROMPT_VERSION,
)
from app.ai.prompts.evaluation.behavioral.v1.builder import (
    SCHEMA_VERSION as BEHAVIORAL_SCHEMA_VERSION,
)
from app.ai.prompts.evaluation.behavioral.v1.builder import build_behavioral_messages
from app.ai.prompts.evaluation.communication.v1.builder import (
    PROMPT_VERSION as COMMUNICATION_PROMPT_VERSION,
)
from app.ai.prompts.evaluation.communication.v1.builder import (
    SCHEMA_VERSION as COMMUNICATION_SCHEMA_VERSION,
)
from app.ai.prompts.evaluation.communication.v1.builder import build_communication_messages
from app.ai.prompts.evaluation.hiring_manager.v1.builder import (
    PROMPT_VERSION as HIRING_MANAGER_PROMPT_VERSION,
)
from app.ai.prompts.evaluation.hiring_manager.v1.builder import (
    SCHEMA_VERSION as HIRING_MANAGER_SCHEMA_VERSION,
)
from app.ai.prompts.evaluation.hiring_manager.v1.builder import build_hiring_manager_messages
from app.ai.prompts.evaluation.relevance.v1.builder import (
    PROMPT_VERSION as RELEVANCE_PROMPT_VERSION,
)
from app.ai.prompts.evaluation.relevance.v1.builder import (
    SCHEMA_VERSION as RELEVANCE_SCHEMA_VERSION,
)
from app.ai.prompts.evaluation.relevance.v1.builder import build_relevance_messages
from app.ai.prompts.evaluation.technical.v1.builder import (
    PROMPT_VERSION as TECHNICAL_PROMPT_VERSION,
)
from app.ai.prompts.evaluation.technical.v1.builder import (
    SCHEMA_VERSION as TECHNICAL_SCHEMA_VERSION,
)
from app.ai.prompts.evaluation.technical.v1.builder import build_technical_messages
from app.ai.providers.base import StructuredOutputProvider
from app.ai.schemas.evaluation.behavioral import BehavioralEvaluationOutput
from app.ai.schemas.evaluation.communication import CommunicationEvaluationOutput
from app.ai.schemas.evaluation.hiring_manager import HiringManagerEvaluationOutput
from app.ai.schemas.evaluation.relevance import RelevanceEvaluationOutput
from app.ai.schemas.evaluation.technical import TechnicalEvaluationOutput
from app.db.enums import AgentName
from app.modules.evaluation.agents.base import BaseEvaluator
from app.modules.evaluation.gating import (
    should_run_behavioral,
    should_run_communication,
    should_run_hiring_manager,
    should_run_relevance,
    should_run_technical,
)
from app.modules.evaluation.schemas import EvaluationContext


def _communication_gating(context: EvaluationContext) -> tuple[bool, str | None]:
    return should_run_communication(context.interview_type)


def _technical_gating(context: EvaluationContext) -> tuple[bool, str | None]:
    return should_run_technical(context.interview_type)


def _behavioral_gating(context: EvaluationContext) -> tuple[bool, str | None]:
    return should_run_behavioral(context.interview_type)


def _relevance_gating(context: EvaluationContext) -> tuple[bool, str | None]:
    return should_run_relevance(context.interview_type)


def _hiring_manager_gating(context: EvaluationContext) -> tuple[bool, str | None]:
    return should_run_hiring_manager(context.interview_type)


def build_specialist_evaluators(
    llm_provider: StructuredOutputProvider,
    *,
    model_id: str,
) -> list[BaseEvaluator]:
    return [
        BaseEvaluator(
            agent_name=AgentName.COMMUNICATION_EVALUATION,
            output_schema=CommunicationEvaluationOutput,
            schema_version=COMMUNICATION_SCHEMA_VERSION,
            prompt_version=COMMUNICATION_PROMPT_VERSION,
            build_messages=build_communication_messages,
            should_run_fn=_communication_gating,
            llm_provider=llm_provider,
            model_id=model_id,
        ),
        BaseEvaluator(
            agent_name=AgentName.TECHNICAL_EVALUATION,
            output_schema=TechnicalEvaluationOutput,
            schema_version=TECHNICAL_SCHEMA_VERSION,
            prompt_version=TECHNICAL_PROMPT_VERSION,
            build_messages=build_technical_messages,
            should_run_fn=_technical_gating,
            llm_provider=llm_provider,
            model_id=model_id,
        ),
        BaseEvaluator(
            agent_name=AgentName.BEHAVIORAL_EVALUATION,
            output_schema=BehavioralEvaluationOutput,
            schema_version=BEHAVIORAL_SCHEMA_VERSION,
            prompt_version=BEHAVIORAL_PROMPT_VERSION,
            build_messages=build_behavioral_messages,
            should_run_fn=_behavioral_gating,
            llm_provider=llm_provider,
            model_id=model_id,
        ),
        BaseEvaluator(
            agent_name=AgentName.RELEVANCE_EVALUATION,
            output_schema=RelevanceEvaluationOutput,
            schema_version=RELEVANCE_SCHEMA_VERSION,
            prompt_version=RELEVANCE_PROMPT_VERSION,
            build_messages=build_relevance_messages,
            should_run_fn=_relevance_gating,
            llm_provider=llm_provider,
            model_id=model_id,
        ),
        BaseEvaluator(
            agent_name=AgentName.HIRING_MANAGER_EVALUATION,
            output_schema=HiringManagerEvaluationOutput,
            schema_version=HIRING_MANAGER_SCHEMA_VERSION,
            prompt_version=HIRING_MANAGER_PROMPT_VERSION,
            build_messages=build_hiring_manager_messages,
            should_run_fn=_hiring_manager_gating,
            llm_provider=llm_provider,
            model_id=model_id,
        ),
    ]
