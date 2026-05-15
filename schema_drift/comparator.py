"""Snapshot comparator: compares two named snapshots and returns a labelled result."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from schema_drift.models import SchemaSnapshot
from schema_drift.detector import DriftDetector
from schema_drift.tagger import tag_report
from schema_drift.scorer import score_report
from schema_drift.models import DriftReport


@dataclass
class CompareResult:
    baseline_name: str
    current_name: str
    report: DriftReport
    tags: list[str] = field(default_factory=list)
    score: Optional[object] = None

    def to_dict(self) -> dict:
        return {
            "baseline_name": self.baseline_name,
            "current_name": self.current_name,
            "tags": self.tags,
            "score": self.score.to_dict() if self.score else None,
            "report": {
                "changes": [
                    {
                        "table": c.table,
                        "change_type": c.change_type.value,
                        "column": c.column,
                        "detail": c.detail,
                        "breaking": c.breaking,
                    }
                    for c in self.report.changes
                ]
            },
        }


class SnapshotComparator:
    """Orchestrates detection, tagging, and scoring for a pair of snapshots."""

    def __init__(self, tag: bool = True, score: bool = True) -> None:
        self._tag = tag
        self._score = score
        self._detector = DriftDetector()

    def compare(
        self,
        baseline: SchemaSnapshot,
        current: SchemaSnapshot,
        baseline_name: str = "baseline",
        current_name: str = "current",
    ) -> CompareResult:
        report = self._detector.detect(baseline, current)

        tags: list[str] = []
        if self._tag:
            tag_result = tag_report(report)
            tags = tag_result.tags

        drift_score = None
        if self._score:
            drift_score = score_report(report)

        return CompareResult(
            baseline_name=baseline_name,
            current_name=current_name,
            report=report,
            tags=tags,
            score=drift_score,
        )
