from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.factory import get_active_provider, get_all_providers, get_default_model_for
from app.ai.schemas import GenerateResult, ModelInfo, ProviderStatus
from app.core.config import settings

router = APIRouter(prefix="/api/ai", tags=["ai"])


class TestGenerateRequest(BaseModel):
    model: str | None = None
    prompt: str = "Reply with one short sentence confirming you are responding."


@router.get("/status", response_model=ProviderStatus)
async def ai_status():
    """Status of whichever provider is currently active (Ollama unless
    cloud AI is explicitly enabled)."""
    provider = get_active_provider()
    return await provider.check_status()


@router.get("/providers", response_model=list[ProviderStatus])
async def ai_providers():
    """Status of every provider this build knows about, active or not --
    useful for deciding whether to enable cloud AI."""
    results = []
    for provider in get_all_providers():
        results.append(await provider.check_status())
    return results


@router.get("/models", response_model=list[ModelInfo])
async def ai_models():
    """List models available from the currently active provider."""
    provider = get_active_provider()
    return await provider.list_models()


@router.post("/test", response_model=GenerateResult)
async def ai_test(body: TestGenerateRequest):
    """Run a real test generation against the currently active provider."""
    provider = get_active_provider()
    model = body.model or get_default_model_for(provider)
    return await provider.generate(model=model, prompt=body.prompt)
