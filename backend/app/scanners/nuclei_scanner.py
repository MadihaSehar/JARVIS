"""Scanner wrapper around the external nuclei tool (template-based
exposure/vuln/tech-detection scanning). Converts nuclei's JSONL hits into
this project's FindingCandidate shape."""
from app.scanners.base import FindingCandidate, Scanner
from app.tools.nuclei import run_nuclei

_SEVERITY_MAP = {
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "info": "low",
    "unknown": "low",
}

_CONFIDENCE_MAP = {
    "critical": 0.8,
    "high": 0.8,
    "medium": 0.75,
    "low": 0.7,
    "info": 0.6,
    "unknown": 0.5,
}


class NucleiScanner(Scanner):
    """Runs curated nuclei templates (exposures, misconfiguration, tech
    detection, default-login) against the target. Safe-active: templates
    are restricted to this non-destructive tag set, never the full
    (much larger, more intrusive) default template catalog."""

    name = "nuclei"
    category = "External signature scan (nuclei)"
    risk_level = "safe-active"

    def run(self, url: str, timeout: int = 10) -> list[FindingCandidate]:
        # nuclei needs far more than the generic SCANNER_TIMEOUT (10s) the
        # caller passes in -- run_nuclei falls back to
        # settings.external_tool_timeout_seconds (120s) when given None.
        hits = run_nuclei(url, timeout=None)

        findings: list[FindingCandidate] = []
        for hit in hits:
            severity_key = (hit.get("severity") or "unknown").lower()
            severity = _SEVERITY_MAP.get(severity_key, "low")
            confidence = _CONFIDENCE_MAP.get(severity_key, 0.5)

            name = hit.get("name") or hit.get("template_id") or "Nuclei template match"
            tags = ", ".join(hit.get("tags") or []) or "none"

            findings.append(
                FindingCandidate(
                    category=self.category,
                    severity=severity,
                    confidence=confidence,
                    observation=(
                        f"Nuclei template '{hit.get('template_id', 'unknown')}' matched: {name}. "
                        f"Tags: {tags}."
                        + (f" {hit['description']}" if hit.get("description") else "")
                    ),
                    evidence={
                        "url": url,
                        "template_id": hit.get("template_id", ""),
                        "name": name,
                        "nuclei_severity": hit.get("severity", "unknown"),
                        "tags": hit.get("tags", []),
                        "matched_at": hit.get("matched_at", ""),
                        "type": hit.get("type", ""),
                        "extracted_results": hit.get("extracted_results", []),
                    },
                    remediation=None,
                    human_review_required=True,
                )
            )

        return findings
