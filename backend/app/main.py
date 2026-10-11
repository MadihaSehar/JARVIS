from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.router import router as ai_router
from app.core.config import settings
from app.core.info import router as info_router
from app.orchestration.router import router as orchestration_router
from app.scanners.router import router as scanning_router
from app.scans.router import router as scans_router
from app.scans.ws import router as scans_ws_router
from app.reports.router import router as reports_router

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://192.168.56.105:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router)
app.include_router(scans_router)
app.include_router(orchestration_router)
app.include_router(scanning_router)
app.include_router(scans_ws_router)
app.include_router(info_router)
app.include_router(reports_router)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }
