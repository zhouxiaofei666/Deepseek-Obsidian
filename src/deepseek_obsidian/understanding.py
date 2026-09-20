from __future__ import annotations

import json
from pathlib import Path

from deepseek_obsidian.models import DocumentManifest
from deepseek_obsidian.paper_schema import PaperUnderstanding
from deepseek_obsidian.providers.base import LLMProvider


SYSTEM = """You extract structured facts from scientific and technical documents.
Return JSON only. Never invent missing information.
Every factual item should retain page evidence when possible.
Do not turn cited prior-work claims into findings of the current paper.
Keep numerical results exact when present.
"""


class PaperAnalyzer:
    def __init__(
        self,
        processed_dir: str | Path,
        text_provider: LLMProvider,
        *,
        vision_provider: LLMProvider | None = None,
        max_chunk_chars: int = 45000,
    ) -> None:
        self.processed_dir = Path(processed_dir)
        self.text_provider = text_provider
        self.vision_provider = vision_provider or text_provider
        self.max_chunk_chars = max_chunk_chars

    def _load_pages(self, manifest: DocumentManifest) -> list[dict]:
        root = self.processed_dir / manifest.document_id
        return json.loads((root / manifest.pages_file).read_text(encoding="utf-8"))

    def _chunks(self, pages: list[dict]) -> list[str]:
        chunks: list[str] = []
        current: list[str] = []
        size = 0
        for page in pages:
            block = f"\n<!-- PAGE:{page['page']} -->\n{page.get('text', '')}\n"
            if current and size + len(block) > self.max_chunk_chars:
                chunks.append("".join(current))
                current = []
                size = 0
            current.append(block)
            size += len(block)
        if current:
            chunks.append("".join(current))
        return chunks

    def _figure_summaries(self, manifest: DocumentManifest, pages: list[dict]) -> list[dict]:
        if not getattr(self.vision_provider, "supports_vision", False):
            return []
        root = self.processed_dir / manifest.document_id
        output: list[dict] = []
        for page in pages:
            for rel in page.get("images", []):
                path = root / rel
                if not path.exists():
                    continue
                try:
                    description = self.vision_provider.analyze_image(
                        path,
                        "Analyze this scientific figure or table. State what it shows, axes/labels, "
                        "important numerical trends, and the role it appears to play in the paper. "
                        "Do not invent unreadable values.",
                    )
                except Exception as exc:
                    description = f"Vision analysis unavailable: {type(exc).__name__}"
                output.append(
                    {
                        "label": None,
                        "page": page["page"],
                        "image_path": rel,
                        "description": description,
                        "confidence": 0.7,
                    }
                )
        return output

    def analyze(self, manifest: DocumentManifest) -> PaperUnderstanding:
        pages = self._load_pages(manifest)
        schema = PaperUnderstanding.model_json_schema()
        partials: list[dict] = []

        instruction = """Extract this chunk into JSON using the supplied schema as closely as possible.
For list items use objects with value, confidence, and evidence.
Evidence must use the PAGE markers from the input.
The document_id is {document_id}.
"""
        for chunk in self._chunks(pages):
            data = self.text_provider.analyze_json(
                instruction.format(document_id=manifest.document_id) + "\n\n" + chunk,
                schema_hint=schema,
                system_prompt=SYSTEM,
            )
            partials.append(data)

        figures = self._figure_summaries(manifest, pages)
        synthesis_prompt = """Merge the partial extractions below into one final scientific-paper record.
Deduplicate synonymous items. Preserve exact numbers and page evidence.
Do not add facts that do not occur in the partial records.
Return JSON matching the supplied schema.
"""
        merged = self.text_provider.analyze_json(
            synthesis_prompt
            + "\nDocument metadata:\n"
            + json.dumps(
                {"document_id": manifest.document_id, "title": manifest.title},
                ensure_ascii=False,
            )
            + "\nPartial records:\n"
            + json.dumps(partials, ensure_ascii=False)
            + "\nFigure analyses:\n"
            + json.dumps(figures, ensure_ascii=False),
            schema_hint=schema,
            system_prompt=SYSTEM,
        )
        merged["document_id"] = manifest.document_id
        merged.setdefault("title", manifest.title)
        merged["figures"] = figures
        result = PaperUnderstanding.model_validate(merged)

        root = self.processed_dir / manifest.document_id
        (root / "understanding.json").write_text(
            result.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return result
