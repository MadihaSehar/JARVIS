"""Amass adapter: passive subdomain enumeration (OWASP Amass). Passive
is the default mode as of amass v4 (no -active flag is ever passed, so
this never does live zone transfers or brute forcing against the
target's own infrastructure).

Amass v4 has no stable JSON flag for `enum`; its plain-text output is a
relationship graph ("source (Type) --> relation --> target (Type)"),
and in practice the process can keep running for a few seconds after
printing "The enumeration has finished" -- so this adapter passes
amass's own -timeout (in minutes) to bound the enumeration itself, and
relies on app.tools.base's timeout-salvage behavior to still capture
output if the outer subprocess timeout has to kill a lingering process.
"""
from __future__ import annotations

import logging
import re

from app.tools.base import ExternalToolInfo, is_tool_installed, run_tool

logger = logging.getLogger(__name__)

BINARY = "amass"
_FQDN_LINE_RE = re.compile(r"^(\S+)\s+\(FQDN\)")


def info() -> ExternalToolInfo:
    return ExternalToolInfo(
        name="amass",
        binary=BINARY,
        category="Subdomain enumeration",
        purpose="Passive subdomain discovery (OWASP Amass, passive mode only)",
        installed=is_tool_installed(BINARY),
    )


def run_amass(domain: str, timeout: int | None = None) -> list[str]:
    """Returns a deduplicated list of candidate subdomain hostnames that
    are the target domain itself or a subdomain of it (infrastructure
    hostnames amass discovers along the way, like upstream nameservers,
    are deliberately excluded -- they are not assets of the target).
    Never raises; returns [] on any failure."""
    domain = domain.strip().lower()
    effective_timeout = timeout or 120
    internal_minutes = max(1, effective_timeout // 60)
    # Give the outer kill a grace buffer beyond amass's own stated
    # timeout, since it can linger briefly after finishing.
    outer_timeout = effective_timeout + 30

    result = run_tool(
        BINARY,
        ["enum", "-d", domain, "-nocolor", "-timeout", str(internal_minutes)],
        timeout=outer_timeout,
    )
    if result is None:
        return []
    if result.returncode not in (0, -1):
        logger.warning("amass exited %s for %s: %s", result.returncode, domain, result.stderr[:500])
        return []

    hosts: set[str] = set()
    for line in result.stdout.splitlines():
        match = _FQDN_LINE_RE.match(line.strip())
        if not match:
            continue
        name = match.group(1).strip().lower().rstrip(".")
        if name == domain or name.endswith("." + domain):
            hosts.add(name)
    return sorted(hosts)
