from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class LLMProvider(ABC):
    """Model adapter boundary.

    Everything before this class is model-independent.
    """

    name = "base"
    supports_vision = False

    @abstractmethod
    def analyze_text(self, text: str, system_prompt: str | None = None) -> str:
        raise NotImplementedError

    def analyze_image(self, image_path: str | Path, prompt: str) -> str:
        raise NotImplementedError(f"{self.name} provider does not implement image analysis")
