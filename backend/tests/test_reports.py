from app.models.asset import Asset
from app.models.finding import Finding
from app.models.scan import ScanProfile, ScanStatus
from app.reports.builder import build_report
from app.reports.renderers import to_html, to_json, to_markdown
from app.scans.service import create_scan, transition


def test_build_report_returns_none_for_missing_scan(db_session):
    assert build_report("does-not-exist") is None


def _seed_scan_with_finding(db_session):
    scan = create_scan(
        db_session, "report-test.example", ScanProfile.STANDARD, {"allowed": ["report-test.example"]}
    )
    scan = transition(db_session, scan, ScanStatus.RUNNING)

    asset = Asset(scan_id=scan.id, asset_type="http_service", value="https://report-test.example")
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)

    finding = Finding(
        scan_id=scan.id,
        asset_id=asset.id,
        category="Security misconfiguration",
        severity="medium",
        confidence=0.9,
        observation="Missing X-Frame-Options header",
        evidence={"header": "x-frame-options"},
        remediation="Add the header",
        human_review_required=False,
        dedup_key="testkey123",
    )
    db_session.add(finding)
    db_session.commit()
    return scan


def test_build_report_summary_counts(db_session):
    scan = _seed_scan_with_finding(db_session)
    data = build_report(scan.id)
    assert data is not None
    assert data["summary"]["asset_count"] == 1
    assert data["summary"]["finding_count"] == 1
    assert data["summary"]["findings_by_severity"] == {"medium": 1}
    assert data["summary"]["assets_by_type"] == {"http_service": 1}


def test_json_renderer_contains_target_and_is_valid_json(db_session):
    import json

    scan = _seed_scan_with_finding(db_session)
    data = build_report(scan.id)
    rendered = to_json(data)
    parsed = json.loads(rendered)
    assert parsed["scan"]["target"] == "report-test.example"


def test_markdown_renderer_contains_finding_text(db_session):
    scan = _seed_scan_with_finding(db_session)
    data = build_report(scan.id)
    rendered = to_markdown(data)
    assert "# J.A.R.V.I.S. Scan Report: report-test.example" in rendered
    assert "Missing X-Frame-Options header" in rendered
    assert "[MEDIUM]" in rendered


def test_html_renderer_escapes_and_contains_finding(db_session):
    scan = _seed_scan_with_finding(db_session)
    data = build_report(scan.id)
    rendered = to_html(data)
    assert "report-test.example" in rendered
    assert "Missing X-Frame-Options header" in rendered
    assert "<html>" in rendered


def test_html_renderer_escapes_html_in_observation(db_session):
    # A finding observation containing markup must not break out of the
    # page -- this is operator-facing output rendered in a real browser.
    scan = create_scan(
        db_session, "xss-report-test.example", ScanProfile.STANDARD, {"allowed": ["xss-report-test.example"]}
    )
    finding = Finding(
        scan_id=scan.id,
        category="test",
        severity="low",
        confidence=0.5,
        observation="<script>alert(1)</script>",
        evidence={},
        human_review_required=False,
    )
    db_session.add(finding)
    db_session.commit()

    data = build_report(scan.id)
    rendered = to_html(data)
    assert "<script>alert(1)</script>" not in rendered
    assert "&lt;script&gt;" in rendered
