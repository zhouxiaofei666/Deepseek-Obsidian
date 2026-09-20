from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

from deepseek_obsidian.models import DocumentManifest, PageRecord


class ImageParser:
    name = "image"

    def parse(self, source: str | Path, output_root: str | Path) -> DocumentManifest:
        source = Path(source).expanduser().resolve()
        digest = hashlib.sha256(source.read_bytes()).hexdigest()[:12]
        stem = re.sub(r"[^A-Za-z0-9._-]+", "-", source.stem).strip("-") or "image"
        document_id = f"{stem}-{digest}"
        out = Path(output_root).expanduser().resolve() / document_id
        images = out / "images"
        images.mkdir(parents=True, exist_ok=True)
        target = images / source.name
        shutil.copy2(source, target)
        ref = f"images/{target.name}"
        text = f"# {source.stem}\n\n![]({ref})"
        page = PageRecord(page=1, text=text, images=[ref])
        (out / "document.md").write_text(
            f'---\ntitle: "{source.stem}"\ndocument_id: "{document_id}"\npages: 1\n---\n\n'
            "<!-- PAGE:1 -->\n\n" + text,
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
