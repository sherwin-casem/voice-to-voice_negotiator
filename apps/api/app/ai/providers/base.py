from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(Protocol):
    async def generate_structured(
        self,
        messages: list[dict[str, str]],
        response_model: type[T],
    ) -> T: ...
