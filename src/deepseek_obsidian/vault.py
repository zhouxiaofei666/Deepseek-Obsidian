from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VaultLayout:
    root: Path
    inbox: Path
    projects: Path
    papers: Path
    concepts: Path
    methods: Path
    devices: Path
    datasets: Path
    sources: Path
    processed: Path
    system: Path
    review: Path

    @classmethod
    def from_root(cls, root: str | Path) -> "VaultLayout":
        root = Path(root).expanduser().resolve()
        return cls(
            root=root,
            inbox=root / "00_Inbox",
            projects=root / "01_Projects",
            papers=root / "02_Papers",
            concepts=root / "03_Concepts",
            methods=root / "04_Methods",
            devices=root / "05_Devices",
            datasets=root / "06_Datasets",
            sources=root / "_sources",
            processed=root / "_processed",
            system=root / "_system",
            review=root / "_system" / "review",
        )

    def ensure(self) -> "VaultLayout":
        for path in (
            self.root,
            self.inbox,
            self.projects,
            self.papers,
            self.concepts,
            self.methods,
            self.devices,
            self.datasets,
            self.sources,
            self.processed,
            self.system,
            self.review,
        ):
            path.mkdir(parents=True, exist_ok=True)
        return self
