from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pymupdf
import pymupdf4llm

from deepseek_obsidian.models import DocumentManifest, PageRecord


class PdfParser:
    """Convert a PDF into a model-friendly, provenance-preserving document package."""

    name = "pymupdf4llm"

    def __init__(self, dpi: int = 160) -> None:
        self.dpi = dpi

    @staticmethod
    def _safe_name(name: str) -> str:
        value = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")
        return value or "document"

    @staticmethod
    def _document_id(pdf_path: Path) -> str:
        digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()[:12]
        return f"{PdfParser._safe_name(pdf_path.stem)}-{digest}"

    def parse(self, pdf_path: str | Path, output_root: str | Path) -> DocumentManifest:
        pdf_path = Path(pdf_path).expanduser().resolve()
        output_root = Path(output_root).expanduser().resolve()

        if not pdf_path.exists():
            raise FileNotFoundError(pdf_path)
        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected a PDF file, got: {pdf_path.suffix}")

        document_id = self._document_id(pdf_path)
        out_dir = output_root / document_id
        image_dir = out_dir / "images"
        out_dir.mkdir(parents=True, exist_ok=True)
        image_dir.mkdir(parents=True, exist_ok=True)

        doc = pymupdf.open(pdf_path)
        title = str(doc.metadata.get("title") or pdf_path.stem).strip()

        chunks = pymupdf4llm.to_markdown(
            doc,
            page_chunks=True,
            write_images=True,
            image_path=str(image_dir),
            image_format="png",
            dpi=self.dpi,
            force_text=True,
            header=False,
            footer=False,
            show_progress=False,
        )

        pages: list[PageRecord] = []
        markdown_parts: list[str] = [
            "---",
            f'title: "{title.replace(chr(34), chr(39))}"',
            f'source_pdf: "{pdf_path.name}"',
            f'document_id: "{document_id}"',
            f"pages: {len(chunks)}",
            "---",
            "",
        ]

        for page_number, chunk in enumerate(chunks, start=1):
            text = str(chunk.get("text", "")).strip()
            images = [
                str(path.relative_to(out_dir)).replace("\\", "/")
                for path in sorted(image_dir.glob(f"*p{page_number}*"))
            ]
            pages.append(
                PageRecord(
                    page=page_number,
                    text=text,
                    images=images,
                    metadata=dict(chunk.get("metadata") or {}),
                )
            )
            markdown_parts.extend(
                [
                    f"<!-- PAGE:{page_number} -->",
                    "",
                    text,
                    "",
                ]
            )

        markdown_path = out_dir / "document.md"
        pages_path = out_dir / "pages.json"
        manifest_path = out_dir / "document.json"

        markdown_path.write_text("\n".join(markdown_parts), encoding="utf-8")
        pages_path.write_text(
            json.dumps([page.model_dump() for page in pages], ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

        manifest = DocumentManifest(
            document_id=document_id,
            source_file=str(pdf_path),
            title=title,
            page_count=len(pages),
            parser=self.name,
            markdown_file="document.md",
            pages_file="pages.json",
            images_dir="images",
            metadata={
                "pdf_metadata": dict(doc.metadata or {}),
                "dpi": self.dpi,
            },
        )
        manifest_path.write_text(
            manifest.model_dump_json(indent=2),
            encoding="utf-8",
        )
        doc.close()
        return manifest
