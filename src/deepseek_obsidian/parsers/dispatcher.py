from __future__ import annotations

from pathlib import Path

from deepseek_obsidian.models import DocumentManifest

from .docx import DocxParser
from .image import ImageParser
from .pdf import PdfParser
from .text import TextParser


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".md",
    ".markdown",
    ".txt",
    ".html",
    ".htm",
    ".docx",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
}


class ParserDispatcher:
    def __init__(self) -> None:
        self.pdf = PdfParser()
        self.text = TextParser()
        self.docx = DocxParser()
        self.image = ImageParser()

    def supports(self, path: str | Path) -> bool:
        return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS

    def parse(self, source: str | Path, output_root: str | Path) -> DocumentManifest:
        suffix = Path(source).suffix.lower()
        if suffix == ".pdf":
            return self.pdf.parse(source, output_root)
        if suffix == ".docx":
            return self.docx.parse(source, output_root)
        if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            return self.image.parse(source, output_root)
        if suffix in {".md", ".markdown", ".txt", ".html", ".htm"}:
            return self.text.parse(source, output_root)
        raise ValueError(f"Unsupported file type: {suffix}")
