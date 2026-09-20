from __future__ import annotations

import hashlib
import re

from deepseek_obsidian.knowledge.schema import KnowledgeEdge, KnowledgeNode
from deepseek_obsidian.paper_schema import PaperUnderstanding, SupportedItem


def _norm(value: str) -> str:
    return " ".join(value.lower().split())


def _node_id(kind: str, label: str) -> str:
    norm = _norm(label)
    slug = re.sub(r"[^a-z0-9]+", "-", norm).strip("-")[:48] or kind
    digest = hashlib.sha1(norm.encode("utf-8")).hexdigest()[:8]
    return f"{kind}:{slug}:{digest}"


class KnowledgeBuilder:
    def build(self, paper: PaperUnderstanding) -> tuple[list[KnowledgeNode], list[KnowledgeEdge]]:
        paper_id = f"paper:{paper.document_id}"
        nodes: dict[str, KnowledgeNode] = {
            paper_id: KnowledgeNode(
                id=paper_id,
                label=paper.title,
                type="paper",
                source_documents=[paper.document_id],
            )
        }
        edges: list[KnowledgeEdge] = []

        def add(items: list[SupportedItem], kind: str, relation: str) -> None:
            for item in items:
                label = item.value.strip()
                if not label:
                    continue
                node_id = _node_id(kind, label)
                existing = nodes.get(node_id)
                if existing is None:
                    nodes[node_id] = KnowledgeNode(
                        id=node_id,
                        label=label,
                        type=kind if kind in {
                            "concept", "method", "device", "dataset", "metric",
                            "result", "experiment", "model", "other"
                        } else "other",
                        source_documents=[paper.document_id],
                    )
                elif paper.document_id not in existing.source_documents:
                    existing.source_documents.append(paper.document_id)

                evidence = item.evidence[0] if item.evidence else None
                edges.append(
                    KnowledgeEdge(
                        source=paper_id,
                        target=node_id,
                        relation=relation,
                        confidence=item.confidence,
                        evidence=evidence.text if evidence else None,
                        source_document=paper.document_id,
                        source_page=evidence.page if evidence else None,
                    )
                )

        add(paper.methods, "method", "uses_method")
        add(paper.datasets, "dataset", "uses_dataset")
        add(paper.models, "model", "uses_model")
        add(paper.metrics, "metric", "evaluates_with")
        add(paper.inputs, "concept", "has_input")
        add(paper.outputs, "concept", "produces_output")
        add(paper.experimental_conditions, "experiment", "tested_under")
        add(paper.results, "result", "reports_result")
        add(paper.limitations, "concept", "has_limitation")
        add(paper.research_questions, "concept", "investigates")

        return list(nodes.values()), edges
