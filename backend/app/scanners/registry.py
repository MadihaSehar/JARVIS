from app.scanners.reflected_input import ReflectedInputScanner
from app.scanners.security_headers import SecurityHeadersScanner

# New scanner providers register here. Each app start works fine even if a
# provider's underlying tool/dependency is unavailable, as long as the
# provider class itself can be constructed.
AVAILABLE_SCANNERS = {
    "security_headers": SecurityHeadersScanner(),
    "reflected_input": ReflectedInputScanner(),
}
