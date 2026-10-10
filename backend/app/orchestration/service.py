from sqlalchemy import select

from app.core.config import settings
from app.models.action_proposal import ActionProposal, ProposalStatus
from app.models.asset import Asset
from app.models.base import SessionLocal
from app.models.event import ScanEvent
from app.models.scan import Scan, ScanStatus
from app.orchestration import ai_planner, fallback, policy


def _emit(db, scan_id: str, event_type: str, payload: dict | None = None) -> None:
    db.add(ScanEvent(scan_id=scan_id, event_type=event_type, payload=payload or {}))
    db.commit()


def run_orchestration(scan_id: str) -> None:
    """Evidence-driven proposal generation for a scan. Runs as a background
    task with its own DB session. Nothing here executes any security check --
    it only proposes and records policy-gated priorities for Phase 6 to act on."""
    db = SessionLocal()
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return

        assets = db.execute(select(Asset).where(Asset.scan_id == scan_id)).scalars().all()
        asset_dicts = [{"id": a.id, "asset_type": a.asset_type, "value": a.value} for a in assets]
        value_to_id = {a.value: a.id for a in assets}

        existing = db.execute(
            select(ActionProposal).where(ActionProposal.scan_id == scan_id)
        ).scalars().all()
        budget_remaining = max(0, settings.orchestration_budget - len(existing))

        _emit(
            db, scan_id, "orchestration.started",
            {"asset_count": len(asset_dicts), "budget_remaining": budget_remaining},
        )

        if not asset_dicts:
            _emit(db, scan_id, "orchestration.no_assets", {})
            return

        if budget_remaining <= 0:
            _emit(db, scan_id, "orchestration.budget_exhausted", {})
            return

        proposals, ai_error = ai_planner.propose_with_ai(asset_dicts, max_items=budget_remaining)
        source = "ai"
        if proposals is None:
            _emit(db, scan_id, "orchestration.ai_unavailable", {"reason": ai_error})
            proposals = fallback.propose_deterministic(asset_dicts, max_items=budget_remaining)
            source = "fallback"

        _emit(
            db, scan_id, "orchestration.proposals_generated",
            {"count": len(proposals), "source": source},
        )

        for p in proposals:
            current = db.get(Scan, scan_id)
            if current is None or current.status not in (ScanStatus.RUNNING, ScanStatus.COMPLETED):
                _emit(db, scan_id, "orchestration.cancelled", {"status": current.status.value if current else "deleted"})
                break

            if budget_remaining <= 0:
                _emit(db, scan_id, "orchestration.budget_exhausted", {})
                break

            asset_id = value_to_id.get(p["asset_value"])
            result = policy.validate_proposal(
                action_type="prioritize_asset",
                confidence=p["confidence"],
                asset_in_scan=asset_id is not None,
                budget_remaining=budget_remaining,
            )

            db.add(
                ActionProposal(
                    scan_id=scan_id,
                    asset_id=asset_id,
                    action_type="prioritize_asset",
                    rationale=p["rationale"],
                    confidence=p["confidence"],
                    source=source,
                    status=ProposalStatus.APPROVED if result.approved else ProposalStatus.REJECTED,
                    policy_reason=result.reason,
                )
            )
            db.commit()
            budget_remaining -= 1

            _emit(
                db, scan_id, "orchestration.proposal.evaluated",
                {"asset_value": p["asset_value"], "approved": result.approved, "reason": result.reason},
            )

        _emit(db, scan_id, "orchestration.completed", {})
    finally:
        db.close()
