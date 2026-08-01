from pydantic import BaseModel

from app.ai.providers.base import T


class MockLLMProvider:
    """Deterministic LLM stub for tests and local development without OpenAI."""

    async def generate_structured(
        self,
        messages: list[dict[str, str]],
        response_model: type[T],
    ) -> T:
        _ = messages
        if not issubclass(response_model, BaseModel):
            raise TypeError("response_model must be a Pydantic BaseModel subclass")
        raise NotImplementedError("Use MockInterviewerLLMProvider for interviewer flows")
