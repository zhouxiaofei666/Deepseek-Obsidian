from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ExtractedImage(BaseModel):
    path: str
    page: int
    label: str | None = None


class PageRecord(BaseModel):
    page: int
    text: str
    images: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentManifest(BaseModel):
    document_id: str
    source_file: str
    title: str
    page_count: int
    parser: str
    markdown_file: str
    pages_file: str
    images_dir: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    def resolve_markdown(self, root: Path) -> Path:
        return root / self.markdown_file
