"""Katana adapter: web crawling for endpoint/route discovery. Crawls
only the given URL's own scope (katana's default host-based scope, -ns
is never passed) and is bounded by both depth and a hard page cap so a
single target can't turn into an unbounded crawl."""
from __future__ import annotations

import logging

from app.tools.base import ExternalToolInfo, is_tool_installed, run_tool

logger = logging.getLogger(__name__)

BINARY = "katana"

DEFAULT_DEPTH = 2
DEFAULT_MAX_PAGES = 100


def info() -> ExternalToolInfo:
    return ExternalToolInfo(
        name="katana",
        binary=BINARY,
        category="Endpoint discovery",
        purpose="Crawls a web app to discover endpoints/routes",
        installed=is_tool_installed(BINARY),
    )


def run_katana(
    url: str,
    timeout: int | None = None,
    depth: int = DEFAULT_DEPTH,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> list[str]:
    """Returns a deduplicated list of discovered endpoint URLs. Never
    raises; returns [] on any failure."""
    result = run_tool(
        BINARY,
        ["-u", url, "-silent", "-d", str(depth), "-mdp", str(max_pages)],
        timeout=timeout,
    )
    if result is None:
        return []
    if result.returncode not in (0, -1) and not result.stdout.strip():
        logger.warning("katana exited %s for %s: %s", result.returncode, url, result.stderr[:500])
        return []

    endpoints: set[str] = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith(("http://", "https://")):
            endpoints.add(line)
    return sorted(endpoints)
