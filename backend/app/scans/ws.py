import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.security import check_ws_api_key
from app.models.base import SessionLocal
from app.models.event import ScanEvent

router = APIRouter()

POLL_INTERVAL_SECONDS = 1.0


@router.websocket("/ws/scans/{scan_id}")
async def scan_events_ws(websocket: WebSocket, scan_id: str):
    """Streams scan events. A reconnecting client should first GET
    /api/scans/{id}/events for history, then open this for live updates --
    in practice this socket also backfills full history on connect, since
    it has no prior cursor the first time through the loop.

    If API_KEY is configured, the client must pass it as ?api_key=... --
    browsers can't set custom headers on a WebSocket handshake, so the
    header-based auth used elsewhere isn't available here."""
    provided_key = websocket.query_params.get("api_key")
    if not check_ws_api_key(provided_key):
        await websocket.close(code=4401)
        return

    await websocket.accept()
    last_seen = None
    try:
        while True:
            db = SessionLocal()
            try:
                stmt = select(ScanEvent).where(ScanEvent.scan_id == scan_id).order_by(ScanEvent.created_at)
                if last_seen is not None:
                    stmt = stmt.where(ScanEvent.created_at > last_seen)
                events = db.execute(stmt).scalars().all()
            finally:
                db.close()

            for e in events:
                await websocket.send_json(
                    {
                        "id": e.id,
                        "scan_id": e.scan_id,
                        "event_type": e.event_type,
                        "payload": e.payload,
                        "created_at": e.created_at.isoformat(),
                    }
                )
                last_seen = e.created_at

            await asyncio.sleep(POLL_INTERVAL_SECONDS)
    except WebSocketDisconnect:
        pass
