import time
from typing import Optional

import httpx

from app.ai.base import AIProvider
from app.ai.schemas import GenerateResult, ModelInfo, ProviderStatus
from app.core.config import settings

API_BASE = "https://api.openai.com/v1"


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self, api_key: Optional[str] = None, timeout_seconds: Optional[int] = None):
        self.api_key = api_key or settings.openai_api_key
        self.timeout_seconds = timeout_seconds or settings.cloud_ai_timeout_seconds

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    async def check_status(self) -> ProviderStatus:
        installed = bool(self.api_key)
        if not installed:
            return ProviderStatus(
                provider=self.name,
                installed=False,
                reachable=False,
                base_url=API_BASE,
                error="No OpenAI API key configured (set OPENAI_API_KEY in .env).",
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
                error="Connection to api.openai.com failed.",
            )
        except httpx.TimeoutException:
            return ProviderStatus(
                provider=self.name,
                installed=True,
                reachable=False,
                base_url=API_BASE,
                error="Timed out contacting the OpenAI API.",
            )
        except Exception as e:
            return ProviderStatus(
                provider=self.name, installed=True, reachable=False, base_url=API_BASE, error=str(e)
            )

    async def list_models(self) -> list[ModelInfo]:
        if not self.api_key:
            return []
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{API_BASE}/models", headers=self._headers())
            resp.raise_for_status()
            data = resp.json()
        models: list[ModelInfo] = []
        for m in data.get("data", []):
            model_id = m.get("id", "")
            if "gpt" in model_id or "o1" in model_id or "o3" in model_id:
                models.append(ModelInfo(name=model_id))
        return models

    async def generate(
        self, model: str, prompt: str, timeout_seconds: Optional[int] = None
    ) -> GenerateResult:
        if not self.api_key:
            return GenerateResult(
                provider=self.name,
                model=model,
                success=False,
                error="No OpenAI API key configured (set OPENAI_API_KEY in .env).",
            )
        timeout = timeout_seconds or self.timeout_seconds
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    f"{API_BASE}/chat/completions",
                    headers=self._headers(),
                    json={
                        "model": model,
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
            choice = (data.get("choices") or [{}])[0]
            text = (choice.get("message") or {}).get("content")
            usage = data.get("usage") or {}
            return GenerateResult(
                provider=self.name,
                model=model,
                success=True,
                response=text,
                eval_count=usage.get("completion_tokens"),
                duration_ms=duration_ms,
            )
        except httpx.ConnectError:
            return GenerateResult(
                provider=self.name,
                model=model,
                success=False,
                error="Connection to api.openai.com failed.",
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
