from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(title=settings.app_name)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }
