"""Every outbound HTTP call the app makes must set follow_redirects=False.
If this app ever calls an attacker-influenced URL and blindly follows
redirects, that's a DNS-rebinding / SSRF-via-redirect hole. These scanners
only record the Location header as metadata -- they never fetch it. This
test exists so that guarantee can't regress silently in a future edit."""

import pathlib
import re

BACKEND_ROOT = pathlib.Path(__file__).parent.parent / "app"

FILES_THAT_MAKE_HTTP_CALLS = [
    "recon/orchestrator.py",
    "scanners/security_headers.py",
    "scanners/reflected_input.py",
]


def test_every_httpx_client_disables_redirect_following():
    for rel_path in FILES_THAT_MAKE_HTTP_CALLS:
        path = BACKEND_ROOT / rel_path
        assert path.exists(), f"expected file not found: {path}"
        content = path.read_text()

        client_calls = re.findall(r"httpx\.(?:Client|AsyncClient)\([^)]*\)", content)
        assert client_calls, f"{rel_path} doesn't appear to construct an httpx client at all"

        for call in client_calls:
            assert "follow_redirects=False" in call, (
                f"{rel_path} constructs an httpx client without follow_redirects=False: {call!r}"
            )
