from __future__ import annotations

import json
from pathlib import Path

from deepseek_obsidian.models import DocumentManifest
from deepseek_obsidian.parsers import PdfParser
from deepseek_obsidian.providers.base import LLMProvider


PAPER_SYSTEM_PROMPT = """You are reading a scientific paper from a normalized document package.
Preserve uncertainty. Do not invent missing information.
When making a claim, retain page references whenever the input contains them.
Separate methods, experimental conditions, metrics, results, limitations and cited prior work.
"""


class ResearchPipeline:
    def __init__(
        self,
        processed_dir: str | Path,
        *,
        text_provider: LLMProvider | None = None,
        vision_provider: LLMProvider | None = None,
    ) -> None:
        self.processed_dir = Path(processed_dir)
        self.text_provider = text_provider
        self.vision_provider = vision_provider
        self.pdf_parser = PdfParser()

    def ingest_pdf(self, pdf_path: str | Path) -> DocumentManifest:
        return self.pdf_parser.parse(pdf_path, self.processed_dir)

    def create_reading_packet(self, manifest: DocumentManifest) -> Path:
        document_dir = self.processed_dir / manifest.document_id
        markdown = (document_dir / manifest.markdown_file).read_text(encoding="utf-8")
        pages = json.loads((document_dir / manifest.pages_file).read_text(encoding="utf-8"))

        packet = [
            "# LLM Reading Packet",
            "",
            f"- Document ID: {manifest.document_id}",
            f"- Title: {manifest.title}",
            f"- Pages: {manifest.page_count}",
            "",
            "## Reading rules",
            "",
            "- Treat PAGE markers as provenance.",
            "- Do not infer values that are not present.",
            "- Keep figure references even when figure content has not been interpreted yet.",
            "",
            "## Full text",
            "",
            markdown,
            "",
            "## Page index",
            "",
        ]
        for page in pages:
            packet.append(f"- Page {page['page']}: {len(page.get('text', ''))} characters")

        packet_path = document_dir / "reading_packet.md"
        packet_path.write_text("\n".join(packet), encoding="utf-8")
        return packet_path

    def analyze_text(self, manifest: DocumentManifest, instruction: str) -> str:
        if self.text_provider is None:
            raise RuntimeError("No text provider configured")
        packet = self.create_reading_packet(manifest).read_text(encoding="utf-8")
        return self.text_provider.analyze_text(
            f"{instruction}\n\n{packet}",
            system_prompt=PAPER_SYSTEM_PROMPT,
        )
