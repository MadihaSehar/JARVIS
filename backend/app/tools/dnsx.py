"""dnsx adapter: fast bulk DNS resolution, used to validate which
candidate hostnames (from subfinder/amass) actually resolve, before
they are ever treated as live assets. This does not replace the
project's scope/blocklist checks -- it only filters out hostnames that
don't resolve at all; every resolved IP still goes through
is_blocked_destination() same as the existing manual resolution path."""
from __future__ import annotations

import json
import logging

from app.tools.base import ExternalToolInfo, is_tool_installed, run_tool

logger = logging.getLogger(__name__)

BINARY = "dnsx"


def info() -> ExternalToolInfo:
    return ExternalToolInfo(
        name="dnsx",
        binary=BINARY,
        category="DNS resolution",
        purpose="Fast bulk DNS resolution/validation of candidate hostnames",
        installed=is_tool_installed(BINARY),
    )


def run_dnsx(hostnames: list[str], timeout: int | None = None) -> dict[str, list[str]]:
    """Resolves a batch of hostnames to their A-record IPs. Returns a
    dict of hostname -> [ips] for hostnames that resolved; unresolved
    hostnames are simply absent from the result. Never raises; returns
    {} on any failure."""
    if not hostnames:
        return {}

    stdin_text = "\n".join(hostnames) + "\n"
    result = run_tool(BINARY, ["-silent", "-a", "-resp", "-json"], timeout=timeout, input_text=stdin_text)
    if result is None:
        return {}
    if result.returncode != 0 and not result.stdout.strip():
        logger.warning("dnsx exited %s: %s", result.returncode, result.stderr[:500])
        return {}

    resolved: dict[str, list[str]] = {}
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        host = obj.get("host")
        ips = obj.get("a") or []
        if host and ips:
            resolved.setdefault(host.strip().lower(), [])
            for ip in ips:
                if ip not in resolved[host.strip().lower()]:
                    resolved[host.strip().lower()].append(ip)
    return resolved
