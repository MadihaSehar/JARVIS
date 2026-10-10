from typing import Optional
from pydantic import BaseModel


class ModelInfo(BaseModel):
    name: str
    size_bytes: Optional[int] = None
    parameter_size: Optional[str] = None
    quantization: Optional[str] = None


class ProviderStatus(BaseModel):
    provider: str
    installed: bool
    reachable: bool
    base_url: Optional[str] = None
    error: Optional[str] = None


class GenerateResult(BaseModel):
    provider: str
    model: str
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    eval_count: Optional[int] = None
    duration_ms: Optional[int] = None
