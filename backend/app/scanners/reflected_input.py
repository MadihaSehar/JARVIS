import uuid

import httpx

from app.scanners.base import FindingCandidate, Scanner


class ReflectedInputScanner(Scanner):
    """Safe, non-destructive reflected-input probe. Sends a unique, harmless
    canary string as a query parameter and checks whether it comes back
    unescaped in the response body -- a standard differential-response
    technique for flagging potential reflected-input issues without ever
    submitting or executing any script payload."""

    name = "reflected_input"
    category = "Cross-site scripting"
    risk_level = "safe-active"

    PARAM_NAMES = ["q", "search", "id", "query", "name"]

    def run(self, url: str, timeout: int = 10) -> list[FindingCandidate]:
        canary = f"jarviscanary{uuid.uuid4().hex[:8]}"
        findings: list[FindingCandidate] = []

        try:
            with httpx.Client(timeout=timeout, follow_redirects=False) as client:
                client.get(url)
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

        for param in self.PARAM_NAMES:
            separator = "&" if "?" in url else "?"
            probe_url = f"{url}{separator}{param}={canary}"
            try:
                with httpx.Client(timeout=timeout, follow_redirects=False) as client:
                    resp = client.get(probe_url)
            except httpx.RequestError:
                continue

            if canary in resp.text:
                findings.append(
                    FindingCandidate(
                        category=self.category,
                        severity="medium",
                        confidence=0.5,
                        observation=(
                            f"A unique canary value submitted via the '{param}' parameter was "
                            "reflected unescaped in the response body. This alone does not confirm "
                            "an exploitable vulnerability -- it indicates the input is reflected and "
                            "warrants manual verification of context and output encoding."
                        ),
                        evidence={
                            "url": probe_url,
                            "parameter": param,
                            "canary": canary,
                            "status_code": resp.status_code,
                        },
                        remediation=(
                            "Ensure all reflected user input is properly output-encoded "
                            "for its context (HTML, attribute, JS, URL)."
                        ),
                        human_review_required=True,
                    )
                )

        return findings
