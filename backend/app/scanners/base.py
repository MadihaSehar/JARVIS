from abc import ABC, abstractmethod


class FindingCandidate:
    def __init__(
        self,
        category: str,
        severity: str,
        confidence: float,
        observation: str,
        evidence: dict,
        remediation: str | None = None,
        human_review_required: bool = True,
    ):
        self.category = category
        self.severity = severity
        self.confidence = confidence
        self.observation = observation
        self.evidence = evidence
        self.remediation = remediation
        self.human_review_required = human_review_required


class Scanner(ABC):
    """Base interface every vulnerability-check provider implements. Kept
    deliberately simple: a scanner takes a target URL and returns candidate
    findings -- it never writes to the database or decides what's "true",
    that's the caller's job (dedup + policy + persistence)."""

    name: str
    category: str
    risk_level: str = "passive"  # "passive" or "safe-active"

    @abstractmethod
    def run(self, url: str, timeout: int = 10) -> list[FindingCandidate]:
        ...
