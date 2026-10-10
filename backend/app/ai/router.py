from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.ollama_provider import OllamaProvider
from app.ai.schemas import GenerateResult, ModelInfo, ProviderStatus
from app.core.config import settings

router = APIRouter(prefix="/api/ai", tags=["ai"])


class TestGenerateRequest(BaseModel):
    model: str | None = None
    prompt: str = "Reply with one short sentence confirming you are responding."


@router.get("/status", response_model=ProviderStatus)
async def ai_status():
    """Is Ollama installed and is its API reachable right now."""
    provider = OllamaProvider()
    return await provider.check_status()


@router.get("/models", response_model=list[ModelInfo])
async def ai_models():
    """List locally available Ollama models."""
    provider = OllamaProvider()
    return await provider.list_models()


@router.post("/test", response_model=GenerateResult)
async def ai_test(body: TestGenerateRequest):
    """Run a real test generation against a model to confirm it actually works."""
    provider = OllamaProvider()
    model = body.model or settings.ollama_default_model
    return await provider.generate(model=model, prompt=body.prompt)
