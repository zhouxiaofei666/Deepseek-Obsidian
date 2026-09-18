# Deepseek-Obsidian

AI-assisted research knowledge vault inspired by Obsidian.

The core design is **model-independent**:

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
(DeepSeek / OpenAI-compatible / future local models)
        |
        v
Structured understanding
        |
        v
Knowledge graph / backlinks / visualization
```

## Current milestone

The first milestone solves one problem well:

> Convert research PDFs into a reliable, model-friendly document package that DeepSeek or another LLM can understand.

The knowledge graph is scaffolded, but not yet the active focus.

## Why the processing can be shared by DeepSeek and Codex/OpenAI

The difficult PDF work happens **before** the model is called.

Both providers receive the same normalized material:

- clean Markdown text;
- explicit page boundaries;
- PDF metadata;
- extracted figures;
- table/figure references;
- source provenance.

The provider layer only decides how those materials are interpreted. A stronger text or vision model can therefore be swapped in without rebuilding the PDF pipeline.

## Project structure

```text
deepseek-obsidian/
├── src/deepseek_obsidian/
│   ├── cli.py
│   ├── config.py
│   ├── models.py
│   ├── pipeline.py
│   ├── parsers/
│   │   └── pdf.py
│   ├── providers/
│   │   ├── base.py
│   │   ├── deepseek.py
│   │   └── openai_compatible.py
│   └── knowledge/
│       └── schema.py
├── docs/
│   ├── ARCHITECTURE.md
│   └── ROADMAP.md
├── tests/
├── .github/workflows/ci.yml
├── .env.example
├── .gitignore
└── pyproject.toml
```

## Quick start

Clone the repository and create a Python 3.11+ environment:

```bash
git clone https://github.com/zhouxiaofei666/Deepseek-Obsidian.git
cd Deepseek-Obsidian

python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Process a paper:

```powershell
deepseek-obsidian ingest "D:\papers\example.pdf"
```

The parser writes a content-derived document folder under:

```text
vault/_processed/<document-id>/
├── document.md
├── document.json
├── pages.json
├── reading_packet.md
└── images/
```

### document.md

Portable Markdown intended for both people and LLMs. Page markers are retained:

```html
<!-- PAGE:7 -->
```

### pages.json

Per-page structured text used later for retrieval, citations and evidence tracking.

### document.json

Machine-readable manifest describing the processed paper.

### images/

Extracted figure/image regions. They are deliberately separated from text reasoning so the project can route them to whichever vision model is most suitable.

## Model providers

The parser is independent of the model.

Currently scaffolded:

- **DeepSeekProvider** — default text reasoning path.
- **OpenAICompatibleProvider** — generic text/vision-compatible adapter.
- **LLMProvider** — base interface for future providers.

This means the future routing can be:

```text
paper text  -> DeepSeek
figures     -> vision-capable provider
final merge -> DeepSeek or another reasoning model
```

without changing PDF ingestion.

## Configuration

Copy:

```text
.env.example
```

to:

```text
.env
```

API keys are intentionally excluded from Git.

## Development principles

- Markdown-first and Obsidian-compatible.
- Original files remain the source of truth.
- AI-generated relations must retain evidence and source pages.
- Low-confidence edits should eventually go to a review queue.
- Derived graph data must be rebuildable.
- Model choice must remain replaceable.
- Git history will provide rollback for automated knowledge edits.

## Next work

See `docs/ROADMAP.md`.

The immediate next milestone is to validate the PDF package on real scientific papers, then add a fixed scientific-paper schema for Methods, Dataset, Metrics, Results, Limitations and Figures.
