# Deepseek-Obsidian

AI-assisted research knowledge vault inspired by Obsidian.

The project is designed around a model-independent pipeline:

```text
PDF / notes / documents
        |
        v
Document parser
        |
        v
Normalized Document Package
(markdown + pages + figures + metadata)
        |
        v
LLM Provider
(DeepSeek / OpenAI / other compatible models)
        |
        v
Structured understanding
        |
        v
Knowledge graph / backlinks / visualization
```

## Current milestone

The first milestone focuses only on one problem:

> Convert research PDFs into a reliable, model-friendly document package that DeepSeek or another LLM can understand.

No knowledge graph is required for the first milestone.

## Design principles

- Markdown-first and Obsidian-compatible.
- PDF parsing is independent from the LLM.
- DeepSeek is the default provider, not a hard dependency.
- Figures and tables are preserved for multimodal processing.
- Page provenance is retained so every extracted claim can be traced back.
- Future graph generation uses explicit nodes, edges, evidence and confidence.
- Local files remain the source of truth.

## Planned package

```text
deepseek-obsidian/
├── src/deepseek_obsidian/
│   ├── cli.py
│   ├── config.py
│   ├── models.py
│   ├── pipeline.py
│   ├── parsers/
│   │   └── pdf.py
│   └── providers/
│       ├── base.py
│       ├── deepseek.py
│       └── openai_compatible.py
├── docs/
│   ├── ARCHITECTURE.md
│   └── ROADMAP.md
├── tests/
│   └── test_models.py
├── .env.example
├── .gitignore
└── pyproject.toml
```

## Output format

For an input such as:

```text
papers/example.pdf
```

the parser will create:

```text
vault/_processed/example/
├── document.md
├── document.json
├── pages.json
└── images/
```

This normalized package is what the model layer consumes.

## Why this works with both DeepSeek and Codex/OpenAI

The parsing stage does not depend on model intelligence.

Both providers receive the same structured inputs:

- clean Markdown text;
- page boundaries;
- metadata;
- extracted figures;
- table/figure references;
- source provenance.

The provider layer only decides how those inputs are interpreted. A stronger vision model can therefore be substituted without rebuilding the PDF pipeline.

## Development status

Scaffold in progress. The repository is intentionally being built milestone-by-milestone.
