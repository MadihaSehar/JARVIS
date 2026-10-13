"""FFUF adapter: directory/file brute-forcing against a single target
URL. This is the one adapter in this project that deliberately
generates a high volume of requests, so safety here means conservative
defaults (thread count, a hard wall-clock cap via -maxtime) rather than
scope checks alone -- the caller is still responsible for scope/
blocklist checks on the target URL before ever calling this."""
from __future__ import annotations

import json
import logging

from app.tools.base import ExternalToolInfo, is_tool_installed, run_tool

logger = logging.getLogger(__name__)

BINARY = "ffuf"

DEFAULT_THREADS = 10
DEFAULT_MAXTIME = 60  # hard wall-clock cap in seconds, independent of wordlist size


def info() -> ExternalToolInfo:
    return ExternalToolInfo(
        name="ffuf",
        binary=BINARY,
        category="Directory/file discovery",
        purpose="Brute-forces directories/files against a target URL from a wordlist",
        installed=is_tool_installed(BINARY),
    )


def run_ffuf(
    base_url: str,
    wordlist_path: str,
    timeout: int | None = None,
    threads: int = DEFAULT_THREADS,
    maxtime: int = DEFAULT_MAXTIME,
) -> list[dict]:
    """Fuzzes base_url + '/FUZZ' against the given wordlist file. Returns
    a list of hit dicts: {"url", "status", "length", "redirect_to"}.
    Never raises; returns [] on any failure (missing binary/wordlist,
    timeout, bad output)."""
    target = base_url.rstrip("/") + "/FUZZ"
    outer_timeout = timeout or (maxtime + 30)

    result = run_tool(
        BINARY,
        [
            "-u", target,
            "-w", wordlist_path,
            "-json", "-s",
            "-t", str(threads),
            "-maxtime", str(maxtime),
        ],
        timeout=outer_timeout,
    )
    if result is None:
        return []
    if result.returncode not in (0, -1) and not result.stdout.strip():
        logger.warning("ffuf exited %s for %s: %s", result.returncode, target, result.stderr[:500])
        return []

    hits: list[dict] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        url = obj.get("url")
        if not url:
            continue
        hits.append(
            {
                "url": url,
                "status": obj.get("status"),
                "length": obj.get("length"),
                "redirect_to": obj.get("redirectlocation") or None,
            }
        )
    return hits
