"""Shared helpers for external recon/scanning tool adapters.

These wrap third-party CLI binaries (subfinder, amass, dnsx, katana,
ffuf, nuclei) that are not Python-native, unlike the scanners in
app/scanners/. Every adapter here is a thin, defensive subprocess
wrapper: it resolves the binary path, enforces a timeout, and never
raises on a missing binary or a non-zero exit -- callers get an empty
result plus a logged warning instead, so one missing tool never takes
down a whole scan.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ExternalToolInfo:
    name: str
    binary: str
    category: str
    purpose: str
    installed: bool


def resolve_binary(binary_name: str) -> str | None:
    """Find a binary on PATH first, then in the configured fallback dir
    (covers `go install`, which places binaries in ~/go/bin -- a
    directory that is not always on a service account's PATH)."""
    found = shutil.which(binary_name)
    if found:
        return found
    fallback = Path(settings.external_tools_bin_dir) / binary_name
    if fallback.is_file() and (fallback.stat().st_mode & 0o111):
        return str(fallback)
    return None


def is_tool_installed(binary_name: str) -> bool:
    return resolve_binary(binary_name) is not None


def run_tool(
    binary_name: str,
    args: list[str],
    timeout: int | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess | None:
    """Run an external tool defensively. Returns None (and logs a
    warning) if the binary is missing, the run times out, or it cannot
    be executed for any other OS-level reason. Never raises."""
    if not settings.external_tools_enabled:
        logger.info("external tools disabled via settings; skipping %s", binary_name)
        return None

    binary_path = resolve_binary(binary_name)
    if not binary_path:
        logger.warning("external tool '%s' not found on PATH or in %s", binary_name, settings.external_tools_bin_dir)
        return None

    effective_timeout = timeout or settings.external_tool_timeout_seconds
    try:
        return subprocess.run(
            [binary_path, *args],
            input=input_text,
            capture_output=True,
            text=True,
            timeout=effective_timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        # Some tools (amass, notably) can hang briefly after logically
        # finishing their work. If anything was captured before the
        # kill, salvage it as a completed process with returncode -1
        # rather than discarding real data.
        partial_stdout = e.stdout if isinstance(e.stdout, str) else (e.stdout.decode(errors="replace") if e.stdout else "")
        partial_stderr = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode(errors="replace") if e.stderr else "")
        if partial_stdout.strip():
            logger.warning(
                "external tool '%s' timed out after %ss but produced partial output; using it",
                binary_name, effective_timeout,
            )
            return subprocess.CompletedProcess(
                args=[binary_path, *args], returncode=-1, stdout=partial_stdout, stderr=partial_stderr,
            )
        logger.warning("external tool '%s' timed out after %ss with no output", binary_name, effective_timeout)
        return None
    except OSError as e:
        logger.warning("external tool '%s' failed to execute: %s", binary_name, e)
        return None
