import time
from typing import Optional

import httpx

from app.ai.base import AIProvider
from app.ai.schemas import GenerateResult, ModelInfo, ProviderStatus
from app.core.config import settings

API_BASE = "https://api.anthropic.com/v1"
ANTHROPIC_VERSION = "2023-06-01"

# Fallback list used only if the live /v1/models lookup fails but the key
# itself is valid -- keeps the UI useful even if that endpoint changes.
FALLBACK_MODELS = [
    "claude-sonnet-5",
    "claude-opus-5-5",
    "claude-haiku-5-5",
]


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def __init__(self, api_key: Optional[str] = None, timeout_seconds: Optional[int] = None):
        self.api_key = api_key or settings.anthropic_api_key
        self.timeout_seconds = timeout_seconds or settings.cloud_ai_timeout_seconds

    def _headers(self) -> dict:
        return {
            "x-api-key": self.api_key or "",
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

    async def check_status(self) -> ProviderStatus:
        installed = bool(self.api_key)
        if not installed:
            return ProviderStatus(
                provider=self.name,
                installed=False,
                reachable=False,
                base_url=API_BASE,
                error="No Anthropic API key configured (set ANTHROPIC_API_KEY in .env).",
            )
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{API_BASE}/models", headers=self._headers())
            if resp.status_code == 401:
                return ProviderStatus(
                    provider=self.name,
                    installed=True,
                    reachable=False,
                    base_url=API_BASE,
                    error="API key was rejected (401 Unauthorized).",
                )
            resp.raise_for_status()
            return ProviderStatus(
                provider=self.name, installed=True, reachable=True, base_url=API_BASE
            )
        except httpx.ConnectError:
            return ProviderStatus(
                provider=self.name,
                installed=True,
                reachable=False,
                base_url=API_BASE,
                error="Connection to api.anthropic.com failed.",
            )
        except httpx.TimeoutException:
            return ProviderStatus(
                provider=self.name,
                installed=True,
                reachable=False,
                base_url=API_BASE,
                error="Timed out contacting the Anthropic API.",
            )
        except Exception as e:
            return ProviderStatus(
                provider=self.name, installed=True, reachable=False, base_url=API_BASE, error=str(e)
            )

    async def list_models(self) -> list[ModelInfo]:
        if not self.api_key:
            return []
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{API_BASE}/models", headers=self._headers())
                resp.raise_for_status()
                data = resp.json()
            models = [ModelInfo(name=m.get("id", "unknown")) for m in data.get("data", [])]
            if models:
                return models
        except Exception:
            pass
        return [ModelInfo(name=m) for m in FALLBACK_MODELS]

    async def generate(
        self, model: str, prompt: str, timeout_seconds: Optional[int] = None
    ) -> GenerateResult:
        if not self.api_key:
            return GenerateResult(
                provider=self.name,
                model=model,
                success=False,
                error="No Anthropic API key configured (set ANTHROPIC_API_KEY in .env).",
            )
        timeout = timeout_seconds or self.timeout_seconds
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    f"{API_BASE}/messages",
                    headers=self._headers(),
                    json={
                        "model": model,
                        "max_tokens": 1024,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
            duration_ms = int((time.monotonic() - start) * 1000)

            if resp.status_code == 401:
                return GenerateResult(
                    provider=self.name,
                    model=model,
                    success=False,
                    error="API key was rejected (401 Unauthorized).",
                    duration_ms=duration_ms,
                )
            if resp.status_code == 404:
                return GenerateResult(
                    provider=self.name,
                    model=model,
                    success=False,
                    error=f"Model '{model}' not found or not available to this account.",
                    duration_ms=duration_ms,
                )

            resp.raise_for_status()
            data = resp.json()
            blocks = data.get("content") or []
            text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
            usage = data.get("usage") or {}
            return GenerateResult(
                provider=self.name,
                model=model,
                success=True,
                response=text,
                eval_count=usage.get("output_tokens"),
                duration_ms=duration_ms,
            )
        except httpx.ConnectError:
            return GenerateResult(
                provider=self.name,
                model=model,
                success=False,
                error="Connection to api.anthropic.com failed.",
            )
        except httpx.TimeoutException:
            return GenerateResult(
                provider=self.name,
                model=model,
                success=False,
                error=f"Request timed out after {timeout}s.",
            )
        except Exception as e:
            return GenerateResult(provider=self.name, model=model, success=False, error=str(e))
