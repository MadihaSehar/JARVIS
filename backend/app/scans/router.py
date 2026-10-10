from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.base import get_db
from app.models.event import ScanEvent
from app.models.finding import Finding
from app.models.scan import Scan, ScanStatus
from app.recon.orchestrator import run_recon
from app.scans import service
from app.scans.schemas import (
    AssetResponse,
    FindingResponse,
    ScanCreateRequest,
    ScanEventResponse,
    ScanResponse,
)

router = APIRouter(prefix="/api/scans", tags=["scans"])


def _get_scan_or_404(db: Session, scan_id: str) -> Scan:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.post("", response_model=ScanResponse, status_code=201)
def create_scan(body: ScanCreateRequest, db: Session = Depends(get_db)):
    scan = service.create_scan(db, body.target, body.profile, body.scope_config)
    return scan


@router.get("", response_model=list[ScanResponse])
def list_scans(
    status_filter: ScanStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    stmt = select(Scan).order_by(Scan.created_at.desc()).limit(limit)
    if status_filter is not None:
        stmt = stmt.where(Scan.status == status_filter)
    return db.execute(stmt).scalars().all()


@router.get("/{scan_id}", response_model=ScanResponse)
def get_scan(scan_id: str, db: Session = Depends(get_db)):
    return _get_scan_or_404(db, scan_id)


@router.post("/{scan_id}/start", response_model=ScanResponse)
def start_scan(scan_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    scan = _get_scan_or_404(db, scan_id)
    try:
        updated = service.transition(db, scan, ScanStatus.RUNNING)
    except service.InvalidTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    background_tasks.add_task(run_recon, scan_id)
    return updated


@router.post("/{scan_id}/pause", response_model=ScanResponse)
def pause_scan(scan_id: str, db: Session = Depends(get_db)):
    scan = _get_scan_or_404(db, scan_id)
    try:
        return service.transition(db, scan, ScanStatus.PAUSED)
    except service.InvalidTransition as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{scan_id}/resume", response_model=ScanResponse)
def resume_scan(scan_id: str, db: Session = Depends(get_db)):
    scan = _get_scan_or_404(db, scan_id)
    try:
        return service.transition(db, scan, ScanStatus.RUNNING)
    except service.InvalidTransition as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{scan_id}/cancel", response_model=ScanResponse)
def cancel_scan(scan_id: str, db: Session = Depends(get_db)):
    scan = _get_scan_or_404(db, scan_id)
    try:
        return service.transition(db, scan, ScanStatus.CANCELLED)
    except service.InvalidTransition as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{scan_id}/events", response_model=list[ScanEventResponse])
def get_scan_events(scan_id: str, db: Session = Depends(get_db)):
    _get_scan_or_404(db, scan_id)
    stmt = select(ScanEvent).where(ScanEvent.scan_id == scan_id).order_by(ScanEvent.created_at)
    return db.execute(stmt).scalars().all()


@router.get("/{scan_id}/assets", response_model=list[AssetResponse])
def get_scan_assets(scan_id: str, db: Session = Depends(get_db)):
    _get_scan_or_404(db, scan_id)
    stmt = select(Asset).where(Asset.scan_id == scan_id).order_by(Asset.discovered_at)
    return db.execute(stmt).scalars().all()


@router.get("/{scan_id}/findings", response_model=list[FindingResponse])
def get_scan_findings(scan_id: str, db: Session = Depends(get_db)):
    _get_scan_or_404(db, scan_id)
    stmt = select(Finding).where(Finding.scan_id == scan_id).order_by(Finding.created_at)
    return db.execute(stmt).scalars().all()
