import httpx


def discover_subdomains_passive(domain: str, timeout: int = 15) -> set[str]:
    """Passive subdomain discovery via crt.sh certificate transparency logs.
    Makes no requests to the target itself, only to crt.sh's public API."""
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except (httpx.RequestError, httpx.HTTPStatusError, ValueError):
        return set()

    subdomains = set()
    for entry in data:
        name_value = entry.get("name_value", "")
        for name in name_value.split("\n"):
            name = name.strip().lstrip("*.").lower()
            if name and name.endswith(domain):
                subdomains.add(name)
    return subdomains
