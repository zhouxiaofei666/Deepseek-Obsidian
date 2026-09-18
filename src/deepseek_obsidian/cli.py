from __future__ import annotations

import argparse
from pathlib import Path

from deepseek_obsidian.config import Settings
from deepseek_obsidian.pipeline import ResearchPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deepseek-obsidian")
    parser.add_argument("--vault", default="vault", help="Vault directory")

    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Convert PDF into a normalized document package")
    ingest.add_argument("pdf", help="Path to PDF")

    packet = sub.add_parser("packet", help="Create an LLM reading packet from a processed document")
    packet.add_argument("document_id")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = Settings.load(args.vault)
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    pipeline = ResearchPipeline(settings.processed_dir)

    if args.command == "ingest":
        manifest = pipeline.ingest_pdf(args.pdf)
        packet = pipeline.create_reading_packet(manifest)
        print(f"Document ID: {manifest.document_id}")
        print(f"Pages: {manifest.page_count}")
        print(f"Output: {packet.parent}")
        return

    if args.command == "packet":
        document_dir = settings.processed_dir / args.document_id
        manifest_path = document_dir / "document.json"
        if not manifest_path.exists():
            raise SystemExit(f"Unknown document: {args.document_id}")

        from deepseek_obsidian.models import DocumentManifest

        manifest = DocumentManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        packet_path = pipeline.create_reading_packet(manifest)
        print(packet_path)


if __name__ == "__main__":
    main()
