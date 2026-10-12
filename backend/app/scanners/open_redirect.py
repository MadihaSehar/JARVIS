import httpx

from app.scanners.base import FindingCandidate, Scanner

CANARY_TARGET = "https://jarvis-redirect-canary.invalid/"


class OpenRedirectScanner(Scanner):
    """Safe, non-destructive open-redirect probe. Submits a harmless,
    clearly-fake external URL as common redirect-parameter names and
    checks whether the server echoes it back unmodified in a redirect
    Location header. Never follows the redirect (follow_redirects=False
    everywhere in this app) -- it only inspects the header the server
    would have sent a browser."""

    name = "open_redirect"
    category = "Open redirect"
    risk_level = "safe-active"

    PARAM_NAMES = ["url", "next", "redirect", "redirect_uri", "return", "returnTo", "dest", "continue"]

    def run(self, url: str, timeout: int = 10) -> list[FindingCandidate]:
        findings: list[FindingCandidate] = []

        for param in self.PARAM_NAMES:
            separator = "&" if "?" in url else "?"
            probe_url = f"{url}{separator}{param}={CANARY_TARGET}"
            try:
                with httpx.Client(timeout=timeout, follow_redirects=False) as client:
                    resp = client.get(probe_url)
            except httpx.RequestError:
                continue

            if resp.status_code in (301, 302, 303, 307, 308):
                location = resp.headers.get("location", "")
                if CANARY_TARGET.rstrip("/") in location:
                    findings.append(
                        FindingCandidate(
                            category=self.category,
                            severity="medium",
                            confidence=0.6,
                            observation=(
                                f"Submitting an external URL via the '{param}' parameter produced "
                                f"a {resp.status_code} redirect pointing to that same attacker-"
                                "controlled URL. This indicates the redirect target is not "
                                "validated against an allowlist, which can be used for phishing "
                                "or to bypass OAuth/SSO redirect checks."
                            ),
                            evidence={
                                "url": probe_url,
                                "parameter": param,
                                "status_code": resp.status_code,
                                "location_header": location,
                            },
                            remediation=(
                                "Validate redirect targets against an allowlist of known-safe "
                                "paths/hosts rather than redirecting to arbitrary user input."
                            ),
                            human_review_required=True,
                        )
                    )

        return findings
