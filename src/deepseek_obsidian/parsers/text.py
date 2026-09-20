from __future__ import annotations

import hashlib
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path

from deepseek_obsidian.models import DocumentManifest, PageRecord


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if value:
            self.parts.append(value)


class TextParser:
    name = "text"

    @staticmethod
    def _id(path: Path) -> str:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
        stem = re.sub(r"[^A-Za-z0-9._-]+", "-", path.stem).strip("-") or "document"
        return f"{stem}-{digest}"

    def parse(self, source: str | Path, output_root: str | Path) -> DocumentManifest:
        source = Path(source).expanduser().resolve()
        output_root = Path(output_root).expanduser().resolve()
        raw = source.read_text(encoding="utf-8", errors="replace")
        if source.suffix.lower() in {".html", ".htm"}:
            parser = _TextExtractor()
            parser.feed(raw)
            text = "\n\n".join(parser.parts)
            text = html.unescape(text)
        else:
            text = raw

        document_id = self._id(source)
        out = output_root / document_id
        images = out / "images"
        out.mkdir(parents=True, exist_ok=True)
        images.mkdir(exist_ok=True)

        markdown = text if source.suffix.lower() in {".md", ".markdown"} else f"# {source.stem}\n\n{text}"
        page = PageRecord(page=1, text=markdown)
        (out / "document.md").write_text(
            f'---\ntitle: "{source.stem}"\ndocument_id: "{document_id}"\npages: 1\n---\n\n'
            "<!-- PAGE:1 -->\n\n" + markdown,
            encoding="utf-8",
        )
        (out / "pages.json").write_text(
            json.dumps([page.model_dump()], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        manifest = DocumentManifest(
            document_id=document_id,
            source_file=str(source),
            title=source.stem,
            page_count=1,
            parser=self.name,
            markdown_file="document.md",
            pages_file="pages.json",
            images_dir="images",
            metadata={"source_type": source.suffix.lower().lstrip(".")},
        )
        (out / "document.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        return manifest
