from pathlib import Path

import pymupdf

from deepseek_obsidian.parsers import PdfParser


def _make_pdf(path: Path) -> None:
    doc = pymupdf.open()
    page1 = doc.new_page()
    page1.insert_text((72, 72), "Example research paper")
    page1.insert_text((72, 100), "Methods: pressure sensing and pose estimation.")
    page2 = doc.new_page()
    page2.insert_text((72, 72), "Results: test value 42.")
    doc.save(path)
    doc.close()


def test_pdf_parser_creates_document_package(tmp_path: Path) -> None:
    pdf_path = tmp_path / "example.pdf"
    out = tmp_path / "processed"
    _make_pdf(pdf_path)

    manifest = PdfParser().parse(pdf_path, out)

    document_dir = out / manifest.document_id
    assert manifest.page_count == 2
    assert (document_dir / "document.md").exists()
    assert (document_dir / "document.json").exists()
    assert (document_dir / "pages.json").exists()
    assert (document_dir / "images").is_dir()

    markdown = (document_dir / "document.md").read_text(encoding="utf-8")
    assert "<!-- PAGE:1 -->" in markdown
    assert "<!-- PAGE:2 -->" in markdown
    assert "pressure sensing" in markdown
