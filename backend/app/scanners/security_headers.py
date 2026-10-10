import httpx

from app.scanners.base import FindingCandidate, Scanner

EXPECTED_HEADERS = {
    "content-security-policy": (
        "Security misconfiguration",
        "medium",
        "No Content-Security-Policy header set, increasing exposure to injection-based attacks.",
    ),
    "x-frame-options": (
        "Security misconfiguration",
        "low",
        "No X-Frame-Options header set; the page may be vulnerable to clickjacking.",
    ),
    "x-content-type-options": (
        "Security misconfiguration",
        "low",
        "No X-Content-Type-Options header set; the browser may MIME-sniff responses.",
    ),
    "strict-transport-security": (
        "Security misconfiguration",
        "medium",
        "No Strict-Transport-Security header set on an HTTPS response.",
    ),
}


class SecurityHeadersScanner(Scanner):
    name = "security_headers"
    category = "Security misconfiguration"
    risk_level = "passive"

    def run(self, url: str, timeout: int = 10) -> list[FindingCandidate]:
        findings: list[FindingCandidate] = []
        try:
            with httpx.Client(timeout=timeout, follow_redirects=False) as client:
                resp = client.get(url)
        except httpx.RequestError as e:
            return [
                FindingCandidate(
                    category="Scanner error",
                    severity="info",
                    confidence=1.0,
                    observation=f"Could not connect to {url}: {e}",
                    evidence={"url": url, "error": str(e)},
                    human_review_required=False,
                )
            ]

        headers = {k.lower(): v for k, v in resp.headers.items()}

        for header, (category, severity, observation) in EXPECTED_HEADERS.items():
            if header == "strict-transport-security" and not url.startswith("https"):
                continue
            if header not in headers:
                findings.append(
                    FindingCandidate(
                        category=category,
                        severity=severity,
                        confidence=1.0,
                        observation=observation,
                        evidence={"url": url, "missing_header": header, "status_code": resp.status_code},
                        remediation=f"Set the '{header}' response header to an appropriate value.",
                        human_review_required=False,
                    )
                )

        server = headers.get("server")
        if server:
            findings.append(
                FindingCandidate(
                    category="Information disclosure",
                    severity="info",
                    confidence=0.6,
                    observation=f"Server header discloses software/version: '{server}'.",
                    evidence={"url": url, "server_header": server},
                    remediation="Suppress or genericize the Server header to reduce fingerprinting surface.",
                    human_review_required=True,
                )
            )

        try:
            cookies = resp.headers.get_list("set-cookie")
        except Exception:
            cookies = []
        for cookie in cookies:
            lowered = cookie.lower()
            missing = []
            if "secure" not in lowered and url.startswith("https"):
                missing.append("Secure")
            if "httponly" not in lowered:
                missing.append("HttpOnly")
            if missing:
                findings.append(
                    FindingCandidate(
                        category="Security misconfiguration",
                        severity="low",
                        confidence=0.9,
                        observation=f"Cookie set without {', '.join(missing)} attribute(s).",
                        evidence={"url": url, "cookie_header": cookie[:200]},
                        remediation=f"Set the {', '.join(missing)} attribute(s) on this cookie.",
                        human_review_required=False,
                    )
                )

        return findings
