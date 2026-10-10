from abc import ABC, abstractmethod
from typing import Optional
from app.ai.schemas import ModelInfo, ProviderStatus, GenerateResult


class AIProvider(ABC):
    """Base interface every AI provider (local or cloud) must implement.

    Keeping this abstract means new providers (OpenAI, Gemini, Anthropic)
    can be added later without touching the Ollama implementation or the
    API routes that consume it.
    """

    name: str

    @abstractmethod
    async def check_status(self) -> ProviderStatus:
        ...

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        ...

    @abstractmethod
    async def generate(
        self, model: str, prompt: str, timeout_seconds: Optional[int] = None
    ) -> GenerateResult:
        ...
