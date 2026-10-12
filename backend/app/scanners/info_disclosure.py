import httpx

from app.scanners.base import FindingCandidate, Scanner

# A small, curated set of commonly-exposed sensitive paths -- deliberately
# short. This is not a brute-force wordlist scanner (that belongs in
# "Directory Discovery", not yet built, and would need its own rate
# limiting). Each path here is a single, specific, well-known mistake.
SENSITIVE_PATHS = [
    (".git/config", "git configuration file"),
    (".git/HEAD", "git repository metadata"),
    (".env", "environment/secrets file"),
    ("wp-config.php.bak", "WordPress config backup"),
    ("config.php.bak", "application config backup"),
    (".svn/entries", "Subversion metadata"),
    ("backup.zip", "backup archive"),
    (".DS_Store", "macOS directory metadata (can leak file listings)"),
]


class InfoDisclosureScanner(Scanner):
    """Passive-equivalent check: requests a small, curated list of
    well-known sensitive paths and flags any that return content instead
    of a 404/redirect. Never attempts to brute-force paths or guess
    credentials -- this is checking for specific, well-documented
    deployment mistakes."""

    name = "info_disclosure"
    category = "Information disclosure"
    risk_level = "safe-active"

    def run(self, url: str, timeout: int = 10) -> list[FindingCandidate]:
        findings: list[FindingCandidate] = []
        base = url.rstrip("/")

        for path, description in SENSITIVE_PATHS:
            probe_url = f"{base}/{path}"
            try:
                with httpx.Client(timeout=timeout, follow_redirects=False) as client:
                    resp = client.get(probe_url)
            except httpx.RequestError:
                continue

            if resp.status_code != 200:
                continue

            content_type = resp.headers.get("content-type", "")
            body_sample = resp.text[:2000] if "text" in content_type or content_type == "" else ""

            # Many servers return a 200 HTML page (SPA fallback, custom
            # 404) for any path. That's not an exposed file -- skip it.
            if "<html" in body_sample.lower() or "<!doctype html" in body_sample.lower():
                continue
            if not resp.content:
                continue

            findings.append(
                FindingCandidate(
                    category=self.category,
                    severity="high",
                    confidence=0.6,
                    observation=(
                        f"A request for '{path}' ({description}) returned HTTP 200 with "
                        f"{len(resp.content)} bytes of non-HTML content, suggesting this file "
                        "is actually being served rather than returning a 404. Manual "
                        "verification of the response content is recommended before concluding "
                        "this is a genuine exposure."
                    ),
                    evidence={
                        "url": probe_url,
                        "status_code": resp.status_code,
                        "content_type": content_type,
                        "content_length": len(resp.content),
                    },
                    remediation=(
                        f"Remove or block public access to {path}. Ensure build/deploy "
                        "processes never publish VCS metadata, backups, or env files into the "
                        "web root."
                    ),
                    human_review_required=True,
                )
            )

        return findings
