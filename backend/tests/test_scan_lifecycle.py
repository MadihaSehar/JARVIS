import pytest

from app.models.scan import ScanProfile, ScanStatus
from app.scans.service import InvalidTransition, create_scan, transition


def test_full_lifecycle(db_session):
    scan = create_scan(
        db_session, "lifecycle1.example", ScanProfile.STANDARD, {"allowed": ["lifecycle1.example"]}
    )
    assert scan.status == ScanStatus.PENDING
    assert scan.started_at is None
    assert scan.completed_at is None

    scan = transition(db_session, scan, ScanStatus.RUNNING)
    assert scan.status == ScanStatus.RUNNING
    assert scan.started_at is not None

    scan = transition(db_session, scan, ScanStatus.PAUSED)
    assert scan.status == ScanStatus.PAUSED

    scan = transition(db_session, scan, ScanStatus.RUNNING)
    assert scan.status == ScanStatus.RUNNING
    # started_at should not be reset on a second transition into RUNNING
    first_started_at = scan.started_at

    scan = transition(db_session, scan, ScanStatus.CANCELLED)
    assert scan.status == ScanStatus.CANCELLED
    assert scan.completed_at is not None
    assert scan.started_at == first_started_at


def test_pending_cannot_jump_to_completed(db_session):
    scan = create_scan(
        db_session, "lifecycle2.example", ScanProfile.STANDARD, {"allowed": ["lifecycle2.example"]}
    )
    with pytest.raises(InvalidTransition):
        transition(db_session, scan, ScanStatus.COMPLETED)


def test_terminal_states_accept_no_further_transitions(db_session):
    scan = create_scan(
        db_session, "lifecycle3.example", ScanProfile.STANDARD, {"allowed": ["lifecycle3.example"]}
    )
    scan = transition(db_session, scan, ScanStatus.RUNNING)
    scan = transition(db_session, scan, ScanStatus.COMPLETED)
    with pytest.raises(InvalidTransition):
        transition(db_session, scan, ScanStatus.RUNNING)
    with pytest.raises(InvalidTransition):
        transition(db_session, scan, ScanStatus.CANCELLED)


def test_scan_creation_emits_event(db_session):
    from sqlalchemy import select
    from app.models.event import ScanEvent

    scan = create_scan(
        db_session, "lifecycle4.example", ScanProfile.PASSIVE, {"allowed": ["lifecycle4.example"]}
    )
    events = db_session.execute(
        select(ScanEvent).where(ScanEvent.scan_id == scan.id)
    ).scalars().all()
    assert len(events) == 1
    assert events[0].event_type == "scan.created"
