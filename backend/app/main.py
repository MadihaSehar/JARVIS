from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.router import router as ai_router
from app.core.config import settings
from app.core.info import router as info_router
from app.discovery.router import router as discovery_router
from app.core.security import verify_api_key
from app.orchestration.router import router as orchestration_router
from app.reports.router import router as reports_router
from app.scanners.router import router as scanning_router
from app.scans.router import router as scans_router
from app.scans.ws import router as scans_ws_router

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://192.168.56.105:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not settings.api_key:
    import logging

    logging.getLogger("uvicorn.error").warning(
        "API_KEY is not set -- the API is running UNAUTHENTICATED. "
        "Set API_KEY in .env before exposing this beyond localhost."
    )

_auth = [Depends(verify_api_key)]

app.include_router(ai_router, dependencies=_auth)
app.include_router(scans_router, dependencies=_auth)
app.include_router(orchestration_router, dependencies=_auth)
app.include_router(scanning_router, dependencies=_auth)
app.include_router(discovery_router, dependencies=_auth)
app.include_router(scans_ws_router)  # WebSocket auth is handled inside the handler
app.include_router(info_router, dependencies=_auth)
app.include_router(reports_router, dependencies=_auth)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "auth_enabled": bool(settings.api_key),
    }
