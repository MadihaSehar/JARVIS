from app.ai.anthropic_provider import AnthropicProvider
from app.ai.base import AIProvider
from app.ai.ollama_provider import OllamaProvider
from app.ai.openai_provider import OpenAIProvider
from app.core.config import settings

CLOUD_PROVIDERS: dict[str, type[AIProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}


def get_active_provider() -> AIProvider:
    """The provider actually used for generation right now.

    Local-first by design: cloud is only used when the operator has
    explicitly flipped enable_cloud_ai=true AND picked a known provider.
    Any misconfiguration falls back to Ollama rather than silently
    failing closed.
    """
    if settings.enable_cloud_ai:
        provider_cls = CLOUD_PROVIDERS.get(settings.cloud_ai_provider)
        if provider_cls is not None:
            return provider_cls()
    return OllamaProvider()


def get_default_model_for(provider: AIProvider) -> str:
    if provider.name == "openai":
        return settings.openai_default_model
    if provider.name == "anthropic":
        return settings.anthropic_default_model
    return settings.ollama_default_model


def get_all_providers() -> list[AIProvider]:
    """Every provider this build knows how to talk to, for a status overview."""
    return [OllamaProvider(), OpenAIProvider(), AnthropicProvider()]
