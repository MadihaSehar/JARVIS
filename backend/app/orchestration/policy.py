ALLOWED_ACTION_TYPES = {"prioritize_asset"}

MIN_CONFIDENCE = 0.0
MAX_CONFIDENCE = 1.0


class PolicyResult:
    def __init__(self, approved: bool, reason: str):
        self.approved = approved
        self.reason = reason


def validate_proposal(
    action_type: str,
    confidence: float,
    asset_in_scan: bool,
    budget_remaining: int,
) -> PolicyResult:
    """Deterministic policy gate. The AI's rationale is never trusted on its
    own -- every proposal must pass these hard rules regardless of what the
    model said or how confident it claimed to be."""
    if budget_remaining <= 0:
        return PolicyResult(False, "Scan action budget exhausted")
    if action_type not in ALLOWED_ACTION_TYPES:
        return PolicyResult(False, f"Action type '{action_type}' is not in the allowed registry")
    if not (MIN_CONFIDENCE <= confidence <= MAX_CONFIDENCE):
        return PolicyResult(False, f"Confidence {confidence} out of valid range [0,1]")
    if not asset_in_scan:
        return PolicyResult(False, "Referenced asset does not belong to this scan")
    return PolicyResult(True, "Passed all policy checks")
