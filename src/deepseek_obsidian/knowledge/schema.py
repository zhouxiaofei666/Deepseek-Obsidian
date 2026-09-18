from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


NodeType = Literal[
    "paper",
    "concept",
    "method",
    "device",
    "dataset",
    "metric",
    "result",
    "experiment",
    "model",
    "person",
    "organization",
    "other",
]


class KnowledgeNode(BaseModel):
    id: str
    label: str
    type: NodeType = "other"
    aliases: list[str] = Field(default_factory=list)
    source_documents: list[str] = Field(default_factory=list)


class KnowledgeEdge(BaseModel):
    source: str
    target: str
    relation: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str | None = None
    source_document: str | None = None
    source_page: int | None = None
