# Static priority order used when no AI provider is available. Deliberately
# simple and fully deterministic -- no model, no randomness, same output
# every time for the same input.
ASSET_TYPE_PRIORITY = {
    "http_service": 3,
    "subdomain": 2,
    "ip": 1,
}


def propose_deterministic(assets: list[dict], max_items: int = 10) -> list[dict]:
    ranked = sorted(
        assets,
        key=lambda a: ASSET_TYPE_PRIORITY.get(a["asset_type"], 0),
        reverse=True,
    )
    proposals = []
    for a in ranked[:max_items]:
        proposals.append(
            {
                "asset_value": a["value"],
                "rationale": (
                    f"Deterministic fallback: asset type '{a['asset_type']}' "
                    "ranked by static priority order (no AI provider available)."
                ),
                "confidence": 0.3,
            }
        )
    return proposals
