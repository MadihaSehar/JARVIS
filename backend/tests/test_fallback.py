from app.orchestration.fallback import propose_deterministic


def test_ranks_http_service_above_subdomain_above_ip():
    assets = [
        {"asset_type": "ip", "value": "1.2.3.4"},
        {"asset_type": "http_service", "value": "https://a.example.com"},
        {"asset_type": "subdomain", "value": "a.example.com"},
    ]
    proposals = propose_deterministic(assets)
    assert [p["asset_value"] for p in proposals] == [
        "https://a.example.com",
        "a.example.com",
        "1.2.3.4",
    ]


def test_confidence_is_always_fixed_low_value():
    # The fallback never claims high confidence -- it's a static ranking,
    # not an assessment.
    assets = [{"asset_type": "ip", "value": "1.2.3.4"}]
    proposals = propose_deterministic(assets)
    assert proposals[0]["confidence"] == 0.3


def test_rationale_discloses_no_ai_was_used():
    assets = [{"asset_type": "ip", "value": "1.2.3.4"}]
    proposals = propose_deterministic(assets)
    assert "no ai provider available" in proposals[0]["rationale"].lower()


def test_respects_max_items():
    assets = [{"asset_type": "ip", "value": f"1.2.3.{i}"} for i in range(20)]
    proposals = propose_deterministic(assets, max_items=5)
    assert len(proposals) == 5


def test_unknown_asset_type_ranks_lowest_but_is_not_dropped():
    assets = [
        {"asset_type": "mystery_type", "value": "x"},
        {"asset_type": "ip", "value": "1.2.3.4"},
    ]
    proposals = propose_deterministic(assets)
    assert len(proposals) == 2
    assert proposals[-1]["asset_value"] == "x"


def test_empty_input_returns_empty_output():
    assert propose_deterministic([]) == []
