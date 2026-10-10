from sqlalchemy.orm import Session

from app.models.event import ScanEvent
from app.models.scan import Scan, ScanStatus

ALLOWED_TRANSITIONS: dict[ScanStatus, set[ScanStatus]] = {
    ScanStatus.PENDING: {ScanStatus.RUNNING, ScanStatus.CANCELLED},
    ScanStatus.RUNNING: {ScanStatus.PAUSED, ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED},
    ScanStatus.PAUSED: {ScanStatus.RUNNING, ScanStatus.CANCELLED},
    ScanStatus.COMPLETED: set(),
    ScanStatus.FAILED: set(),
    ScanStatus.CANCELLED: set(),
}


class InvalidTransition(Exception):
    def __init__(self, current: ScanStatus, target: ScanStatus):
        self.current = current
        self.target = target
        super().__init__(f"Cannot move scan from '{current.value}' to '{target.value}'")


def _emit(db: Session, scan: Scan, event_type: str, payload: dict | None = None) -> None:
    db.add(ScanEvent(scan_id=scan.id, event_type=event_type, payload=payload or {}))


def create_scan(db: Session, target: str, profile, scope_config: dict) -> Scan:
    scan = Scan(target=target, profile=profile, scope_config=scope_config)
    db.add(scan)
    db.flush()
    _emit(db, scan, "scan.created", {"target": target, "profile": profile.value})
    db.commit()
    db.refresh(scan)
    return scan


def transition(db: Session, scan: Scan, target_status: ScanStatus) -> Scan:
    allowed = ALLOWED_TRANSITIONS.get(scan.status, set())
    if target_status not in allowed:
        raise InvalidTransition(scan.status, target_status)

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    scan.status = target_status
    if target_status == ScanStatus.RUNNING and scan.started_at is None:
        scan.started_at = now
    if target_status in (ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED):
        scan.completed_at = now

    _emit(db, scan, f"scan.{target_status.value}", {})
    db.commit()
    db.refresh(scan)
    return scan
