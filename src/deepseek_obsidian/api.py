from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from deepseek_obsidian.ingestion import IngestionService
from deepseek_obsidian.watcher import InboxWatcher


class IngestRequest(BaseModel):
    path: str
    analyze: bool = False


def create_app(service: IngestionService) -> FastAPI:
    app = FastAPI(title="Deepseek-Obsidian Backend", version="0.2.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "vault": str(service.layout.root)}

    @app.get("/documents")
    def documents() -> list[dict]:
        return service.store.list_documents()

    @app.get("/search")
    def search(q: str, limit: int = 20) -> list[dict]:
        try:
            return service.store.search(q, limit=min(max(limit, 1), 100))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/graph")
    def graph(include_review: bool = False) -> dict:
        return service.store.graph(include_review=include_review)

    @app.get("/review")
    def review() -> list[dict]:
        return service.store.pending_edges()

    @app.post("/ingest")
    def ingest(request: IngestRequest) -> dict:
        path = Path(request.path).expanduser()
        try:
            manifest = service.ingest(path, analyze=request.analyze)
        except (FileNotFoundError, ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return manifest.model_dump()

    @app.post("/scan")
    def scan(analyze: bool = False) -> dict:
        files = InboxWatcher(service).scan_once(analyze=analyze)
        return {"processed": files}

    return app
