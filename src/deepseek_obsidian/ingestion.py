from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from deepseek_obsidian.knowledge.builder import KnowledgeBuilder
from deepseek_obsidian.models import DocumentManifest
from deepseek_obsidian.notes import NoteWriter
from deepseek_obsidian.parsers.dispatcher import ParserDispatcher
from deepseek_obsidian.providers.base import LLMProvider
from deepseek_obsidian.storage import KnowledgeStore
from deepseek_obsidian.understanding import PaperAnalyzer
from deepseek_obsidian.vault import VaultLayout


class IngestionService:
    def __init__(
        self,
        layout: VaultLayout,
        store: KnowledgeStore,
        *,
        text_provider: LLMProvider | None = None,
        vision_provider: LLMProvider | None = None,
        confidence_threshold: float = 0.78,
        max_chunk_chars: int = 45000,
    ) -> None:
        self.layout = layout.ensure()
        self.store = store
        self.dispatcher = ParserDispatcher()
        self.text_provider = text_provider
        self.vision_provider = vision_provider
        self.confidence_threshold = confidence_threshold
        self.max_chunk_chars = max_chunk_chars

    @staticmethod
    def sha256(path: str | Path) -> str:
        digest = hashlib.sha256()
        with Path(path).open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def archive_source(self, source: str | Path, sha256: str) -> Path:
        source = Path(source).expanduser().resolve()
        folder = self.layout.sources / sha256[:2]
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"{sha256}{source.suffix.lower()}"
        if not target.exists():
            shutil.copy2(source, target)
        return target

    def _load_manifest(self, document_id: str) -> DocumentManifest:
        path = self.layout.processed / document_id / "document.json"
        return DocumentManifest.model_validate_json(path.read_text(encoding="utf-8"))

    def ingest(self, source: str | Path, *, analyze: bool = False) -> DocumentManifest:
        source = Path(source).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        if not self.dispatcher.supports(source):
            raise ValueError(f"Unsupported source type: {source.suffix}")

        digest = self.sha256(source)
        existing = self.store.find_document_by_sha(digest)
        if existing:
            manifest = self._load_manifest(existing["document_id"])
            if analyze and existing["status"] != "analyzed":
                self.analyze(manifest)
            return manifest

        manifest = self.dispatcher.parse(source, self.layout.processed)
        archived = self.archive_source(source, digest)
        manifest.source_file = str(archived)
        manifest.metadata["sha256"] = digest
        manifest.metadata["original_file"] = str(source)
        manifest.metadata["source_type"] = source.suffix.lower().lstrip(".")
        manifest_path = self.layout.processed / manifest.document_id / "document.json"
        manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

        markdown = (self.layout.processed / manifest.document_id / manifest.markdown_file).read_text(
            encoding="utf-8"
        )
        self.store.upsert_document(
            document_id=manifest.document_id,
            sha256=digest,
            source_file=str(archived),
            original_file=str(source),
            title=manifest.title,
            source_type=source.suffix.lower().lstrip("."),
            content=markdown,
            status="ingested",
        )
        self._write_reading_packet(manifest)
        if analyze:
            self.analyze(manifest)
        return manifest

    def _write_reading_packet(self, manifest: DocumentManifest) -> Path:
        root = self.layout.processed / manifest.document_id
        markdown = (root / manifest.markdown_file).read_text(encoding="utf-8")
        packet = (
            "# LLM Reading Packet\n\n"
            f"- Document ID: {manifest.document_id}\n"
            f"- Title: {manifest.title}\n"
            f"- Pages: {manifest.page_count}\n\n"
            "## Rules\n\n"
            "- PAGE markers are provenance.\n"
            "- Do not invent missing values.\n"
            "- Distinguish this document's findings from cited prior work.\n\n"
            "## Content\n\n"
            + markdown
        )
        target = root / "reading_packet.md"
        target.write_text(packet, encoding="utf-8")
        return target

    def analyze(self, manifest: DocumentManifest) -> None:
        if self.text_provider is None:
            raise RuntimeError("Analysis requested but no text provider is configured")

        analyzer = PaperAnalyzer(
            self.layout.processed,
            self.text_provider,
            vision_provider=self.vision_provider,
            max_chunk_chars=self.max_chunk_chars,
        )
        paper = analyzer.analyze(manifest)
        nodes, edges = KnowledgeBuilder().build(paper)

        for node in nodes:
            self.store.upsert_node(node)

        approved = []
        for edge in edges:
            status = "approved" if edge.confidence >= self.confidence_threshold else "review"
            self.store.upsert_edge(edge, status=status)
            if status == "approved":
                approved.append(edge)

        writer = NoteWriter(self.layout)
        writer.write_paper(paper, nodes, approved)
        writer.write_nodes(nodes, approved)
        self.store.update_document_status(manifest.document_id, "analyzed")
        self.export_graph()
        self.export_review_queue()

    def export_graph(self) -> Path:
        target = self.layout.system / "graph.json"
        target.write_text(
            json.dumps(self.store.graph(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return target

    def export_review_queue(self) -> Path:
        target = self.layout.review / "pending_edges.json"
        target.write_text(
            json.dumps(self.store.pending_edges(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return target
