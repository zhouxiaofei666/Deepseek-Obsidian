from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    sha256 TEXT UNIQUE NOT NULL,
    source_file TEXT NOT NULL,
    original_file TEXT,
    title TEXT NOT NULL,
    source_type TEXT,
    status TEXT NOT NULL DEFAULT 'ingested',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    type TEXT NOT NULL,
    aliases_json TEXT NOT NULL DEFAULT '[]',
    source_documents_json TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    relation TEXT NOT NULL,
    confidence REAL NOT NULL,
    evidence TEXT,
    source_document TEXT,
    source_page INTEGER,
    status TEXT NOT NULL DEFAULT 'approved',
    UNIQUE(source, target, relation, source_document, source_page)
);

CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    document_id UNINDEXED,
    title,
    content
);
"""


class KnowledgeStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def find_document_by_sha(self, sha256: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM documents WHERE sha256 = ?",
            (sha256,),
        ).fetchone()
        return dict(row) if row else None

    def upsert_document(
        self,
        *,
        document_id: str,
        sha256: str,
        source_file: str,
        original_file: str,
        title: str,
        source_type: str,
        content: str,
        status: str = "ingested",
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO documents(document_id, sha256, source_file, original_file, title, source_type, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(document_id) DO UPDATE SET
              source_file=excluded.source_file,
              original_file=excluded.original_file,
              title=excluded.title,
              source_type=excluded.source_type,
              status=excluded.status,
              updated_at=CURRENT_TIMESTAMP
            """,
            (document_id, sha256, source_file, original_file, title, source_type, status),
        )
        self.conn.execute("DELETE FROM documents_fts WHERE document_id = ?", (document_id,))
        self.conn.execute(
            "INSERT INTO documents_fts(document_id, title, content) VALUES (?, ?, ?)",
            (document_id, title, content),
        )
        self.conn.commit()

    def update_document_status(self, document_id: str, status: str) -> None:
        self.conn.execute(
            "UPDATE documents SET status=?, updated_at=CURRENT_TIMESTAMP WHERE document_id=?",
            (status, document_id),
        )
        self.conn.commit()

    def list_documents(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.conn.execute(
            "SELECT * FROM documents ORDER BY updated_at DESC"
        ).fetchall()]

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT document_id, title, snippet(documents_fts, 2, '[', ']', '…', 18) AS snippet
            FROM documents_fts
            WHERE documents_fts MATCH ?
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def upsert_node(self, node: Any) -> None:
        data = node.model_dump() if hasattr(node, "model_dump") else dict(node)
        self.conn.execute(
            """
            INSERT INTO nodes(id, label, type, aliases_json, source_documents_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              label=excluded.label,
              type=excluded.type,
              aliases_json=excluded.aliases_json,
              source_documents_json=excluded.source_documents_json,
              updated_at=CURRENT_TIMESTAMP
            """,
            (
                data["id"],
                data["label"],
                data["type"],
                json.dumps(data.get("aliases", []), ensure_ascii=False),
                json.dumps(data.get("source_documents", []), ensure_ascii=False),
            ),
        )
        self.conn.commit()

    def upsert_edge(self, edge: Any, status: str = "approved") -> None:
        data = edge.model_dump() if hasattr(edge, "model_dump") else dict(edge)
        self.conn.execute(
            """
            INSERT INTO edges(source, target, relation, confidence, evidence, source_document, source_page, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source, target, relation, source_document, source_page) DO UPDATE SET
              confidence=excluded.confidence,
              evidence=excluded.evidence,
              status=excluded.status
            """,
            (
                data["source"],
                data["target"],
                data["relation"],
                data["confidence"],
                data.get("evidence"),
                data.get("source_document"),
                data.get("source_page"),
                status,
            ),
        )
        self.conn.commit()

    def graph(self, include_review: bool = False) -> dict[str, list[dict[str, Any]]]:
        nodes = [dict(row) for row in self.conn.execute("SELECT * FROM nodes").fetchall()]
        sql = "SELECT * FROM edges" if include_review else "SELECT * FROM edges WHERE status='approved'"
        edges = [dict(row) for row in self.conn.execute(sql).fetchall()]
        return {"nodes": nodes, "edges": edges}

    def pending_edges(self) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self.conn.execute(
                "SELECT * FROM edges WHERE status='review' ORDER BY confidence DESC"
            ).fetchall()
        ]
