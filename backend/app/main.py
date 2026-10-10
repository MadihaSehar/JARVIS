from fastapi import FastAPI

from app.ai.router import router as ai_router
from app.core.config import settings
from app.orchestration.router import router as orchestration_router
from app.scanners.router import router as scanning_router
from app.scans.router import router as scans_router

app = FastAPI(title=settings.app_name)

app.include_router(ai_router)
app.include_router(scans_router)
app.include_router(orchestration_router)
app.include_router(scanning_router)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }
