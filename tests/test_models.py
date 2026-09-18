from deepseek_obsidian.knowledge.schema import KnowledgeEdge
from deepseek_obsidian.models import DocumentManifest


def test_manifest_roundtrip() -> None:
    manifest = DocumentManifest(
        document_id="paper-123",
        source_file="paper.pdf",
        title="Example",
        page_count=10,
        parser="test",
        markdown_file="document.md",
        pages_file="pages.json",
        images_dir="images",
    )
    restored = DocumentManifest.model_validate_json(manifest.model_dump_json())
    assert restored.document_id == "paper-123"
    assert restored.page_count == 10


def test_edge_confidence() -> None:
    edge = KnowledgeEdge(
        source="a",
        target="b",
        relation="uses",
        confidence=0.9,
        source_page=3,
    )
    assert edge.confidence == 0.9
