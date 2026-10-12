"""Subfinder adapter: passive subdomain enumeration via subfinder's own
aggregated passive sources (crt.sh, VirusTotal-style sources, etc.)."""
from __future__ import annotations

import json
import logging

from app.tools.base import ExternalToolInfo, is_tool_installed, run_tool

logger = logging.getLogger(__name__)

BINARY = "subfinder"


def info() -> ExternalToolInfo:
    return ExternalToolInfo(
        name="subfinder",
        binary=BINARY,
        category="Subdomain enumeration",
        purpose="Passive subdomain discovery across many public sources",
        installed=is_tool_installed(BINARY),
    )


def run_subfinder(domain: str, timeout: int | None = None) -> list[str]:
    """Returns a deduplicated list of candidate subdomain hostnames.
    Never raises; returns [] on any failure (missing binary, timeout,
    bad output)."""
    result = run_tool(BINARY, ["-d", domain, "-silent", "-json"], timeout=timeout)
    if result is None:
        return []
    if result.returncode != 0 and not result.stdout.strip():
        logger.warning("subfinder exited %s for %s: %s", result.returncode, domain, result.stderr[:500])
        return []

    hosts: set[str] = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            host = obj.get("host")
        except (json.JSONDecodeError, AttributeError):
            host = line  # fall back: treat the raw line as a hostname
        if host:
            hosts.add(host.strip().lower())
    return sorted(hosts)
