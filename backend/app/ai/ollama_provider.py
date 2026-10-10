import shutil
import time
from typing import Optional

import httpx

from app.ai.base import AIProvider
from app.ai.schemas import GenerateResult, ModelInfo, ProviderStatus
from app.core.config import settings


class OllamaProvider(AIProvider):
    name = "ollama"

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.ollama_timeout_seconds

    def _binary_installed(self) -> bool:
        return shutil.which("ollama") is not None

    async def check_status(self) -> ProviderStatus:
        installed = self._binary_installed()
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
            return ProviderStatus(
                provider=self.name,
                installed=installed,
                reachable=True,
                base_url=self.base_url,
            )
        except httpx.ConnectError:
            return ProviderStatus(
                provider=self.name,
                installed=installed,
                reachable=False,
                base_url=self.base_url,
                error="Connection refused. Is the Ollama service running? (systemctl status ollama)",
            )
        except httpx.TimeoutException:
            return ProviderStatus(
                provider=self.name,
                installed=installed,
                reachable=False,
                base_url=self.base_url,
                error="Timed out contacting the Ollama API.",
            )
        except Exception as e:
            return ProviderStatus(
                provider=self.name,
                installed=installed,
                reachable=False,
                base_url=self.base_url,
                error=str(e),
            )

    async def list_models(self) -> list[ModelInfo]:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{self.base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()

        models: list[ModelInfo] = []
        for m in data.get("models", []):
            details = m.get("details", {}) or {}
            models.append(
                ModelInfo(
                    name=m.get("name", "unknown"),
                    size_bytes=m.get("size"),
                    parameter_size=details.get("parameter_size"),
                    quantization=details.get("quantization_level"),
                )
            )
        return models

    async def generate(
        self,
        model: str,
        prompt: str,
        timeout_seconds: Optional[int] = None,
    ) -> GenerateResult:
        timeout = timeout_seconds or self.timeout_seconds
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": model, "prompt": prompt, "stream": False},
                )
            duration_ms = int((time.monotonic() - start) * 1000)

            if resp.status_code == 404:
                return GenerateResult(
                    provider=self.name,
                    model=model,
                    success=False,
                    error=f"Model '{model}' not found locally. Pull it first: ollama pull {model}",
                    duration_ms=duration_ms,
                )

            resp.raise_for_status()
            data = resp.json()
            return GenerateResult(
                provider=self.name,
                model=model,
                success=True,
                response=data.get("response"),
                eval_count=data.get("eval_count"),
                duration_ms=duration_ms,
            )
        except httpx.ConnectError:
            return GenerateResult(
                provider=self.name,
                model=model,
                success=False,
                error="Connection refused. Ollama service is unreachable.",
            )
        except httpx.TimeoutException:
            return GenerateResult(
                provider=self.name,
                model=model,
                success=False,
                error=(
                    f"Request timed out after {timeout}s. The model may still be "
                    "loading into memory, or the host may not have enough RAM for it."
                ),
            )
        except Exception as e:
            msg = str(e)
            if "memory" in msg.lower() or "oom" in msg.lower():
                return GenerateResult(
                    provider=self.name,
                    model=model,
                    success=False,
                    error=f"Possible insufficient-memory error from Ollama: {msg}",
                )
            return GenerateResult(
                provider=self.name, model=model, success=False, error=msg
            )
