from fastapi import APIRouter

from app.core.config import settings
from app.scanners.registry import AVAILABLE_SCANNERS

router = APIRouter(prefix="/api", tags=["info"])


@router.get("/scanners")
async def list_scanners():
    return [
        {"name": name, "category": s.category, "risk_level": s.risk_level}
        for name, s in AVAILABLE_SCANNERS.items()
    ]


@router.get("/settings")
async def get_settings():
    """Non-secret configuration only -- never includes API keys."""
    return {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "database_url": settings.database_url.split("://")[0] + "://***",
        "ollama_base_url": settings.ollama_base_url,
        "ollama_default_model": settings.ollama_default_model,
        "orchestration_budget": settings.orchestration_budget,
        "enable_cloud_ai": settings.enable_cloud_ai,
    }
