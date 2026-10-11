import pytest

from app.scope.validator import (
    ScopeViolation,
    is_blocked_destination,
    is_in_scope,
    validate_target_format,
)


def test_valid_domain_passes():
    assert validate_target_format("example.com") == "example.com"


def test_valid_public_ip_passes():
    assert validate_target_format("8.8.8.8") == "8.8.8.8"


def test_rejects_private_ip():
    with pytest.raises(ScopeViolation):
        validate_target_format("192.168.1.1")


def test_rejects_loopback():
    with pytest.raises(ScopeViolation):
        validate_target_format("127.0.0.1")


def test_rejects_link_local():
    with pytest.raises(ScopeViolation):
        validate_target_format("169.254.1.1")


def test_rejects_cloud_metadata_ip():
    with pytest.raises(ScopeViolation):
        validate_target_format("169.254.169.254")


def test_rejects_cloud_metadata_hostname():
    with pytest.raises(ScopeViolation):
        validate_target_format("metadata.google.internal")


def test_rejects_malformed_target():
    with pytest.raises(ScopeViolation):
        validate_target_format("not a domain!!")


def test_accepts_url_and_extracts_hostname():
    assert validate_target_format("https://example.com/path") == "example.com"


def test_is_blocked_destination_covers_private_ranges():
    assert is_blocked_destination("10.0.0.5") is True
    assert is_blocked_destination("172.16.0.5") is True
    assert is_blocked_destination("192.168.0.5") is True
    assert is_blocked_destination("8.8.8.8") is False


def test_is_blocked_destination_ignores_plain_hostnames():
    # Not an IP and not a known metadata host -- scope decides, not this check.
    assert is_blocked_destination("www.example.com") is False


def test_is_in_scope_allows_target_and_subdomains():
    scope = {"allowed": ["example.com"]}
    assert is_in_scope("example.com", scope) is True
    assert is_in_scope("www.example.com", scope) is True
    assert is_in_scope("evil.com", scope) is False


def test_is_in_scope_exclusion_overrides_allow():
    scope = {"allowed": ["example.com"], "excluded": ["internal.example.com"]}
    assert is_in_scope("internal.example.com", scope) is False
    assert is_in_scope("www.example.com", scope) is True


def test_is_in_scope_empty_allowlist_denies_everything():
    assert is_in_scope("example.com", {}) is False


def test_is_in_scope_blocks_private_ip_even_if_allowlisted():
    # Scope config can't override the hard safety rail.
    scope = {"allowed": ["10.0.0.5"]}
    assert is_in_scope("10.0.0.5", scope) is False
