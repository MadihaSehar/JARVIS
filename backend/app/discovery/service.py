"""Endpoint discovery (katana) and directory/file discovery (ffuf)
against a scan's already-discovered HTTP services. Mirrors the
structure of app.scanners.service.run_security_tests: every target is
re-checked against scope before use, progress is emitted as scan
events, and one target's failure never aborts the others."""
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select

from app.core.config import settings
from app.models.asset import Asset
from app.models.base import SessionLocal
from app.models.event import ScanEvent
from app.models.scan import Scan, ScanStatus
from app.scope.validator import is_blocked_destination, is_in_scope
from app.tools.ffuf import run_ffuf
from app.tools.katana import run_katana

DEFAULT_WORDLIST = str(Path(__file__).parent / "wordlists" / "common.txt")
MAX_ENDPOINTS_PER_TARGET = 200
MAX_DIRECTORY_HITS_PER_TARGET = 100


def _emit(db, scan_id: str, event_type: str, payload: dict | None = None) -> None:
    db.add(ScanEvent(scan_id=scan_id, event_type=event_type, payload=payload or {}))
    db.commit()


def _add_asset(db, scan_id: str, asset_type: str, value: str, meta: dict | None = None) -> None:
    db.add(Asset(scan_id=scan_id, asset_type=asset_type, value=value, meta=meta or {}))
    db.commit()


def run_discovery(scan_id: str) -> None:
    db = SessionLocal()
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return

        scope_config = scan.scope_config or {}
        wordlist_path = settings.ffuf_wordlist_path or DEFAULT_WORDLIST

        http_assets = db.execute(
            select(Asset).where(Asset.scan_id == scan_id, Asset.asset_type == "http_service")
        ).scalars().all()

        _emit(db, scan_id, "discovery.started", {"target_count": len(http_assets)})

        if not http_assets:
            _emit(db, scan_id, "discovery.no_targets", {})
            return

        if not settings.external_tools_enabled:
            _emit(db, scan_id, "discovery.disabled", {"reason": "external_tools_enabled is false"})
            return

        for asset in http_assets:
            current = db.get(Scan, scan_id)
            if current is None or current.status not in (ScanStatus.RUNNING, ScanStatus.COMPLETED):
                _emit(db, scan_id, "discovery.cancelled", {})
                break

            url = asset.value
            hostname = urlparse(url).hostname or ""

            if not is_in_scope(hostname, scope_config):
                _emit(db, scan_id, "discovery.out_of_scope", {"url": url, "hostname": hostname})
                continue
            if is_blocked_destination(hostname):
                _emit(db, scan_id, "discovery.blocked", {"url": url})
                continue

            _emit(db, scan_id, "discovery.katana.started", {"url": url})
            try:
                endpoints = run_katana(url, timeout=settings.external_tool_timeout_seconds)
            except Exception as e:
                _emit(db, scan_id, "discovery.katana.error", {"url": url, "error": str(e)})
                endpoints = []
            stored = 0
            for ep in endpoints[:MAX_ENDPOINTS_PER_TARGET]:
                ep_hostname = urlparse(ep).hostname or ""
                if not is_in_scope(ep_hostname, scope_config) or is_blocked_destination(ep_hostname):
                    continue
                _add_asset(db, scan_id, "endpoint", ep, {"source": "katana", "parent": url})
                stored += 1
            _emit(db, scan_id, "discovery.katana.completed", {"url": url, "found": len(endpoints), "stored": stored})

            _emit(db, scan_id, "discovery.ffuf.started", {"url": url})
            try:
                hits = run_ffuf(url, wordlist_path, timeout=settings.external_tool_timeout_seconds)
            except Exception as e:
                _emit(db, scan_id, "discovery.ffuf.error", {"url": url, "error": str(e)})
                hits = []
            stored = 0
            for hit in hits[:MAX_DIRECTORY_HITS_PER_TARGET]:
                hit_hostname = urlparse(hit["url"]).hostname or ""
                if not is_in_scope(hit_hostname, scope_config) or is_blocked_destination(hit_hostname):
                    continue
                _add_asset(
                    db, scan_id, "directory", hit["url"],
                    {"source": "ffuf", "parent": url, "status": hit["status"], "length": hit["length"], "redirect_to": hit["redirect_to"]},
                )
                stored += 1
            _emit(db, scan_id, "discovery.ffuf.completed", {"url": url, "found": len(hits), "stored": stored})

        _emit(db, scan_id, "discovery.completed", {})
    finally:
        db.close()
