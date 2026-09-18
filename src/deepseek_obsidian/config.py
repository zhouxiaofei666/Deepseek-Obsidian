from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    vault_dir: Path
    processed_dir: Path
    deepseek_api_key: str | None
    deepseek_base_url: str
    deepseek_model: str

    @classmethod
    def load(cls, vault_dir: str | Path = "vault") -> "Settings":
        load_dotenv()
        vault = Path(vault_dir).expanduser().resolve()
        return cls(
            vault_dir=vault,
            processed_dir=vault / "_processed",
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY") or None,
            deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/"),
            deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        )
