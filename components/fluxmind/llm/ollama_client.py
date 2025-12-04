from __future__ import annotations

from typing import Sequence

import httpx

from .interfaces import LLMClient, LLMMessage


class OllamaClient(LLMClient):
    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=60.0)

    async def generate(
        self,
        messages: Sequence[LLMMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        payload = {
            "model": model or self._model,
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
        }
        if temperature is not None:
            payload["options"] = payload.get("options", {})
            payload["options"]["temperature"] = temperature
        if max_tokens is not None:
            payload["options"] = payload.get("options", {})
            payload["options"]["num_predict"] = max_tokens

        resp = await self._client.post("/v1/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    async def aclose(self) -> None:
        await self._client.aclose()
