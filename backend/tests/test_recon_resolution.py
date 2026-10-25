import socket

import httpx

from app.models.asset import Asset
from app.models.event import ScanEvent
from app.models.scan import ScanProfile, ScanStatus
from app.recon import orchestrator
from app.scans.service import create_scan, transition


def _fake_getaddrinfo(answers):
    def fake(host, port, *args, **kwargs):
        if host not in answers:
            raise socket.gaierror("no such host")
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 0)) for ip in answers[host]]
    return fake


def test_host_with_any_blocked_address_is_never_probed(db_session, monkeypatch):
    answers = {
        "mixed.example": ["93.184.216.34", "10.0.0.5"],
        "ok.mixed.example": ["93.184.216.35"],
    }
    monkeypatch.setattr(orchestrator.socket, "getaddrinfo", _fake_getaddrinfo(answers))
    monkeypatch.setattr(
        "app.scope.validator.resolve_ips", lambda host: sorted(answers.get(host, []))
    )
    monkeypatch.setattr(orchestrator, "enumerate_dns_records", lambda target: {})
    monkeypatch.setattr(orchestrator, "discover_subdomains_passive", lambda target: ["ok.mixed.example"])
    monkeypatch.setattr(orchestrator.settings, "external_tools_enabled", False)

    probed = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def get(self, url):
            probed.append(url)
            return httpx.Response(200, request=httpx.Request("GET", url))

    monkeypatch.setattr(orchestrator.httpx, "Client", FakeClient)

    scan = create_scan(
        db_session, "mixed.example", ScanProfile.STANDARD, {"allowed": ["mixed.example"]}
    )
    transition(db_session, scan, ScanStatus.RUNNING)
    orchestrator.run_recon(scan.id)

    assert probed == ["https://ok.mixed.example"]
    ip_assets = {
        a.value for a in db_session.query(Asset).filter_by(scan_id=scan.id, asset_type="ip")
    }
    assert ip_assets == {"93.184.216.35"}
    blocked = [
        e.payload for e in db_session.query(ScanEvent).filter_by(scan_id=scan.id, event_type="scope.blocked")
    ]
    assert {"host": "mixed.example", "ip": "10.0.0.5"}.items() <= blocked[0].items()
