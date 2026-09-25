"""
OllamaTriage — identical contract to LLMTriage, but calls a local Ollama
container instead of a hosted API. No key, no external network, no PII
leaving the machine — the trade-off is speed and classification quality
on CPU, which is the whole point of comparing this against LLMTriage.
"""

import json

import httpx
from pydantic import ValidationError

from app.schemas import TriageResult
from app.providers.triage.llm import _SYSTEM_PROMPT


class OllamaTriage:
    name = "llm:ollama"

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url
        self.model = model

    async def triage(self, text: str, location: str) -> TriageResult:
        user_prompt = f"<complaint>{text}</complaint>\nLocation: {location}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    "format": "json",
                    "stream": False,
                },
            )
            response.raise_for_status()

        raw = response.json()["message"]["content"]
        parsed = json.loads(raw)

        try:
            return TriageResult(**parsed)
        except ValidationError as exc:
            raise ValueError(f"OllamaTriage: response failed schema validation: {exc}") from exc