"""Merges two drift reports into a single consolidated report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from schema_drift.models import ChangeType
from schema_drift.reporter import DriftReport, SchemaChange


@dataclass
class MergeResult:
    """Result of merging two drift reports."""

    changes: List[SchemaChange] = field(default_factory=list)
    total: int = 0
    breaking: int = 0
    sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "sources": self.sources,
            "total": self.total,
            "breaking": self.breaking,
            "changes": [
                {
                    "table": c.table,
                    "column": c.column,
                    "change_type": c.change_type.value,
                    "breaking": c.breaking,
                    "detail": c.detail,
                }
                for c in self.changes
            ],
        }


def _dedup_changes(changes: List[SchemaChange]) -> List[SchemaChange]:
    """Remove duplicate changes based on (table, column, change_type)."""
    seen = set()
    result = []
    for c in changes:
        key = (c.table, c.column, c.change_type)
        if key not in seen:
            seen.add(key)
            result.append(c)
    return result


def merge_reports(
    *reports: DriftReport,
    source_labels: List[str] | None = None,
    deduplicate: bool = True,
) -> MergeResult:
    """Merge multiple DriftReports into a single MergeResult.

    Args:
        *reports: One or more DriftReport instances to merge.
        source_labels: Optional labels identifying each report source.
        deduplicate: If True, remove duplicate changes across reports.

    Returns:
        A MergeResult containing all consolidated changes.
    """
    labels = list(source_labels) if source_labels else [f"report_{i}" for i in range(len(reports))]

    all_changes: List[SchemaChange] = []
    for report in reports:
        all_changes.extend(report.changes)

    if deduplicate:
        all_changes = _dedup_changes(all_changes)

    breaking = sum(1 for c in all_changes if c.breaking)

    return MergeResult(
        changes=all_changes,
        total=len(all_changes),
        breaking=breaking,
        sources=labels,
    )
