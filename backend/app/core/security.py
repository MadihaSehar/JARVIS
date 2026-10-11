import secrets

from fastapi import Header, HTTPException, Query, status

from app.core.config import settings


def verify_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    api_key_qs: str | None = Query(default=None, alias="api_key"),
) -> None:
    """Gate for every HTTP route except /api/health. Accepts the key via
    header (used by the frontend's fetch wrapper) or query string (needed
    for plain <a href> downloads like report export, which can't set
    custom headers). If no API_KEY is configured, auth is a no-op -- the
    operator explicitly chose to run unauthenticated."""
    if not settings.api_key:
        return
    provided = x_api_key or api_key_qs
    if not provided or not secrets.compare_digest(provided, settings.api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")


def check_ws_api_key(provided: str | None) -> bool:
    """Same check for the WebSocket route, which can't use FastAPI's
    Depends()-based header/query injection before the handshake."""
    if not settings.api_key:
        return True
    if not provided:
        return False
    return secrets.compare_digest(provided, settings.api_key)
