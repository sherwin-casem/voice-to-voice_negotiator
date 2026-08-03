from app.ai.providers.factory import build_ai_providers
from app.config import Settings, settings
from app.modules.evaluation.agents.judge import JudgeAgent
from app.modules.evaluation.agents.registry import build_specialist_evaluators
from app.modules.evaluation.mock_llm import MockEvaluationLLMProvider
from app.modules.evaluation.service import EvaluationService


def build_evaluation_service(app_settings: Settings | None = None) -> EvaluationService:
    resolved = app_settings or settings

    if resolved.ai_provider == "mock":
        llm = MockEvaluationLLMProvider()
        model_id = "mock-structured"
    else:
        llm = build_ai_providers(resolved).structured
        model_id = resolved.openai_structured_model

    evaluators = build_specialist_evaluators(llm, model_id=model_id)
    judge = JudgeAgent(llm, model_id=model_id)
    return EvaluationService(evaluators, judge)


def get_evaluation_service() -> EvaluationService:
    return build_evaluation_service(settings)
