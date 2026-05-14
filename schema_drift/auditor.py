"""Audit trail for schema drift events — records when drifts were detected and by whom."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from schema_drift.scorer import DriftScore


@dataclass
class AuditEntry:
    timestamp: str
    snapshot_label: str
    total_changes: int
    breaking_changes: int
    score: float
    risk_level: str
    triggered_by: str = "unknown"
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "snapshot_label": self.snapshot_label,
            "total_changes": self.total_changes,
            "breaking_changes": self.breaking_changes,
            "score": self.score,
            "risk_level": self.risk_level,
            "triggered_by": self.triggered_by,
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(data: dict) -> "AuditEntry":
        return AuditEntry(
            timestamp=data["timestamp"],
            snapshot_label=data["snapshot_label"],
            total_changes=data["total_changes"],
            breaking_changes=data["breaking_changes"],
            score=data["score"],
            risk_level=data["risk_level"],
            triggered_by=data.get("triggered_by", "unknown"),
            notes=data.get("notes"),
        )


@dataclass
class DriftAuditor:
    audit_dir: Path
    entries: List[AuditEntry] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.audit_dir = Path(self.audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self._log_path = self.audit_dir / "audit_log.jsonl"
        self._load_existing()

    def _load_existing(self) -> None:
        if not self._log_path.exists():
            return
        with open(self._log_path, "r") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    self.entries.append(AuditEntry.from_dict(json.loads(line)))

    def record(self, drift_score: DriftScore, snapshot_label: str,
               triggered_by: str = "cli", notes: Optional[str] = None) -> AuditEntry:
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            snapshot_label=snapshot_label,
            total_changes=drift_score.total_changes,
            breaking_changes=drift_score.breaking_changes,
            score=drift_score.score,
            risk_level=drift_score.risk_level,
            triggered_by=triggered_by,
            notes=notes,
        )
        self.entries.append(entry)
        with open(self._log_path, "a") as fh:
            fh.write(json.dumps(entry.to_dict()) + "\n")
        return entry

    def recent(self, n: int = 10) -> List[AuditEntry]:
        return self.entries[-n:]

    def clear(self) -> None:
        self.entries.clear()
        if self._log_path.exists():
            self._log_path.unlink()
