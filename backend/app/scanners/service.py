import hashlib
from urllib.parse import urlparse

from sqlalchemy import select

from app.models.asset import Asset
from app.models.base import SessionLocal
from app.models.event import ScanEvent
from app.models.finding import Finding
from app.models.scan import Scan, ScanStatus
from app.scanners.registry import AVAILABLE_SCANNERS
from app.scope.validator import is_blocked_destination, is_in_scope

MAX_FINDINGS_PER_SCAN = 100
SCANNER_TIMEOUT = 10


def _emit(db, scan_id: str, event_type: str, payload: dict | None = None) -> None:
    db.add(ScanEvent(scan_id=scan_id, event_type=event_type, payload=payload or {}))
    db.commit()


def _dedup_key(scan_id: str, asset_value: str, category: str, observation: str) -> str:
    raw = f"{scan_id}|{asset_value}|{category}|{observation}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def run_security_tests(scan_id: str) -> None:
    """Runs every registered scanner against the scan's discovered HTTP
    services. Every target is re-checked against scope before testing --
    never trusts that an asset in the database is still authorized."""
    db = SessionLocal()
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return

        scope_config = scan.scope_config or {}

        http_assets = db.execute(
            select(Asset).where(Asset.scan_id == scan_id, Asset.asset_type == "http_service")
        ).scalars().all()

        existing_findings = db.execute(select(Finding).where(Finding.scan_id == scan_id)).scalars().all()
        budget_remaining = max(0, MAX_FINDINGS_PER_SCAN - len(existing_findings))
        seen_dedup_keys = {f.dedup_key for f in existing_findings if f.dedup_key}

        _emit(
            db, scan_id, "scanning.started",
            {"target_count": len(http_assets), "budget_remaining": budget_remaining},
        )

        if not http_assets:
            _emit(db, scan_id, "scanning.no_targets", {})
            return

        for asset in http_assets:
            current = db.get(Scan, scan_id)
            if current is None or current.status not in (ScanStatus.RUNNING, ScanStatus.COMPLETED):
                _emit(db, scan_id, "scanning.cancelled", {})
                break
            if budget_remaining <= 0:
                _emit(db, scan_id, "scanning.budget_exhausted", {})
                break

            url = asset.value
            hostname = urlparse(url).hostname or ""

            if not is_in_scope(hostname, scope_config):
                _emit(db, scan_id, "scanning.out_of_scope", {"url": url, "hostname": hostname})
                continue
            if is_blocked_destination(hostname):
                _emit(db, scan_id, "scanning.blocked", {"url": url})
                continue

            for scanner_name, scanner in AVAILABLE_SCANNERS.items():
                _emit(db, scan_id, "scanning.scanner.started", {"scanner": scanner_name, "url": url})
                try:
                    candidates = scanner.run(url, timeout=SCANNER_TIMEOUT)
                except Exception as e:
                    _emit(
                        db, scan_id, "scanning.scanner.error",
                        {"scanner": scanner_name, "url": url, "error": str(e)},
                    )
                    continue

                stored = 0
                for c in candidates:
                    if budget_remaining <= 0:
                        break
                    dedup_key = _dedup_key(scan_id, url, c.category, c.observation)
                    if dedup_key in seen_dedup_keys:
                        continue
                    seen_dedup_keys.add(dedup_key)

                    db.add(
                        Finding(
                            scan_id=scan_id,
                            asset_id=asset.id,
                            category=c.category,
                            severity=c.severity,
                            confidence=c.confidence,
                            observation=c.observation,
                            evidence=c.evidence,
                            remediation=c.remediation,
                            human_review_required=c.human_review_required,
                            dedup_key=dedup_key,
                        )
                    )
                    db.commit()
                    budget_remaining -= 1
                    stored += 1

                _emit(
                    db, scan_id, "scanning.scanner.completed",
                    {"scanner": scanner_name, "url": url, "candidates": len(candidates), "stored": stored},
                )

        _emit(db, scan_id, "scanning.completed", {})
    finally:
        db.close()
