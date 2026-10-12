from app.core.config import settings
from app.scanners.cors_misconfig import CorsMisconfigScanner
from app.scanners.info_disclosure import InfoDisclosureScanner
from app.scanners.open_redirect import OpenRedirectScanner
from app.scanners.reflected_input import ReflectedInputScanner
from app.scanners.security_headers import SecurityHeadersScanner

# New scanner providers register here. Each app start works fine even if a
# provider's underlying tool/dependency is unavailable, as long as the
# provider class itself can be constructed.
AVAILABLE_SCANNERS = {
    "security_headers": SecurityHeadersScanner(),
    "reflected_input": ReflectedInputScanner(),
    "open_redirect": OpenRedirectScanner(),
    "info_disclosure": InfoDisclosureScanner(),
    "cors_misconfig": CorsMisconfigScanner(),
}


def get_enabled_scanner_names() -> set[str]:
    """Which registered scanners are turned on, per ENABLED_SCANNERS in .env.
    An empty/unset value enables all registered scanners (fail-open on
    config, not on safety -- every scanner here is passive or safe-active)."""
    raw = (settings.enabled_scanners or "").strip()
    if not raw:
        return set(AVAILABLE_SCANNERS.keys())
    return {name.strip() for name in raw.split(",") if name.strip()}


def get_enabled_scanners() -> dict:
    enabled = get_enabled_scanner_names()
    return {name: s for name, s in AVAILABLE_SCANNERS.items() if name in enabled}
