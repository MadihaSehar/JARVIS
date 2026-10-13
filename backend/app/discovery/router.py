from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.discovery.service import run_discovery
from app.models.base import get_db
from app.models.scan import Scan, ScanStatus

router = APIRouter(prefix="/api/scans", tags=["discovery"])


@router.post("/{scan_id}/discover", status_code=202)
def trigger_discovery(scan_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.status not in (ScanStatus.RUNNING, ScanStatus.COMPLETED):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot run discovery on a scan in status '{scan.status.value}'. "
            "The scan must be running or completed (i.e. have discovered HTTP services).",
        )
    background_tasks.add_task(run_discovery, scan_id)
    return {"status": "discovery_started", "scan_id": scan_id}
