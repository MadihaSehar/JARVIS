from app.scanners.service import _dedup_key


def test_dedup_key_deterministic():
    k1 = _dedup_key("scan1", "https://a.com", "cat", "obs")
    k2 = _dedup_key("scan1", "https://a.com", "cat", "obs")
    assert k1 == k2


def test_dedup_key_differs_by_scan():
    k1 = _dedup_key("scan1", "https://a.com", "cat", "obs")
    k2 = _dedup_key("scan2", "https://a.com", "cat", "obs")
    assert k1 != k2


def test_dedup_key_differs_by_asset_value():
    k1 = _dedup_key("scan1", "https://a.com", "cat", "obs")
    k2 = _dedup_key("scan1", "https://b.com", "cat", "obs")
    assert k1 != k2


def test_dedup_key_differs_by_category():
    k1 = _dedup_key("scan1", "https://a.com", "cat1", "obs")
    k2 = _dedup_key("scan1", "https://a.com", "cat2", "obs")
    assert k1 != k2


def test_dedup_key_differs_by_observation():
    k1 = _dedup_key("scan1", "https://a.com", "cat", "obs1")
    k2 = _dedup_key("scan1", "https://a.com", "cat", "obs2")
    assert k1 != k2
