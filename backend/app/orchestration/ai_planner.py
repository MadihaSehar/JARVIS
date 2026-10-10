import asyncio
import json
import re

from app.ai.ollama_provider import OllamaProvider
from app.core.config import settings

PROMPT_TEMPLATE = """You are assisting a security reconnaissance tool. Given the discovered assets below, propose which ones deserve prioritized human review, and briefly explain why, based only on the evidence given. Do not claim anything is vulnerable. Output ONLY a JSON array, no other text, in exactly this shape:
[{{"asset_value": "<value>", "rationale": "<short reason citing the evidence>", "confidence": <number 0.0 to 1.0>}}]

Assets:
{asset_lines}
"""


def _extract_json_array(text: str) -> list:
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON array found in model output")
    return json.loads(match.group(0))


def propose_with_ai(assets: list[dict], max_items: int = 10):
    """Returns (proposals, error). proposals is None if the AI could not
    produce usable output -- the caller should fall back deterministically."""
    sample = assets[:max_items]
    if not sample:
        return [], None

    asset_lines = "\n".join(f"- {a['asset_type']}: {a['value']}" for a in sample)
    prompt = PROMPT_TEMPLATE.format(asset_lines=asset_lines)

    provider = OllamaProvider()

    async def _run():
        return await provider.generate(model=settings.ollama_default_model, prompt=prompt)

    try:
        result = asyncio.run(_run())
    except Exception as e:
        return None, f"AI call failed: {e}"

    if not result.success:
        return None, result.error or "AI generation failed"

    try:
        parsed = _extract_json_array(result.response or "")
    except (ValueError, json.JSONDecodeError) as e:
        return None, f"Could not parse AI output as JSON: {e}"

    cleaned = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        if "asset_value" not in item or "rationale" not in item:
            continue
        try:
            confidence = float(item.get("confidence", 0.5))
        except (TypeError, ValueError):
            confidence = 0.5
        cleaned.append(
            {
                "asset_value": str(item["asset_value"]),
                "rationale": str(item["rationale"])[:1000],
                "confidence": confidence,
            }
        )
    return cleaned, None
