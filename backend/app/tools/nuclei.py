"""Subprocess adapter for the nuclei CLI (template-based exposure/vuln scanner).

Scoped to a curated, safety-conscious tag set for speed and to stay
consistent with this project's safe-active, non-destructive philosophy.
Deliberately does NOT pass -severity: live testing showed that combined
with -tags it can produce zero output well within the timeout, while
tags-only (plus rate-limit/per-request-timeout) reliably completes.
"""
import json
import logging

from app.core.config import settings
from app.tools.base import run_tool

logger = logging.getLogger(__name__)

DEFAULT_TAGS = "exposures,misconfiguration,tech,default-login"
DEFAULT_RATE_LIMIT = 150
DEFAULT_REQUEST_TIMEOUT = 5


def run_nuclei(url: str, timeout: int | None = None) -> list[dict]:
    """Run nuclei against a single URL and return parsed JSONL hits.

    Each dict has: template_id, name, severity, tags, description,
    matched_at, type, extracted_results, curl_command.
    Returns [] on any failure (missing binary, timeout, parse errors) --
    never raises.
    """
    effective_timeout = timeout or settings.external_tool_timeout_seconds
    args = [
        "-u", url,
        "-jsonl",
        "-silent",
        "-tags", DEFAULT_TAGS,
        "-rate-limit", str(DEFAULT_RATE_LIMIT),
        "-timeout", str(DEFAULT_REQUEST_TIMEOUT),
    ]

    result = run_tool("nuclei", args, timeout=effective_timeout)
    if result is None or result.returncode not in (0, -1):
        return []

    hits = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            logger.warning("nuclei: skipping malformed JSON line")
            continue

        info = data.get("info", {}) or {}
        hits.append({
            "template_id": data.get("template-id", ""),
            "name": info.get("name", ""),
            "severity": info.get("severity", "info"),
            "tags": info.get("tags", []),
            "description": info.get("description", ""),
            "matched_at": data.get("matched-at") or data.get("url", ""),
            "type": data.get("type", ""),
            "extracted_results": data.get("extracted-results", []),
            "curl_command": data.get("curl-command", ""),
        })

    return hits
