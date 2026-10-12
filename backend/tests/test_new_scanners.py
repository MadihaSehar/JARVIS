import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import pytest

from app.scanners.cors_misconfig import CANARY_ORIGIN, CorsMisconfigScanner
from app.scanners.info_disclosure import InfoDisclosureScanner
from app.scanners.open_redirect import CANARY_TARGET, OpenRedirectScanner


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # keep test output quiet

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        # Open-redirect behavior: if any query param's value is the canary
        # target, redirect to it unmodified (simulates a vulnerable app).
        for values in qs.values():
            if values and values[0] == CANARY_TARGET:
                self.send_response(302)
                self.send_header("Location", values[0])
                self.end_headers()
                return

        # Sensitive-path behavior: only /.git/config returns real content.
        if parsed.path == "/.git/config":
            body = b"[core]\n\trepositoryformatversion = 0\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Everything else: CORS-reflecting 200 response (also covers the
        # CORS scanner and the "no sensitive file here" case).
        origin = self.headers.get("Origin")
        self.send_response(200)
        if origin == CANARY_ORIGIN:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Content-Type", "text/html")
        body = b"<html><body>not found</body></html>"
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture(scope="module")
def test_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    thread.join()


def test_open_redirect_scanner_detects_reflected_target(test_server):
    scanner = OpenRedirectScanner()
    findings = scanner.run(test_server, timeout=5)
    assert len(findings) >= 1
    assert all(f.category == "Open redirect" for f in findings)
    assert any(f.evidence["location_header"] == CANARY_TARGET for f in findings)


def test_cors_misconfig_scanner_detects_reflected_origin_with_credentials(test_server):
    scanner = CorsMisconfigScanner()
    findings = scanner.run(test_server, timeout=5)
    assert len(findings) == 1
    assert findings[0].category == "CORS misconfiguration"
    assert findings[0].severity == "high"  # credentials=true makes this the serious case
    assert findings[0].evidence["access_control_allow_credentials"] is True


def test_info_disclosure_scanner_flags_exposed_git_config(test_server):
    scanner = InfoDisclosureScanner()
    findings = scanner.run(test_server, timeout=5)
    paths_flagged = [f.evidence["url"] for f in findings]
    assert any(p.endswith("/.git/config") for p in paths_flagged)


def test_info_disclosure_scanner_ignores_html_fallback_responses(test_server):
    # Every other sensitive path in this server returns the generic HTML
    # 404-lookalike page -- the scanner should not flag those as exposures.
    scanner = InfoDisclosureScanner()
    findings = scanner.run(test_server, timeout=5)
    non_git_findings = [f for f in findings if not f.evidence["url"].endswith("/.git/config")]
    assert non_git_findings == []


def test_scanners_handle_unreachable_target_gracefully():
    # Port 1 is reserved/unlikely to be listening -- should fail fast
    # with a connection error, never raise.
    unreachable = "http://127.0.0.1:1"
    assert OpenRedirectScanner().run(unreachable, timeout=2) == []
    assert CorsMisconfigScanner().run(unreachable, timeout=2) == []
    assert InfoDisclosureScanner().run(unreachable, timeout=2) == []
