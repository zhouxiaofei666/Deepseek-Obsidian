# Roadmap

## Milestone 1 - PDF normalization

- [x] Repository scaffold
- [x] PDF -> Markdown
- [x] Preserve page boundaries
- [x] Extract PDF images
- [x] Generate document manifest
- [x] Generate LLM reading packet
- [ ] Validate against real two-column papers
- [ ] Improve figure-to-page mapping
- [ ] Add table extraction quality checks
- [ ] Add scanned-PDF OCR fallback tests

## Milestone 2 - Paper understanding

- [x] Provider abstraction
- [x] DeepSeek text adapter
- [x] Generic OpenAI-compatible adapter
- [ ] Standard paper schema
- [ ] Methods / dataset / metrics / results extraction
- [ ] Figure interpretation routing
- [ ] Citation and page-evidence validation
- [ ] Chunking for papers larger than context window

## Milestone 3 - Vault

- [ ] Obsidian-compatible Markdown notes
- [ ] Stable concept IDs
- [ ] Bidirectional links
- [ ] Tags and aliases
- [ ] Paper / concept / method / device templates

## Milestone 4 - Knowledge graph

- [x] Initial node/edge schemas
- [ ] SQLite persistence
- [ ] Candidate-link retrieval
- [ ] LLM relation verification
- [ ] Evidence/confidence storage
- [ ] Duplicate entity merging
- [ ] Contradiction detection

## Milestone 5 - Visualization

- [ ] Interactive graph
- [ ] Node filters
- [ ] 1/2/3-hop neighborhood view
- [ ] Evidence side panel
- [ ] Paper-to-method and experiment-to-result views

## Milestone 6 - Automatic maintenance

- [ ] Watch Vault for new files
- [ ] Incremental re-indexing
- [ ] Suggested links
- [ ] Orphan-node detection
- [ ] Conflict detection
- [ ] Review queue for low-confidence AI edits
- [ ] Git-backed history and rollback
