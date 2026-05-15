"""Snapshot archiver — stores versioned snapshots with timestamps for historical diffing."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from schema_drift.models import DatabaseSnapshot

_ARCHIVE_INDEX = "archive_index.json"


@dataclass
class ArchiveEntry:
    snapshot_id: str
    label: str
    created_at: str
    path: str

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "label": self.label,
            "created_at": self.created_at,
            "path": self.path,
        }

    @staticmethod
    def from_dict(d: dict) -> "ArchiveEntry":
        return ArchiveEntry(
            snapshot_id=d["snapshot_id"],
            label=d["label"],
            created_at=d["created_at"],
            path=d["path"],
        )


@dataclass
class SnapshotArchiver:
    archive_dir: Path
    _index: List[ArchiveEntry] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.archive_dir = Path(self.archive_dir)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self._load_index()

    def _index_path(self) -> Path:
        return self.archive_dir / _ARCHIVE_INDEX

    def _load_index(self) -> None:
        if self._index_path().exists():
            data = json.loads(self._index_path().read_text())
            self._index = [ArchiveEntry.from_dict(e) for e in data]
        else:
            self._index = []

    def _save_index(self) -> None:
        self._index_path().write_text(json.dumps([e.to_dict() for e in self._index], indent=2))

    def save(self, snapshot: DatabaseSnapshot, label: str = "") -> ArchiveEntry:
        ts = datetime.now(timezone.utc)
        snapshot_id = ts.strftime("%Y%m%dT%H%M%S")
        filename = f"snapshot_{snapshot_id}.json"
        dest = self.archive_dir / filename
        dest.write_text(json.dumps(snapshot.to_dict(), indent=2))
        entry = ArchiveEntry(
            snapshot_id=snapshot_id,
            label=label or snapshot_id,
            created_at=ts.isoformat(),
            path=str(dest),
        )
        self._index.append(entry)
        self._save_index()
        return entry

    def list_entries(self) -> List[ArchiveEntry]:
        return list(self._index)

    def load(self, snapshot_id: str) -> Optional[DatabaseSnapshot]:
        for entry in self._index:
            if entry.snapshot_id == snapshot_id:
                data = json.loads(Path(entry.path).read_text())
                return DatabaseSnapshot.from_dict(data)
        return None

    def latest(self) -> Optional[ArchiveEntry]:
        return self._index[-1] if self._index else None
