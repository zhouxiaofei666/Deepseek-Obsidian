from __future__ import annotations

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    page: int | None = None
    text: str | None = None


class SupportedItem(BaseModel):
    value: str
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)


class FigureSummary(BaseModel):
    label: str | None = None
    page: int | None = None
    image_path: str | None = None
    description: str
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class PaperUnderstanding(BaseModel):
    document_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    research_questions: list[SupportedItem] = Field(default_factory=list)
    methods: list[SupportedItem] = Field(default_factory=list)
    datasets: list[SupportedItem] = Field(default_factory=list)
    participants: list[SupportedItem] = Field(default_factory=list)
    experimental_conditions: list[SupportedItem] = Field(default_factory=list)
    inputs: list[SupportedItem] = Field(default_factory=list)
    outputs: list[SupportedItem] = Field(default_factory=list)
    models: list[SupportedItem] = Field(default_factory=list)
    metrics: list[SupportedItem] = Field(default_factory=list)
    results: list[SupportedItem] = Field(default_factory=list)
    limitations: list[SupportedItem] = Field(default_factory=list)
    figures: list[FigureSummary] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    suggested_projects: list[str] = Field(default_factory=list)
