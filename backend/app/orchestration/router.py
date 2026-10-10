from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.action_proposal import ActionProposal
from app.models.base import get_db
from app.models.scan import Scan, ScanStatus
from app.orchestration.schemas import ActionProposalResponse
from app.orchestration.service import run_orchestration

router = APIRouter(prefix="/api/scans", tags=["orchestration"])


@router.post("/{scan_id}/orchestrate", status_code=202)
def orchestrate_scan(scan_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.status not in (ScanStatus.RUNNING, ScanStatus.COMPLETED):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot orchestrate a scan in status '{scan.status.value}'. "
            "The scan must be running or completed (i.e. have discovered assets).",
        )
    background_tasks.add_task(run_orchestration, scan_id)
    return {"status": "orchestration_started", "scan_id": scan_id}


@router.get("/{scan_id}/proposals", response_model=list[ActionProposalResponse])
def get_scan_proposals(scan_id: str, db: Session = Depends(get_db)):
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    stmt = (
        select(ActionProposal)
        .where(ActionProposal.scan_id == scan_id)
        .order_by(ActionProposal.created_at)
    )
    return db.execute(stmt).scalars().all()
