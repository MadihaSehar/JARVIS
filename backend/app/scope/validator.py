import ipaddress
import re
import socket
from urllib.parse import urlparse

DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$"
)

BLOCKED_METADATA_HOSTS = {
    "169.254.169.254",
    "metadata.google.internal",
    "fd00:ec2::254",
}


class ScopeViolation(Exception):
    pass


def normalize_target(target: str) -> str:
    target = target.strip()
    if "://" in target:
        parsed = urlparse(target)
        return parsed.hostname or target
    return target.rstrip("/")


def is_valid_domain(value: str) -> bool:
    return bool(DOMAIN_RE.match(value))


def is_valid_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def is_blocked_destination(host_or_ip: str) -> bool:
    """Destinations always blocked regardless of scope config: private,
    loopback, link-local, reserved, multicast addresses and known cloud
    metadata endpoints."""
    if host_or_ip in BLOCKED_METADATA_HOSTS:
        return True
    try:
        ip = ipaddress.ip_address(host_or_ip)
    except ValueError:
        return False
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def resolve_ips(host: str) -> list[str]:
    """All addresses a hostname currently resolves to; empty if it doesn't
    resolve."""
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, UnicodeError):
        return []
    return sorted({info[4][0] for info in infos})


def resolves_to_blocked(host_or_ip: str) -> bool:
    """Like is_blocked_destination, but also resolves hostnames: blocked if
    the name is blocked itself or ANY address it resolves to is. A name
    with one public and one private address is blocked, since a client
    connecting by hostname may pick either. Called again right before
    each network step so a DNS answer that changes after recon (DNS
    rebinding) is caught at the point of use."""
    if is_blocked_destination(host_or_ip):
        return True
    if is_valid_ip(host_or_ip):
        return False
    return any(is_blocked_destination(ip) for ip in resolve_ips(host_or_ip))


def validate_target_format(target: str) -> str:
    """Validate format and reject always-blocked destinations. Returns the
    normalized hostname/IP. Raises ScopeViolation on failure."""
    host = normalize_target(target)
    if not (is_valid_domain(host) or is_valid_ip(host)):
        raise ScopeViolation(
            f"'{target}' is not a valid domain, hostname, or IP address"
        )
    if resolves_to_blocked(host):
        raise ScopeViolation(
            f"'{host}' resolves to a private, reserved, or metadata address "
            "and cannot be scanned"
        )
    return host


def is_in_scope(host_or_ip: str, scope_config: dict) -> bool:
    """Check a discovered host/IP against the scan's authorized scope.
    A domain in 'allowed' authorizes itself and all its subdomains."""
    if is_blocked_destination(host_or_ip):
        return False

    for pattern in scope_config.get("excluded", []):
        if host_or_ip == pattern or host_or_ip.endswith("." + pattern):
            return False

    allowed = scope_config.get("allowed", [])
    if not allowed:
        return False

    for pattern in allowed:
        if host_or_ip == pattern or host_or_ip.endswith("." + pattern):
            return True
    return False
