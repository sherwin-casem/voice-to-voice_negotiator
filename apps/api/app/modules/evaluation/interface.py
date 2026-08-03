from typing import Protocol

from app.db.enums import AgentName
from app.modules.evaluation.schemas import AgentExecutionResult, EvaluationContext


class Evaluator(Protocol):
    """Common interface for specialist evaluation agents."""

    agent_name: AgentName
    schema_version: str
    prompt_version: str

    def should_run(self, context: EvaluationContext) -> tuple[bool, str | None]:
        """Return (True, None) to run, or (False, skip_reason) to skip."""

    async def evaluate(self, context: EvaluationContext) -> AgentExecutionResult: ...
