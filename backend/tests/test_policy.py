from app.orchestration.policy import validate_proposal


def test_approves_valid_proposal():
    result = validate_proposal("prioritize_asset", 0.8, True, 5)
    assert result.approved is True


def test_rejects_when_budget_exhausted():
    result = validate_proposal("prioritize_asset", 0.8, True, 0)
    assert result.approved is False
    assert "budget" in result.reason.lower()


def test_rejects_disallowed_action_type():
    # Even if the AI proposes something that sounds reasonable, anything
    # outside the hardcoded allowlist is rejected -- the AI cannot expand
    # its own authority.
    result = validate_proposal("delete_everything", 0.8, True, 5)
    assert result.approved is False


def test_rejects_confidence_above_range():
    result = validate_proposal("prioritize_asset", 1.5, True, 5)
    assert result.approved is False


def test_rejects_confidence_below_range():
    result = validate_proposal("prioritize_asset", -0.1, True, 5)
    assert result.approved is False


def test_accepts_confidence_boundaries():
    assert validate_proposal("prioritize_asset", 0.0, True, 5).approved is True
    assert validate_proposal("prioritize_asset", 1.0, True, 5).approved is True


def test_rejects_asset_outside_scan():
    result = validate_proposal("prioritize_asset", 0.8, False, 5)
    assert result.approved is False
    assert "scan" in result.reason.lower()


def test_budget_check_runs_before_other_checks():
    # Exhausted budget should fail fast regardless of how bad the other
    # fields are -- confirms the check order the orchestrator relies on.
    result = validate_proposal("not_a_real_action", 99.0, False, 0)
    assert result.approved is False
    assert "budget" in result.reason.lower()
