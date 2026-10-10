import socket
from datetime import datetime, timezone

import httpx

from app.models.asset import Asset
from app.models.base import SessionLocal
from app.models.event import ScanEvent
from app.models.scan import Scan, ScanStatus
from app.recon.dns_enum import enumerate_dns_records
from app.recon.subdomains import discover_subdomains_passive
from app.scope.validator import is_blocked_destination, is_in_scope


def _emit(db, scan_id: str, event_type: str, payload: dict | None = None) -> None:
    db.add(ScanEvent(scan_id=scan_id, event_type=event_type, payload=payload or {}))
    db.commit()


def _add_asset(db, scan_id: str, asset_type: str, value: str, meta: dict | None = None) -> None:
    db.add(Asset(scan_id=scan_id, asset_type=asset_type, value=value, meta=meta or {}))
    db.commit()


def run_recon(scan_id: str) -> None:
    """Full recon workflow for a scan. Runs as a background task with its
    own DB session (never reuses the request-scoped session)."""
    db = SessionLocal()
    try:
        scan = db.get(Scan, scan_id)
        if scan is None or scan.status != ScanStatus.RUNNING:
            return

        target = scan.target
        scope_config = scan.scope_config or {}

        _emit(db, scan_id, "recon.dns.started", {"target": target})
        try:
            dns_records = enumerate_dns_records(target)
            for record_type, values in dns_records.items():
                for v in values:
                    _add_asset(db, scan_id, f"dns_{record_type.lower()}", v, {"record_type": record_type})
            _emit(db, scan_id, "recon.dns.completed", {"record_count": sum(len(v) for v in dns_records.values())})
        except Exception as e:
            _emit(db, scan_id, "recon.dns.error", {"error": str(e)})

        _emit(db, scan_id, "recon.subdomains.started", {"target": target})
        in_scope_subs: list[str] = []
        try:
            discovered = discover_subdomains_passive(target)
            in_scope_subs = [s for s in discovered if is_in_scope(s, scope_config)]
            excluded_count = len(discovered) - len(in_scope_subs)
            for sub in in_scope_subs:
                _add_asset(db, scan_id, "subdomain", sub, {"source": "crt.sh"})
            _emit(
                db, scan_id, "recon.subdomains.completed",
                {"found": len(discovered), "in_scope": len(in_scope_subs), "excluded": excluded_count},
            )
        except Exception as e:
            _emit(db, scan_id, "recon.subdomains.error", {"error": str(e)})

        hosts_to_resolve = set(in_scope_subs) | {target}
        _emit(db, scan_id, "recon.resolution.started", {"host_count": len(hosts_to_resolve)})
        live_hosts: list[str] = []
        for host in hosts_to_resolve:
            try:
                infos = socket.getaddrinfo(host, None)
                ips = sorted({info[4][0] for info in infos})
            except socket.gaierror:
                continue
            for ip in ips:
                if is_blocked_destination(ip):
                    _emit(
                        db, scan_id, "scope.blocked",
                        {"host": host, "ip": ip, "reason": "private/reserved/metadata address"},
                    )
                    continue
                _add_asset(db, scan_id, "ip", ip, {"hostname": host})
                live_hosts.append(host)
        live_hosts = sorted(set(live_hosts))
        _emit(db, scan_id, "recon.resolution.completed", {"resolved": len(live_hosts)})

        _emit(db, scan_id, "recon.http.started", {"host_count": len(live_hosts)})
        for host in live_hosts:
            for scheme in ("https", "http"):
                url = f"{scheme}://{host}"
                try:
                    with httpx.Client(timeout=8, follow_redirects=False) as client:
                        resp = client.get(url)
                    meta = {
                        "status_code": resp.status_code,
                        "server": resp.headers.get("server"),
                        "scheme": scheme,
                    }
                    location = resp.headers.get("location")
                    if location:
                        meta["redirect_to"] = location
                    _add_asset(db, scan_id, "http_service", url, meta)
                    break
                except httpx.RequestError:
                    continue
        _emit(db, scan_id, "recon.http.completed", {})

        scan = db.get(Scan, scan_id)
        if scan and scan.status == ScanStatus.RUNNING:
            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.now(timezone.utc)
            db.commit()
            _emit(db, scan_id, "scan.completed", {})
    except Exception as e:
        scan = db.get(Scan, scan_id)
        if scan:
            scan.status = ScanStatus.FAILED
            scan.error = str(e)
            scan.completed_at = datetime.now(timezone.utc)
            db.commit()
            _emit(db, scan_id, "scan.failed", {"error": str(e)})
    finally:
        db.close()
