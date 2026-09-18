from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

import httpx

from .base import LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    """Generic OpenAI-compatible adapter.

    Set supports_vision=True only for an endpoint/model that accepts image_url content.
    """

    name = "openai-compatible"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        *,
        supports_vision: bool = False,
        timeout: float = 120.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.supports_vision = supports_vision
        self.timeout = timeout

    def _post(self, messages: list[dict]) -> str:
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"model": self.model, "messages": messages, "temperature": 0.1},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def analyze_text(self, text: str, system_prompt: str | None = None) -> str:
        messages: list[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": text})
        return self._post(messages)

    def analyze_image(self, image_path: str | Path, prompt: str) -> str:
        if not self.supports_vision:
            return super().analyze_image(image_path, prompt)

        path = Path(image_path)
        mime = mimetypes.guess_type(path.name)[0] or "image/png"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        data_url = f"data:{mime};base64,{encoded}"
        return self._post(
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ]
        )
