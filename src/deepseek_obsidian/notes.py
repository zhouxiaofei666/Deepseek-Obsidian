from __future__ import annotations

import re
from pathlib import Path

from deepseek_obsidian.knowledge.schema import KnowledgeEdge, KnowledgeNode
from deepseek_obsidian.paper_schema import PaperUnderstanding
from deepseek_obsidian.vault import VaultLayout


START = "<!-- DEEPSEEK-OBSIDIAN:AUTO:START -->"
END = "<!-- DEEPSEEK-OBSIDIAN:AUTO:END -->"


def _safe(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*]+', "-", value).strip().strip(".")
    return value[:120] or "Untitled"


def _replace_auto(path: Path, generated: str, title: str) -> None:
    block = f"{START}\n{generated.rstrip()}\n{END}"
    if path.exists():
        old = path.read_text(encoding="utf-8")
        if START in old and END in old:
            before, rest = old.split(START, 1)
            _, after = rest.split(END, 1)
            content = before.rstrip() + "\n\n" + block + after
        else:
            content = old.rstrip() + "\n\n" + block + "\n"
    else:
        content = f"# {title}\n\n{block}\n"
    path.write_text(content, encoding="utf-8")


class NoteWriter:
    def __init__(self, layout: VaultLayout) -> None:
        self.layout = layout

    def write_paper(self, paper: PaperUnderstanding, nodes: list[KnowledgeNode], edges: list[KnowledgeEdge]) -> Path:
        name = _safe(f"{paper.title}--{paper.document_id[-8:]}")
        path = self.layout.papers / f"{name}.md"
        linked = {edge.target: edge for edge in edges}
        node_by_id = {node.id: node for node in nodes}

        def section(title: str, items: list) -> list[str]:
            lines = [f"## {title}", ""]
            if not items:
                return lines + ["- Not extracted", ""]
            for item in items:
                ev = item.evidence[0] if item.evidence else None
                suffix = f" (p. {ev.page})" if ev and ev.page else ""
                lines.append(f"- {item.value}{suffix}")
            lines.append("")
            return lines

        relations = []
        for target, edge in linked.items():
            node = node_by_id.get(target)
            if node:
                relations.append(f"- [[{node.label}]] — {edge.relation}")

        body = [
            "---",
            f'document_id: "{paper.document_id}"',
            "type: paper",
            f'title: "{paper.title.replace(chr(34), chr(39))}"',
            "---",
            "",
            "## Authors",
            "",
            ", ".join(paper.authors) if paper.authors else "Not extracted",
            "",
        ]
        body += section("Research questions", paper.research_questions)
        body += section("Methods", paper.methods)
        body += section("Datasets / participants", paper.datasets + paper.participants)
        body += section("Experimental conditions", paper.experimental_conditions)
        body += section("Models", paper.models)
        body += section("Metrics", paper.metrics)
        body += section("Results", paper.results)
        body += section("Limitations", paper.limitations)
        body += ["## Knowledge links", ""] + (relations or ["- None"]) + [""]
        _replace_auto(path, "\n".join(body), paper.title)
        return path

    def write_nodes(self, nodes: list[KnowledgeNode], edges: list[KnowledgeEdge]) -> None:
        incoming: dict[str, list[KnowledgeEdge]] = {}
        for edge in edges:
            incoming.setdefault(edge.target, []).append(edge)

        folders = {
            "method": self.layout.methods,
            "device": self.layout.devices,
            "dataset": self.layout.datasets,
            "paper": self.layout.papers,
        }
        for node in nodes:
            if node.type == "paper":
                continue
            folder = folders.get(node.type, self.layout.concepts)
            path = folder / f"{_safe(node.label)}.md"
            sources = incoming.get(node.id, [])
            lines = [
                "---",
                f"type: {node.type}",
                f'node_id: "{node.id}"',
                "---",
                "",
                "## Automatically linked sources",
                "",
            ]
            for edge in sources:
                page = f", p. {edge.source_page}" if edge.source_page else ""
                lines.append(f"- {edge.source_document}{page} — {edge.relation} — confidence {edge.confidence:.2f}")
            if not sources:
                lines.append("- None")
            _replace_auto(path, "\n".join(lines), node.label)
