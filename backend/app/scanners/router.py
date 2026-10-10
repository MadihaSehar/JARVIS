from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.base import get_db
from app.models.scan import Scan, ScanStatus
from app.scanners.service import run_security_tests

router = APIRouter(prefix="/api/scans", tags=["scanning"])


@router.post("/{scan_id}/scan", status_code=202)
def trigger_security_scan(scan_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.status not in (ScanStatus.RUNNING, ScanStatus.COMPLETED):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot run security tests on a scan in status '{scan.status.value}'. "
            "The scan must be running or completed (i.e. have discovered HTTP services).",
        )
    background_tasks.add_task(run_security_tests, scan_id)
    return {"status": "security_scan_started", "scan_id": scan_id}
