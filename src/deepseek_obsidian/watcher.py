from __future__ import annotations

import time
from pathlib import Path

from deepseek_obsidian.ingestion import IngestionService


class InboxWatcher:
    def __init__(self, service: IngestionService, *, interval: float = 5.0) -> None:
        self.service = service
        self.interval = max(1.0, interval)

    def scan_once(self, *, analyze: bool = False) -> list[str]:
        processed: list[str] = []
        inbox = self.service.layout.inbox
        for path in sorted(inbox.iterdir()):
            if not path.is_file() or not self.service.dispatcher.supports(path):
                continue
            self.service.ingest(path, analyze=analyze)
            processed.append(str(path))
        return processed

    def run(self, *, analyze: bool = False) -> None:
        print(f"Watching {self.service.layout.inbox}")
        while True:
            try:
                self.scan_once(analyze=analyze)
                time.sleep(self.interval)
            except KeyboardInterrupt:
                return
