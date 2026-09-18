# Architecture

## Goal

Deepseek-Obsidian separates document processing from model intelligence.

The same parsed paper must be reusable by DeepSeek, OpenAI/Codex-compatible models, local models, or future providers.

## Pipeline

```text
                Sources
        PDF / Markdown / notes
                  |
                  v
        +-------------------+
        | Ingestion layer   |
        | PDF parser        |
        +-------------------+
                  |
                  v
       Normalized document package
       - document.md
       - document.json
       - pages.json
       - images/
                  |
          +-------+-------+
          |               |
          v               v
     Text provider    Vision provider
      DeepSeek        optional stronger
          |               |
          +-------+-------+
                  |
                  v
        Structured understanding
                  |
                  v
          Knowledge extraction
        nodes / edges / evidence
                  |
                  v
       Markdown Vault + graph UI
```

## Important boundary

The parser MUST NOT know which LLM will consume its output.

The LLM provider MUST NOT be responsible for extracting PDF layout.

This allows the model to be changed without reprocessing the original architecture.

## Normalized document package

Each document gets a stable content-derived ID and a directory under `vault/_processed/`.

### document.md

Human-readable Markdown with page markers.

### pages.json

Per-page structured text and metadata for provenance and future retrieval.

### document.json

Manifest for machine use.

### images/

Extracted figures and other PDF images. These can be routed to a separate vision provider.

## Model routing

A single model does not need to do everything.

Example:

```text
PDF text --------> DeepSeek
Figures ---------> vision-capable provider
Tables ----------> deterministic parser first, LLM fallback
Final synthesis -> DeepSeek or stronger reasoning model
```

The routing policy will be configurable rather than hard-coded.

## Future graph layer

Graph records should preserve evidence:

```text
source node
target node
relation
confidence
source document
source page
evidence
```

The graph is derived data. Markdown and original files remain the source of truth.
