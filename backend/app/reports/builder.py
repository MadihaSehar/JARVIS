from sqlalchemy import select

from app.models.asset import Asset
from app.models.base import SessionLocal
from app.models.event import ScanEvent
from app.models.finding import Finding
from app.models.scan import Scan


def build_report(scan_id: str) -> dict | None:
    """Gathers a scan's full picture -- metadata, assets, findings, and the
    event trail -- into one plain dict ready for any renderer. Returns None
    if the scan doesn't exist."""
    db = SessionLocal()
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return None

        assets = db.execute(
            select(Asset).where(Asset.scan_id == scan_id).order_by(Asset.discovered_at)
        ).scalars().all()
        findings = db.execute(
            select(Finding).where(Finding.scan_id == scan_id).order_by(Finding.created_at)
        ).scalars().all()
        events = db.execute(
            select(ScanEvent).where(ScanEvent.scan_id == scan_id).order_by(ScanEvent.created_at)
        ).scalars().all()

        severity_counts: dict[str, int] = {}
        for f in findings:
            severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

        asset_type_counts: dict[str, int] = {}
        for a in assets:
            asset_type_counts[a.asset_type] = asset_type_counts.get(a.asset_type, 0) + 1

        return {
            "scan": {
                "id": scan.id,
                "target": scan.target,
                "profile": scan.profile.value if hasattr(scan.profile, "value") else scan.profile,
                "status": scan.status.value if hasattr(scan.status, "value") else scan.status,
                "scope_config": scan.scope_config,
                "error": scan.error,
                "created_at": scan.created_at,
                "started_at": scan.started_at,
                "completed_at": scan.completed_at,
            },
            "summary": {
                "asset_count": len(assets),
                "finding_count": len(findings),
                "event_count": len(events),
                "findings_by_severity": severity_counts,
                "assets_by_type": asset_type_counts,
            },
            "assets": [
                {
                    "id": a.id,
                    "asset_type": a.asset_type,
                    "value": a.value,
                    "meta": a.meta,
                    "discovered_at": a.discovered_at,
                }
                for a in assets
            ],
            "findings": [
                {
                    "id": f.id,
                    "asset_id": f.asset_id,
                    "category": f.category,
                    "severity": f.severity,
                    "confidence": f.confidence,
                    "observation": f.observation,
                    "evidence": f.evidence,
                    "remediation": f.remediation,
                    "human_review_required": f.human_review_required,
                    "created_at": f.created_at,
                }
                for f in findings
            ],
            "events": [
                {
                    "event_type": e.event_type,
                    "payload": e.payload,
                    "created_at": e.created_at,
                }
                for e in events
            ],
        }
    finally:
        db.close()
